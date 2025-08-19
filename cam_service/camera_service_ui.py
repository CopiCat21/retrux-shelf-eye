import sys
import os
import time
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QGridLayout,
    QSpinBox, QListWidget, QProgressBar, QTabWidget
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from scanner import scan_camera
from background_service import BackgroundCameraService

class CameraServiceThread(QThread):
    status_updated = pyqtSignal(str)
    camera_found = pyqtSignal(list)
    service_started = pyqtSignal()
    service_stopped = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.services = []
        self.root_directory = None
        
    def set_root_directory(self, root_dir):
        self.root_directory = root_dir
        
    def scan_cameras(self, search_limit=10):
        self.status_updated.emit("Scanning for cameras...")
        valid_cameras = scan_camera(search_limit)
        self.camera_found.emit(valid_cameras)
        self.status_updated.emit(f"Found {len(valid_cameras)} valid cameras")
        
    def start_services(self, camera_ids):
        if not self.root_directory:
            self.status_updated.emit("Root directory not set")
            return
            
        # Clear and create root directory
        import shutil
        if os.path.exists(self.root_directory):
            shutil.rmtree(self.root_directory, ignore_errors=True)
        os.makedirs(self.root_directory, exist_ok=True)
        
        self.status_updated.emit(f"Starting services for {len(camera_ids)} cameras...")
        
        for camera_id in camera_ids:
            camera_str = str(camera_id).zfill(3)
            latest_frame_file = os.path.join(self.root_directory, f'camera_{camera_str}_frame.jpg')
            
            camera_service = BackgroundCameraService(camera_str, camera_id, latest_frame_file)
            self.services.append(camera_service)
            
        for i, camera_service in enumerate(self.services):
            self.status_updated.emit(f"Starting camera {camera_service.camera_id}...")
            camera_service.start()
            time.sleep(1.5)  # Stagger start times
            
        self.running = True
        self.service_started.emit()
        self.status_updated.emit("All camera services started")
        
    def stop_services(self):
        self.running = False
        self.status_updated.emit("Stopping all camera services...")
        
        for service in self.services:
            service.stop()
            
        for service in self.services:
            if service.thread.is_alive():
                service.thread.join(timeout=3)
                
        self.services.clear()
        self.service_stopped.emit()
        self.status_updated.emit("All camera services stopped")

class CameraServiceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrux Camera Service Control")
        self.setGeometry(100, 100, 1000, 700)
        
        self.service_thread = CameraServiceThread()
        self.service_thread.status_updated.connect(self.log_status)
        self.service_thread.camera_found.connect(self.update_camera_list)
        self.service_thread.service_started.connect(self.on_service_started)
        self.service_thread.service_stopped.connect(self.on_service_stopped)
        
        self.valid_cameras = []
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Camera Service Control Panel")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Camera Discovery Tab
        discovery_tab = QWidget()
        discovery_layout = QVBoxLayout(discovery_tab)
        
        # Discovery controls
        discovery_group = QGroupBox("Camera Discovery")
        discovery_controls = QGridLayout(discovery_group)
        
        discovery_controls.addWidget(QLabel("Search Limit:"), 0, 0)
        self.search_limit_spin = QSpinBox()
        self.search_limit_spin.setRange(1, 100)
        self.search_limit_spin.setValue(10)
        discovery_controls.addWidget(self.search_limit_spin, 0, 1)
        
        self.scan_btn = QPushButton("Scan for Cameras")
        self.scan_btn.clicked.connect(self.scan_cameras)
        discovery_controls.addWidget(self.scan_btn, 0, 2)
        
        discovery_layout.addWidget(discovery_group)
        
        # Camera list
        camera_list_group = QGroupBox("Detected Cameras")
        camera_list_layout = QVBoxLayout(camera_list_group)
        
        self.camera_list = QListWidget()
        camera_list_layout.addWidget(self.camera_list)
        
        discovery_layout.addWidget(camera_list_group)
        
        tab_widget.addTab(discovery_tab, "Camera Discovery")
        
        # Service Control Tab
        service_tab = QWidget()
        service_layout = QVBoxLayout(service_tab)
        
        # Service controls
        service_group = QGroupBox("Service Control")
        service_controls = QGridLayout(service_group)
        
        service_controls.addWidget(QLabel("Output Directory:"), 0, 0)
        self.output_dir_label = QLabel("../retruxosaproject/app_root/active_state/devices")
        service_controls.addWidget(self.output_dir_label, 0, 1)
        
        # Service buttons
        button_layout = QHBoxLayout()
        self.start_service_btn = QPushButton("Start Camera Services")
        self.start_service_btn.clicked.connect(self.start_services)
        self.start_service_btn.setEnabled(False)
        
        self.stop_service_btn = QPushButton("Stop Camera Services")
        self.stop_service_btn.clicked.connect(self.stop_services)
        self.stop_service_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_service_btn)
        button_layout.addWidget(self.stop_service_btn)
        service_controls.addLayout(button_layout, 1, 0, 1, 2)
        
        service_layout.addWidget(service_group)
        
        # Service status
        service_status_group = QGroupBox("Service Status")
        service_status_layout = QVBoxLayout(service_status_group)
        
        self.service_status_label = QLabel("Services: Stopped")
        self.service_status_label.setStyleSheet("font-weight: bold; color: red;")
        service_status_layout.addWidget(self.service_status_label)
        
        service_layout.addWidget(service_status_group)
        
        tab_widget.addTab(service_tab, "Service Control")
        
        layout.addWidget(tab_widget)
        
        # Status log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(200)
        self.status_log.setReadOnly(True)
        log_layout.addWidget(self.status_log)
        
        layout.addWidget(log_group)
        
        # Initial status
        self.log_status("Camera Service Control Panel initialized")
        
    def scan_cameras(self):
        self.scan_btn.setEnabled(False)
        self.camera_list.clear()
        
        search_limit = self.search_limit_spin.value()
        
        # Run camera scan in thread
        import threading
        scan_thread = threading.Thread(
            target=lambda: self.service_thread.scan_cameras(search_limit)
        )
        scan_thread.start()
        
    def update_camera_list(self, cameras):
        self.valid_cameras = cameras
        self.camera_list.clear()
        
        for camera_id in cameras:
            self.camera_list.addItem(f"Camera {camera_id}")
            
        self.scan_btn.setEnabled(True)
        self.start_service_btn.setEnabled(len(cameras) > 0)
        
    def start_services(self):
        if not self.valid_cameras:
            self.log_status("No cameras available to start")
            return
            
        root_dir = "../retruxosaproject/app_root/active_state/devices"
        root_dir = os.path.abspath(root_dir)
        
        self.service_thread.set_root_directory(root_dir)
        
        # Start services in thread
        import threading
        start_thread = threading.Thread(
            target=lambda: self.service_thread.start_services(self.valid_cameras)
        )
        start_thread.start()
        
        self.start_service_btn.setEnabled(False)
        
    def stop_services(self):
        # Stop services in thread
        import threading
        stop_thread = threading.Thread(
            target=self.service_thread.stop_services
        )
        stop_thread.start()
        
        self.stop_service_btn.setEnabled(False)
        
    def on_service_started(self):
        self.service_status_label.setText("Services: Running")
        self.service_status_label.setStyleSheet("font-weight: bold; color: green;")
        self.stop_service_btn.setEnabled(True)
        
    def on_service_stopped(self):
        self.service_status_label.setText("Services: Stopped")
        self.service_status_label.setStyleSheet("font-weight: bold; color: red;")
        self.start_service_btn.setEnabled(len(self.valid_cameras) > 0)
        
    def log_status(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_log.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        if self.service_thread.running:
            self.stop_services()
            self.service_thread.wait(3000)
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = CameraServiceWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())