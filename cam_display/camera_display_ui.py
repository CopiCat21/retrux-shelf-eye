import sys
import os
import time
import cv2 as cv
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QGroupBox, QGridLayout,
    QComboBox, QSpinBox, QCheckBox, QTabWidget
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QFont
from grid_display import create_grid_datetime

class CameraDisplayThread(QThread):
    image_updated = pyqtSignal(np.ndarray)
    status_updated = pyqtSignal(str)
    
    def __init__(self, root_directory, display_title="Display"):
        super().__init__()
        self.root_directory = root_directory
        self.display_title = display_title
        self.running = False
        self.image_file_list = []
        self.last_modified_time = []
        self.images_frames = []
        
    def find_jpg_images(self, directory):
        jpg_images = []
        if not os.path.exists(directory):
            return jpg_images
            
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    jpg_images.append(os.path.join(root, file))
        return sorted(jpg_images, key=lambda x: os.path.basename(x).lower())
    
    def run(self):
        self.running = True
        
        while self.running:
            # Refresh file list each cycle to catch new files
            current_image_list = self.find_jpg_images(self.root_directory)
            
            # Update lists if new files found
            if len(current_image_list) != len(self.image_file_list):
                self.image_file_list = current_image_list
                self.last_modified_time = [0] * len(self.image_file_list)
                self.images_frames = [np.zeros(shape=(512, 512, 3), dtype=np.uint8)] * len(self.image_file_list)
                self.status_updated.emit(f"[{self.display_title}] Found {len(self.image_file_list)} image files")
            
            updated_count = 0
            
            for i, file_path in enumerate(self.image_file_list):
                if not os.path.exists(file_path):
                    continue
                    
                try:
                    current_modified = os.path.getmtime(file_path)
                    
                    if current_modified != self.last_modified_time[i]:
                        self.last_modified_time[i] = current_modified
                        
                        image_array = cv.imread(file_path)
                        if image_array is not None:
                            self.images_frames[i] = image_array
                            updated_count += 1
                            
                except Exception as e:
                    self.status_updated.emit(f"[{self.display_title}] Error reading {file_path}: {e}")
            
            # Create grid and emit
            if self.images_frames and any(img.sum() > 0 for img in self.images_frames):
                try:
                    # Filter out empty frames
                    valid_frames = [img for img in self.images_frames if img.sum() > 0]
                    if valid_frames:
                        image_grid = create_grid_datetime(valid_frames)
                        self.image_updated.emit(image_grid)
                        
                        if updated_count > 0:
                            current_time = time.strftime("%H:%M:%S")
                            self.status_updated.emit(f"[{self.display_title}] Updated {updated_count} images at {current_time}")
                            
                except Exception as e:
                    self.status_updated.emit(f"[{self.display_title}] Error creating grid: {e}")
            
            self.msleep(1000)  # Update every 1 second
    
    def stop(self):
        self.running = False

class EnhancedCameraDisplayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrux Enhanced Display System")
        self.setGeometry(100, 100, 1400, 1000)
        
        # Threads for different displays
        self.camera_thread = None
        self.product_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("🎯 Retrux Enhanced Display System")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4CAF50; margin: 10px; text-align: center;")
        layout.addWidget(title)
        
        # Tab widget for different displays
        self.tab_widget = QTabWidget()
        
        # Raw Camera Tab
        camera_tab = self.create_camera_tab()
        self.tab_widget.addTab(camera_tab, "📹 Raw Camera Feed")
        
        # Product Visual Tab
        product_tab = self.create_product_tab()
        self.tab_widget.addTab(product_tab, "🔍 AI Detection Results")
        
        # Dual Display Tab
        dual_tab = self.create_dual_tab()
        self.tab_widget.addTab(dual_tab, "📊 Side-by-Side Compare")
        
        layout.addWidget(self.tab_widget)
        
        # Global status area
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("background-color: #1e1e1e; color: white; font-family: monospace;")
        status_layout.addWidget(self.status_text)
        layout.addWidget(status_group)
        
        self.log_status("Enhanced Display System initialized")
        
    def create_camera_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls
        controls_group = QGroupBox("Raw Camera Controls")
        controls_layout = QGridLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Input Directory:"), 0, 0)
        self.camera_dir_input = QLineEdit("retruxosaproject/app_root/active_state/devices")
        controls_layout.addWidget(self.camera_dir_input, 0, 1)
        
        button_layout = QHBoxLayout()
        self.camera_start_btn = QPushButton("▶️ Start Raw Display")
        self.camera_start_btn.clicked.connect(self.start_camera_display)
        self.camera_stop_btn = QPushButton("⏹️ Stop Display")
        self.camera_stop_btn.clicked.connect(self.stop_camera_display)
        self.camera_stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.camera_start_btn)
        button_layout.addWidget(self.camera_stop_btn)
        controls_layout.addLayout(button_layout, 1, 0, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Image display
        self.camera_image_label = QLabel("📹 Raw camera feed will appear here")
        self.camera_image_label.setMinimumSize(800, 600)
        self.camera_image_label.setStyleSheet(
            "border: 2px solid #4CAF50; background-color: #1e1e1e; color: #4CAF50; "
            "font-size: 14pt; text-align: center;"
        )
        self.camera_image_label.setScaledContents(True)
        layout.addWidget(self.camera_image_label)
        
        return tab
        
    def create_product_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls
        controls_group = QGroupBox("AI Detection Controls")
        controls_layout = QGridLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Product Visual Directory:"), 0, 0)
        self.product_dir_input = QLineEdit("retruxosaproject/app_root/active_state/product_visual")
        controls_layout.addWidget(self.product_dir_input, 0, 1)
        
        button_layout = QHBoxLayout()
        self.product_start_btn = QPushButton("▶️ Start AI Display")
        self.product_start_btn.clicked.connect(self.start_product_display)
        self.product_stop_btn = QPushButton("⏹️ Stop Display")
        self.product_stop_btn.clicked.connect(self.stop_product_display)
        self.product_stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.product_start_btn)
        button_layout.addWidget(self.product_stop_btn)
        controls_layout.addLayout(button_layout, 1, 0, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Image display
        self.product_image_label = QLabel("🔍 AI detection results will appear here")
        self.product_image_label.setMinimumSize(800, 600)
        self.product_image_label.setStyleSheet(
            "border: 2px solid #2196F3; background-color: #1e1e1e; color: #2196F3; "
            "font-size: 14pt; text-align: center;"
        )
        self.product_image_label.setScaledContents(True)
        layout.addWidget(self.product_image_label)
        
        return tab
        
    def create_dual_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls
        controls_group = QGroupBox("Dual Display Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.dual_start_btn = QPushButton("▶️ Start Both Displays")
        self.dual_start_btn.clicked.connect(self.start_dual_display)
        self.dual_stop_btn = QPushButton("⏹️ Stop All Displays")
        self.dual_stop_btn.clicked.connect(self.stop_all_displays)
        
        controls_layout.addWidget(self.dual_start_btn)
        controls_layout.addWidget(self.dual_stop_btn)
        layout.addWidget(controls_group)
        
        # Side by side display
        dual_layout = QHBoxLayout()
        
        # Left side - Raw camera
        raw_group = QGroupBox("📹 Raw Camera Feed")
        raw_layout = QVBoxLayout(raw_group)
        
        self.dual_camera_label = QLabel("Raw feed")
        self.dual_camera_label.setMinimumSize(400, 300)
        self.dual_camera_label.setStyleSheet(
            "border: 1px solid #4CAF50; background-color: #1e1e1e; color: #4CAF50;"
        )
        self.dual_camera_label.setScaledContents(True)
        raw_layout.addWidget(self.dual_camera_label)
        
        dual_layout.addWidget(raw_group)
        
        # Right side - AI detection
        ai_group = QGroupBox("🔍 AI Detection Results")
        ai_layout = QVBoxLayout(ai_group)
        
        self.dual_product_label = QLabel("AI results")
        self.dual_product_label.setMinimumSize(400, 300)
        self.dual_product_label.setStyleSheet(
            "border: 1px solid #2196F3; background-color: #1e1e1e; color: #2196F3;"
        )
        self.dual_product_label.setScaledContents(True)
        ai_layout.addWidget(self.dual_product_label)
        
        dual_layout.addWidget(ai_group)
        layout.addLayout(dual_layout)
        
        return tab
        
    def start_camera_display(self):
        camera_dir = self.camera_dir_input.text().strip()
        if not camera_dir:
            self.log_status("❌ Please enter camera directory")
            return
            
        # Make path absolute
        if not os.path.isabs(camera_dir):
            camera_dir = os.path.abspath(camera_dir)
            
        if not os.path.exists(camera_dir):
            self.log_status(f"❌ Directory does not exist: {camera_dir}")
            return
            
        self.camera_thread = CameraDisplayThread(camera_dir, "RAW")
        self.camera_thread.image_updated.connect(
            lambda img: self.update_image(img, self.camera_image_label)
        )
        self.camera_thread.status_updated.connect(self.log_status)
        self.camera_thread.start()
        
        self.camera_start_btn.setEnabled(False)
        self.camera_stop_btn.setEnabled(True)
        self.log_status(f"📹 Started camera display: {camera_dir}")
        
    def stop_camera_display(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread.wait()
            self.camera_thread = None
            
        self.camera_start_btn.setEnabled(True)
        self.camera_stop_btn.setEnabled(False)
        self.log_status("📹 Camera display stopped")
        
    def start_product_display(self):
        product_dir = self.product_dir_input.text().strip()
        if not product_dir:
            self.log_status("❌ Please enter product visual directory")
            return
            
        # Make path absolute
        if not os.path.isabs(product_dir):
            product_dir = os.path.abspath(product_dir)
            
        if not os.path.exists(product_dir):
            self.log_status(f"⚠️ Directory does not exist yet: {product_dir}")
            self.log_status("ℹ️ Directory will be created when scanner service runs")
            # Continue anyway, directory might be created later
            
        self.product_thread = CameraDisplayThread(product_dir, "AI")
        self.product_thread.image_updated.connect(
            lambda img: self.update_image(img, self.product_image_label)
        )
        self.product_thread.status_updated.connect(self.log_status)
        self.product_thread.start()
        
        self.product_start_btn.setEnabled(False)
        self.product_stop_btn.setEnabled(True)
        self.log_status(f"🔍 Started product display: {product_dir}")
        
    def stop_product_display(self):
        if self.product_thread:
            self.product_thread.stop()
            self.product_thread.wait()
            self.product_thread = None
            
        self.product_start_btn.setEnabled(True)
        self.product_stop_btn.setEnabled(False)
        self.log_status("🔍 Product display stopped")
        
    def start_dual_display(self):
        self.start_camera_display()
        QTimer.singleShot(1000, self.start_product_display)  # Slight delay
        
        # Connect dual display updates
        if self.camera_thread:
            self.camera_thread.image_updated.connect(
                lambda img: self.update_image(img, self.dual_camera_label)
            )
        if self.product_thread:
            QTimer.singleShot(1000, lambda: (
                self.product_thread.image_updated.connect(
                    lambda img: self.update_image(img, self.dual_product_label)
                ) if self.product_thread else None
            ))
        
        self.log_status("📊 Dual display started")
        
    def stop_all_displays(self):
        self.stop_camera_display()
        self.stop_product_display()
        self.log_status("🛑 All displays stopped")
        
    def update_image(self, image_array, target_label):
        try:
            # Convert BGR to RGB
            rgb_image = cv.cvtColor(image_array, cv.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            # Create QImage
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Scale to fit label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                target_label.size(),
                aspectRatioMode=1,  # KeepAspectRatio
                transformMode=1     # SmoothTransformation
            )
            
            target_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.log_status(f"❌ Error updating image: {e}")
    
    def log_status(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        # Auto scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        self.stop_all_displays()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Retrux Enhanced Display")
    
    window = EnhancedCameraDisplayWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())