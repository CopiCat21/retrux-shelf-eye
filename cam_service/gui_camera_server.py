import os
import sys
import shutil
import threading
import time
import random
import traceback
import subprocess
import signal
from typing import List, Dict, Optional

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QFileDialog, QMessageBox, QComboBox
)

# ---- your existing modules (used in Camera mode) ----
from scanner            import scan_camera
from background_service import BackgroundCameraService


# --------- Paths ---------
def project_root_dir() -> str:
    """One level above cam_service/."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def default_root_devices_dir() -> str:
    """
    Match shelf_scan.py's absolute_root_directory:
      E:/Projects/retrux-shelf-components-main/retruxosaproject/app_root/active_state/devices
    Fallback to <home>/retruxosaproject/app_root/active_state/devices.
    """
    preferred = os.path.join(
        "E:/Projects/retrux-shelf-components-main",
        "retruxosaproject",
        "app_root",
        "active_state",
        "devices"
    )
    parent = os.path.dirname(preferred)
    if os.path.isdir(parent) or os.path.isdir(preferred):
        return os.path.normpath(preferred)

    home = os.path.expanduser("~")
    return os.path.join(home, "retruxosaproject", "app_root", "active_state", "devices")


def find_jpg_images(devices_dir: str) -> List[str]:
    """Return absolute paths of *.jpg in devices_dir (non-recursive)."""
    if not os.path.isdir(devices_dir):
        return []
    out = []
    for name in sorted(os.listdir(devices_dir)):
        if name.lower().endswith(".jpg"):
            out.append(os.path.join(devices_dir, name))
    return out


# --------- Workers ---------
class CameraServerWorker(QThread):
    """Real camera mode (writes into devices folder, clears it first)."""
    log = pyqtSignal(str)
    finished = pyqtSignal()
    running_changed = pyqtSignal(bool)

    def __init__(self, root_devices_dir: str, camera_indices: List[int]):
        super().__init__()
        # Normalize to .../active_state/devices even if user gives parent
        root_devices_dir = os.path.normpath(root_devices_dir)
        if os.path.basename(root_devices_dir).lower() != "devices":
            root_devices_dir = os.path.join(root_devices_dir, "devices")

        self.root_devices_dir = root_devices_dir
        self._stop_event = threading.Event()
        self.running_services: List[BackgroundCameraService] = []
        self.camera_indices = camera_indices  # explicit list

    def _log(self, msg: str):
        self.log.emit(msg)

    def request_stop(self):
        self._stop_event.set()

    def run(self):
        try:
            self._log("Background Camera Server System")
            self.running_changed.emit(True)

            # Clear + recreate directory (same behavior as your script)
            self._log(f"Preparing directory: {self.root_devices_dir}")
            shutil.rmtree(self.root_devices_dir, ignore_errors=True)
            os.makedirs(self.root_devices_dir, exist_ok=True)

            # Output similar to the CLI script
            self._log("Searching For Valid Cameras...")

            if not self.camera_indices:
                self._log("No cameras selected.")
                return

            self._log(f"Found {len(self.camera_indices)} Cameras")
            self._log("Starting Background Services...")

            # Build + start services
            self.running_services.clear()
            for camera_id in self.camera_indices:
                camera_str = str(camera_id).zfill(3)
                latest_frame_file = os.path.join(
                    self.root_devices_dir, f"camera_{camera_str}_frame.jpg"
                )
                svc = BackgroundCameraService(camera_str, camera_id, latest_frame_file)
                self.running_services.append(svc)

            for svc in self.running_services:
                self._log(f"Starting {svc.camera_id} ...")
                svc.start()
                time.sleep(1.0 + random.uniform(-0.5, 0.5))

            self._log("All Service Is Running")

            # Keep thread alive until stop requested
            while not self._stop_event.is_set():
                time.sleep(1)

            # Stop flow
            self._log("Stopping all services...")
            for svc in self.running_services:
                try:
                    svc.stop()
                except Exception as e:
                    self._log(f"Error during stop() on {svc.camera_id}: {e}")

            for svc in self.running_services:
                try:
                    if hasattr(svc, "thread") and svc.thread is not None:
                        svc.thread.join(timeout=5)
                except Exception as e:
                    self._log(f"Error during join() on {svc.camera_id}: {e}")

            self._log("All Services are Finished.")

        except Exception as e:
            self._log("FATAL ERROR:\n" + "".join(traceback.format_exception(e)))
            QMessageBox.critical(None, "Camera Server Error", str(e))
        finally:
            self.running_changed.emit(False)
            self.finished.emit()


class ImageSourceWorker(QThread):
    """
    'Existing images' mode. Does NOT modify devices folder. Keeps a heartbeat
    so you can run Shelf Setup / Service concurrently.
    """
    log = pyqtSignal(str)
    finished = pyqtSignal()
    running_changed = pyqtSignal(bool)

    def __init__(self, devices_dir: str, selected_images: List[str]):
        super().__init__()
        self.devices_dir = devices_dir
        self.selected_images = selected_images
        self._stop_event = threading.Event()

    def _log(self, msg: str):
        self.log.emit(msg)

    def request_stop(self):
        self._stop_event.set()

    def run(self):
        try:
            self.running_changed.emit(True)
            self._log("Image Source Mode (no camera capture)")
            self._log(f"Devices folder: {self.devices_dir}")
            if not self.selected_images:
                self._log("No images selected.")
            else:
                self._log(f"Using {len(self.selected_images)} image(s):")
                for p in self.selected_images:
                    self._log(f" - {os.path.basename(p)}")

            # Keep alive without touching files
            while not self._stop_event.is_set():
                time.sleep(1)

            self._log("Image source stopped.")
        except Exception as e:
            self._log("FATAL ERROR:\n" + "".join(traceback.format_exception(e)))
        finally:
            self.running_changed.emit(False)
            self.finished.emit()


class ShelfScanWorker(QThread):
    """
    Runs: <venv_python> -u <project_root>/product_scan/shelf_scan.py [setup|service]
    Streams stdout->GUI live. 'setup' ends by itself; 'service' runs until stop() is called.
    """
    log = pyqtSignal(str)
    finished = pyqtSignal()
    mode_changed = pyqtSignal(str)

    def __init__(self, project_root: str, mode: str, python_exe: Optional[str] = None):
        super().__init__()
        assert mode in ("setup", "service")
        self.project_root = project_root
        self.mode = mode
        self.python_exe = python_exe or sys.executable  # ensure we use the venv that launched the GUI
        self._stop = False
        self._process: Optional[subprocess.Popen] = None
        self.shelf_scan_path = os.path.join(project_root, "product_scan", "shelf_scan.py")

    def run(self):
        try:
            if not os.path.isfile(self.shelf_scan_path):
                self.log.emit(f"Not found: {self.shelf_scan_path}")
                return

            # Force unbuffered output from the child process
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            cmd = [self.python_exe, "-u", self.shelf_scan_path, self.mode]
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            self.log.emit(f"Executing with interpreter: {self.python_exe}")
            self.log.emit(f"Command: {' '.join(cmd)}")
            self.mode_changed.emit(self.mode)

            self._process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,                 # line-buffered on our side
                creationflags=creationflags,
                env=env
            )
            assert self._process.stdout is not None

            # Immediate activity line
            self.log.emit(f"shelf_scan.py ({self.mode}) started (pid={self._process.pid})")

            # Read lines as they arrive
            for line in iter(self._process.stdout.readline, ''):
                if self._stop and self.mode == "service":
                    break
                if not line:
                    break
                self.log.emit(line.rstrip())

            rc = self._process.wait()
            self.log.emit(f"shelf_scan.py ({self.mode}) exited with code {rc}")
        except Exception as e:
            self.log.emit(f"Error running shelf_scan.py ({self.mode}): {e}")
        finally:
            self.finished.emit()

    def stop(self):
        self._stop = True
        if self._process and self._process.poll() is None:
            try:
                if os.name == "nt":
                    self._process.send_signal(signal.CTRL_BREAK_EVENT)
                    try:
                        self._process.wait(timeout=3)
                    except Exception:
                        self._process.terminate()
                else:
                    self._process.terminate()
                try:
                    self._process.wait(timeout=3)
                except Exception:
                    self._process.kill()
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass


class CamDisplayWorker(QThread):
    """
    Runs: <venv_python> -u <project_root>/cam_display/display_camera.py --root-dir <active_state>/product_visual --title <title>
    Streams stdout->GUI live. Stops when window is closed or 'q' in that window; you can also stop from GUI.
    """
    log = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, project_root: str, root_dir: str, title: str, python_exe: Optional[str] = None):
        super().__init__()
        self.project_root = project_root
        self.root_dir = root_dir
        self.title = title
        self.python_exe = python_exe or sys.executable
        self._process: Optional[subprocess.Popen] = None

    def run(self):
        try:
            display_path = os.path.join(self.project_root, "cam_display", "display_camera.py")
            if not os.path.isfile(display_path):
                self.log.emit(f"Not found: {display_path}")
                return

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            cmd = [
                self.python_exe, "-u", display_path,
                "--root-dir", self.root_dir,
                "--title", self.title
            ]
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            self.log.emit(f"Executing cam display: {' '.join(cmd)}")
            self._process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags,
                env=env
            )
            assert self._process.stdout is not None

            self.log.emit(f"cam_display started (pid={self._process.pid})")
            for line in iter(self._process.stdout.readline, ''):
                if not line:
                    break
                self.log.emit(line.rstrip())

            rc = self._process.wait()
            self.log.emit(f"cam_display exited with code {rc}")
        except Exception as e:
            self.log.emit(f"Error running cam_display: {e}")
        finally:
            self.finished.emit()

    def stop(self):
        if self._process and self._process.poll() is None:
            try:
                if os.name == "nt":
                    self._process.send_signal(signal.CTRL_BREAK_EVENT)
                    try:
                        self._process.wait(timeout=2)
                    except Exception:
                        self._process.terminate()
                else:
                    self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except Exception:
                    self._process.kill()
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass


# --------- GUI ---------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera & Shelf Controller")

        # === Path row ===
        self.path_edit = QLineEdit(default_root_devices_dir())
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.browse_for_path)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Root (…/active_state[/devices]):"))
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)

        # === Source row ===
        self.source_combo = QComboBox()
        self.source_combo.addItem("Use Existing Images", userData="images")
        self.source_combo.addItem("Use Cameras", userData="cameras")
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)

        # item selector row (images or cameras depending on source)
        self.item_combo = QComboBox()
        self.rescan_btn = QPushButton("Rescan")
        self.rescan_btn.clicked.connect(self.rescan_items)

        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Input Source:"))
        source_row.addWidget(self.source_combo)
        source_row.addSpacing(12)
        source_row.addWidget(QLabel("Select:"))
        source_row.addWidget(self.item_combo)
        source_row.addWidget(self.rescan_btn)

        # === Buttons row (start/stop source) ===
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)

        run_row = QHBoxLayout()
        run_row.addWidget(self.start_btn)
        run_row.addWidget(self.stop_btn)

        # === Buttons row (shelf_scan) ===
        self.shelf_setup_btn = QPushButton("Run Shelf Setup (one-off)")
        self.shelf_service_start_btn = QPushButton("Start Shelf Service")
        self.shelf_service_stop_btn = QPushButton("Stop Shelf Service")
        self.shelf_service_stop_btn.setEnabled(False)

        shelf_row = QHBoxLayout()
        shelf_row.addWidget(self.shelf_setup_btn)
        shelf_row.addWidget(self.shelf_service_start_btn)
        shelf_row.addWidget(self.shelf_service_stop_btn)

        # === Display row (OpenCV grid viewer) ===
        self.display_title_edit = QLineEdit("Product Detection")
        self.display_start_btn = QPushButton("Open Cam Display")
        self.display_stop_btn = QPushButton("Close Cam Display")
        self.display_stop_btn.setEnabled(False)

        display_row = QHBoxLayout()
        display_row.addWidget(QLabel("Display Title:"))
        display_row.addWidget(self.display_title_edit)
        display_row.addWidget(self.display_start_btn)
        display_row.addWidget(self.display_stop_btn)

        # === Log view ===
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        # === Layout ===
        layout = QVBoxLayout()
        layout.addLayout(path_row)
        layout.addLayout(source_row)
        layout.addLayout(run_row)
        layout.addLayout(shelf_row)
        layout.addLayout(display_row)
        layout.addWidget(self.log_view)
        self.setLayout(layout)

        # Signals
        self.start_btn.clicked.connect(self.start_source)
        self.stop_btn.clicked.connect(self.stop_source)
        self.shelf_setup_btn.clicked.connect(self.run_shelf_setup)
        self.shelf_service_start_btn.clicked.connect(self.start_shelf_service)
        self.shelf_service_stop_btn.clicked.connect(self.stop_shelf_service)
        self.display_start_btn.clicked.connect(self.start_cam_display)
        self.display_stop_btn.clicked.connect(self.stop_cam_display)

        # Worker holders
        self.active_worker: Optional[QThread] = None  # CameraServerWorker or ImageSourceWorker
        self.shelf_worker: Optional[ShelfScanWorker] = None
        self.display_worker: Optional[CamDisplayWorker] = None

        # State caches
        self.detected_cameras: List[int] = []
        self.detected_images: List[str] = []  # absolute paths
        self.image_name_to_path: Dict[str, str] = {}

        # Initial fill
        self.on_source_changed()
        self.rescan_items(initial=True)

    # ----- UI helpers -----
    def browse_for_path(self):
        base = os.path.dirname(self.path_edit.text()) or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select active_state or devices folder", base)
        if path:
            self.path_edit.setText(path)
            # refresh items for current source after path change
            self.rescan_items()

    def on_source_changed(self):
        # Rebuild item combo label & content
        self.rescan_items()

    def rescan_items(self, initial: bool = False):
        source = self.source_combo.currentData()
        devices_dir = self.get_devices_dir_normalized()

        if source == "images":
            # List images from devices folder
            self.detected_images = find_jpg_images(devices_dir)
            self.image_name_to_path = {os.path.basename(p): p for p in self.detected_images}
            current = self.item_combo.currentData()
            self.item_combo.clear()
            self.item_combo.addItem("All images", userData="ALL_IMG")
            for name in sorted(self.image_name_to_path.keys()):
                self.item_combo.addItem(name, userData=name)

            if current is not None:
                index_to_set = 0  # default All
                if current != "ALL_IMG":
                    for i in range(1, self.item_combo.count()):
                        if self.item_combo.itemData(i) == current:
                            index_to_set = i
                            break
                self.item_combo.setCurrentIndex(index_to_set)

            if not self.detected_images:
                self.append_log(f"[Images] No .jpg files found in: {devices_dir}")
            else:
                self.append_log(f"[Images] Found {len(self.detected_images)} image(s) in: {devices_dir}")

        else:  # cameras
            cams = scan_camera(100)
            self.detected_cameras = cams
            current = self.item_combo.currentData()
            self.item_combo.clear()
            self.item_combo.addItem("All detected cameras", userData="ALL_CAM")
            for idx in cams:
                self.item_combo.addItem(f"Camera {idx}", userData=idx)

            if current is not None:
                index_to_set = 0
                if current != "ALL_CAM":
                    for i in range(1, self.item_combo.count()):
                        if self.item_combo.itemData(i) == current:
                            index_to_set = i
                            break
                self.item_combo.setCurrentIndex(index_to_set)

            if not cams:
                self.append_log("[Cameras] No valid cameras found.")
            else:
                self.append_log(f"[Cameras] Found cameras: {cams}")

        if initial and source == "cameras" and not self.detected_cameras:
            QMessageBox.information(self, "Scan", "No cameras detected on first scan.")
        if initial and source == "images" and not self.detected_images:
            QMessageBox.information(self, "Scan", f"No .jpg images in:\n{devices_dir}")

    def get_devices_dir_normalized(self) -> str:
        root_path = self.path_edit.text().strip()
        root_path = os.path.normpath(root_path)
        # accept either .../active_state or .../active_state/devices and normalize to /devices
        if os.path.basename(root_path).lower() != "devices":
            root_path = os.path.join(root_path, "devices")
        return root_path

    def get_active_state_dir(self) -> str:
        """Return .../active_state given devices dir normalization."""
        devices_dir = self.get_devices_dir_normalized()
        return os.path.dirname(devices_dir)

    # ----- Start/Stop for source -----
    def start_source(self):
        if self.active_worker and self.active_worker.isRunning():
            QMessageBox.information(self, "Running", "Source is already running.")
            return

        devices_dir = self.get_devices_dir_normalized()
        source = self.source_combo.currentData()

        if source == "images":
            # Use existing images; DO NOT modify devices folder
            sel = self.item_combo.currentData()
            if sel == "ALL_IMG":
                selected_list = list(self.detected_images)
                if not selected_list:
                    QMessageBox.warning(self, "No Images", "No images found. Try 'Rescan'.")
                    return
            else:
                # User selected a specific filename
                path = self.image_name_to_path.get(str(sel))
                if not path:
                    QMessageBox.warning(self, "Selection", "Selected image not found.")
                    return
                selected_list = [path]

            worker = ImageSourceWorker(devices_dir, selected_list)
            self.wire_source_worker(worker, label="Image Source")
            self.append_log(f"=== Starting Image Source (images={len(selected_list)}) ===")
            worker.start()

        else:
            # Cameras mode (will clear & write into devices dir)
            sel = self.item_combo.currentData()
            if sel == "ALL_CAM":
                camera_list = list(self.detected_cameras)
                if not camera_list:
                    QMessageBox.warning(self, "No Cameras", "No cameras detected. Try 'Rescan'.")
                    return
            else:
                camera_list = [int(sel)]

            worker = CameraServerWorker(devices_dir, camera_list)
            self.wire_source_worker(worker, label="Camera Server")
            self.append_log(f"=== Starting Camera Server (cameras={camera_list}) ===")
            worker.start()

    def wire_source_worker(self, worker: QThread, label: str):
        self.active_worker = worker  # CameraServerWorker or ImageSourceWorker
        if hasattr(worker, "log"):
            worker.log.connect(self.append_log)
        worker.finished.connect(lambda: self.on_source_finished(label))
        if hasattr(worker, "running_changed"):
            worker.running_changed.connect(self.on_source_running_changed)
        self.toggle_source_buttons(running=True)

    def stop_source(self):
        if self.active_worker and self.active_worker.isRunning():
            self.append_log("=== Stop requested (source) ===")
            if hasattr(self.active_worker, "request_stop"):
                self.active_worker.request_stop()
        else:
            self.append_log("Source is not running.")

    # ----- Shelf actions -----
    def run_shelf_setup(self):
        if self.shelf_worker and self.shelf_worker.isRunning():
            QMessageBox.information(self, "Shelf", "Another shelf_scan is running.")
            return

        proj_root = project_root_dir()
        self.append_log("=== Starting shelf_scan.py setup ===")
        self.shelf_worker = ShelfScanWorker(proj_root, mode="setup", python_exe=sys.executable)
        self.shelf_worker.log.connect(self.append_log)
        self.shelf_worker.finished.connect(lambda: self.append_log("=== Shelf setup finished ==="))
        self.shelf_worker.start()

    def start_shelf_service(self):
        if self.shelf_worker and self.shelf_worker.isRunning():
            QMessageBox.information(self, "Shelf Service", "Shelf service already running.")
            return

        proj_root = project_root_dir()
        self.append_log("=== Starting shelf_scan.py service ===")
        self.shelf_worker = ShelfScanWorker(proj_root, mode="service", python_exe=sys.executable)
        self.shelf_worker.log.connect(self.append_log)
        self.shelf_worker.finished.connect(self.on_shelf_service_finished)
        self.toggle_shelf_service_buttons(running=True)
        self.shelf_worker.start()

    def stop_shelf_service(self):
        if self.shelf_worker and self.shelf_worker.isRunning():
            self.append_log("=== Stop requested (shelf service) ===")
            self.shelf_worker.stop()
        else:
            self.append_log("Shelf service is not running.")

    # ----- Cam display actions -----
    def start_cam_display(self):
        if self.display_worker and self.display_worker.isRunning():
            QMessageBox.information(self, "Cam Display", "Cam display already running.")
            return

        proj_root = project_root_dir()
        active_state = self.get_active_state_dir()
        product_visual = os.path.join(active_state, "product_visual")
        os.makedirs(product_visual, exist_ok=True)

        title = self.display_title_edit.text().strip() or "Product Detection"
        self.append_log(f"=== Opening Cam Display (root={product_visual}, title={title}) ===")

        self.display_worker = CamDisplayWorker(
            project_root=proj_root,
            root_dir=product_visual,
            title=title,
            python_exe=sys.executable
        )
        self.display_worker.log.connect(self.append_log)
        self.display_worker.finished.connect(self.on_display_finished)
        self.toggle_display_buttons(running=True)
        self.display_worker.start()

    def stop_cam_display(self):
        if self.display_worker and self.display_worker.isRunning():
            self.append_log("=== Close requested (cam display) ===")
            self.display_worker.stop()
        else:
            self.append_log("Cam display is not running.")

    # ----- Callbacks -----
    def on_source_finished(self, label: str):
        self.append_log(f"=== {label} finished ===")
        self.toggle_source_buttons(running=False)

    def on_source_running_changed(self, running: bool):
        pass

    def on_shelf_service_finished(self):
        self.append_log("=== Shelf service finished ===")
        self.toggle_shelf_service_buttons(running=False)

    def on_display_finished(self):
        self.append_log("=== Cam display finished ===")
        self.toggle_display_buttons(running=False)

    # ----- UI state toggles -----
    def toggle_source_buttons(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def toggle_shelf_service_buttons(self, running: bool):
        self.shelf_service_start_btn.setEnabled(not running)
        self.shelf_service_stop_btn.setEnabled(running)

    def toggle_display_buttons(self, running: bool):
        self.display_start_btn.setEnabled(not running)
        self.display_stop_btn.setEnabled(running)

    # ----- Misc -----
    def append_log(self, text: str):
        self.log_view.append(text)

    def closeEvent(self, event):
        # Graceful shutdown on window close
        if self.active_worker and self.active_worker.isRunning():
            if hasattr(self.active_worker, "request_stop"):
                self.active_worker.request_stop()
            for _ in range(20):
                if not self.active_worker.isRunning():
                    break
                QApplication.processEvents()
                time.sleep(0.05)

        if self.shelf_worker and self.shelf_worker.isRunning():
            self.shelf_worker.stop()
            for _ in range(60):
                if not self.shelf_worker.isRunning():
                    break
                QApplication.processEvents()
                time.sleep(0.05)

        if self.display_worker and self.display_worker.isRunning():
            self.display_worker.stop()
            for _ in range(20):
                if not self.display_worker.isRunning():
                    break
                QApplication.processEvents()
                time.sleep(0.05)

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1080, 740)
    w.show()
    sys.exit(app.exec_())
