#!/usr/bin/env python3
"""
Retrux Shelf-Eye System Launcher - Safe Version
"""

import sys
import os
import subprocess
import signal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import QTimer, QProcess
from PyQt6.QtGui import QFont

class RetruxLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrux Shelf-Eye Control Panel")
        self.setGeometry(100, 100, 800, 600)
        
        # Use QProcess instead of subprocess for better Qt integration
        self.processes = {}
        
        self.init_ui()
        QTimer.singleShot(500, self.check_system_status)
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Simple dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #2d2d2d; }
            QWidget { background-color: #2d2d2d; color: white; }
            QPushButton { 
                background-color: #4a4a4a; 
                border: 1px solid #666; 
                padding: 8px; 
                border-radius: 4px;
                min-height: 25px;
            }
            QPushButton:hover { background-color: #5a5a5a; }
            QPushButton:pressed { background-color: #6a6a6a; }
            QGroupBox { 
                border: 1px solid #666; 
                border-radius: 5px; 
                margin-top: 10px; 
                font-weight: bold;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                padding: 0 5px; 
            }
            QTextEdit { 
                background-color: #1e1e1e; 
                border: 1px solid #666; 
                font-family: monospace; 
                font-size: 9pt;
            }
        """)
        
        # Title
        title = QLabel("🎯 Retrux Shelf-Eye System")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #4CAF50; margin: 10px;")
        layout.addWidget(title)
        
        # Main controls
        controls_layout = QHBoxLayout()
        
        # Left side - Camera & Display
        left_group = QGroupBox("Camera System")
        left_layout = QVBoxLayout(left_group)
        
        self.camera_service_btn = QPushButton("🎥 Start Camera Service")
        self.camera_service_btn.clicked.connect(self.toggle_camera_service)
        left_layout.addWidget(self.camera_service_btn)
        
        self.camera_display_btn = QPushButton("📺 Start Raw Display")
        self.camera_display_btn.clicked.connect(self.toggle_camera_display)
        left_layout.addWidget(self.camera_display_btn)

        self.product_display_btn = QPushButton("📺 Start Predicted Display")
        self.product_display_btn.clicked.connect(self.toggle_product_display)
        left_layout.addWidget(self.product_display_btn)

        
        self.people_counter_btn = QPushButton("👥 People Counter")
        self.people_counter_btn.clicked.connect(self.open_people_counter)
        left_layout.addWidget(self.people_counter_btn)
        
        controls_layout.addWidget(left_group)
        
        # Right side - Product Scanner
        right_group = QGroupBox("Product Scanner")
        right_layout = QVBoxLayout(right_group)
        
        self.scanner_setup_btn = QPushButton("⚙️ Run Setup")
        self.scanner_setup_btn.clicked.connect(self.run_scanner_setup)
        right_layout.addWidget(self.scanner_setup_btn)
        
        self.scanner_service_btn = QPushButton("🔍 Start Scanner")
        self.scanner_service_btn.clicked.connect(self.toggle_scanner_service)
        right_layout.addWidget(self.scanner_service_btn)
        
        self.scanner_prediction_btn = QPushButton("🖼️ Test Prediction")
        self.scanner_prediction_btn.clicked.connect(self.test_prediction)
        right_layout.addWidget(self.scanner_prediction_btn)
        
        controls_layout.addWidget(right_group)
        layout.addLayout(controls_layout)
        
        # Status area
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Checking system...")
        self.status_label.setStyleSheet("padding: 8px; background-color: #3a3a3a; border-radius: 3px;")
        status_layout.addWidget(self.status_label)
        
        refresh_btn = QPushButton("🔄 Refresh Status")
        refresh_btn.clicked.connect(self.check_system_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        # Quick actions
        quick_layout = QHBoxLayout()
        
        start_all_btn = QPushButton("🚀 Start All")
        start_all_btn.clicked.connect(self.start_all_services)
        start_all_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        quick_layout.addWidget(start_all_btn)
        
        stop_all_btn = QPushButton("🛑 Stop All")
        stop_all_btn.clicked.connect(self.stop_all_services)
        stop_all_btn.setStyleSheet("background-color: #f44336; font-weight: bold;")
        quick_layout.addWidget(stop_all_btn)
        
        layout.addLayout(quick_layout)
        
        # Log area
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_btn)
        
        layout.addWidget(log_group)
        
        self.log("🎯 Retrux Control Panel Ready")
        
    def check_system_status(self):
        self.log("🔍 Checking system status...")
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check directories
        dirs_to_check = [
            "retruxosaproject/app_root/active_state/devices",
            "retruxosaproject/app_root/active_state/product_visual",
            "retruxosaproject/app_root/last_state", 
            "retruxosaproject/app_root/product_information",
            "retruxosaproject/app_root/product_state"
        ]
        
        # Check files
        files_to_check = [
            "cam_service/camera_server.py",
            "cam_display/camera_display_ui.py",
            "people_counter/count.py",
            "product_scan/shelf_scan.py"
        ]
        
        dirs_ok = 0
        files_ok = 0
        
        for dir_path in dirs_to_check:
            if os.path.exists(os.path.join(base_dir, dir_path)):
                dirs_ok += 1
                
        for file_path in files_to_check:
            if os.path.exists(os.path.join(base_dir, file_path)):
                files_ok += 1
        
        # Check images in devices folder
        devices_path = os.path.join(base_dir, "retruxosaproject/app_root/active_state/devices")
        image_count = 0
        if os.path.exists(devices_path):
            image_files = [f for f in os.listdir(devices_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            image_count = len(image_files)
            
        # Check images in product_visual folder
        visual_path = os.path.join(base_dir, "retruxosaproject/app_root/active_state/product_visual")
        visual_count = 0
        if os.path.exists(visual_path):
            visual_files = [f for f in os.listdir(visual_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            visual_count = len(visual_files)
        
        status_text = f"""System Status:
📁 Directories: {dirs_ok}/{len(dirs_to_check)} ✅
📄 Scripts: {files_ok}/{len(files_to_check)} ✅
🖼️ Images in devices: {image_count} ✅
🔍 Product visuals: {visual_count} ✅

Ready to run setup and services!"""
        
        self.status_label.setText(status_text)
        self.log(f"✅ Status updated - {image_count} device images, {visual_count} product visuals")
        
    def run_scanner_setup(self):
        self.log("⚙️ Running scanner setup...")
        self.scanner_setup_btn.setEnabled(False)
        self.scanner_setup_btn.setText("⏳ Setting up...")
        
        # Check if we have images first
        base_dir = os.path.dirname(os.path.abspath(__file__))
        devices_path = os.path.join(base_dir, "retruxosaproject/app_root/active_state/devices")
        
        if not os.path.exists(devices_path):
            self.log("❌ Devices directory not found")
            self.scanner_setup_btn.setEnabled(True)
            self.scanner_setup_btn.setText("⚙️ Run Setup")
            return
            
        image_files = [f for f in os.listdir(devices_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            self.log("❌ No images found in devices directory. Please add some images first.")
            self.scanner_setup_btn.setEnabled(True)
            self.scanner_setup_btn.setText("⚙️ Run Setup")
            return
            
        self.log(f"📁 Found {len(image_files)} images, starting setup...")
        
        # Use QProcess for safer execution
        process = QProcess(self)
        process.finished.connect(lambda code: self.on_setup_finished(code))
        process.readyReadStandardOutput.connect(lambda: self.on_setup_output(process))
        process.readyReadStandardError.connect(lambda: self.on_setup_error(process))
        
        # Store process reference
        self.processes['setup'] = process
        
        # Start the setup process with the fixed script
        process.start(sys.executable, ["product_scan/shelf_scan.py", "setup"])
        
    def on_setup_finished(self, exit_code):
        self.scanner_setup_btn.setEnabled(True)
        self.scanner_setup_btn.setText("⚙️ Run Setup")
        
        if exit_code == 0:
            self.log("✅ Scanner setup completed successfully!")
        else:
            self.log(f"❌ Scanner setup failed with code: {exit_code}")
            
        if 'setup' in self.processes:
            del self.processes['setup']
            
    def on_setup_output(self, process):
        data = process.readAllStandardOutput()
        text = bytes(data).decode('utf-8').strip()
        if text:
            for line in text.split('\n'):
                if line.strip():
                    self.log(f"📄 {line.strip()}")
                    
    def on_setup_error(self, process):
        data = process.readAllStandardError()
        text = bytes(data).decode('utf-8').strip()
        if text:
            for line in text.split('\n'):
                if line.strip():
                    self.log(f"⚠️ {line.strip()}")
        
    def toggle_camera_service(self):
        if 'camera_service' in self.processes:
            self.stop_process('camera_service')
            self.camera_service_btn.setText("🎥 Start Camera Service")
        else:
            self.start_process('camera_service', [sys.executable, "cam_service/camera_server.py"], "Camera Service")
            self.camera_service_btn.setText("🛑 Stop Camera Service")
            
    def toggle_camera_display(self):
        if 'camera_display' in self.processes:
            self.stop_process('camera_display')
            self.camera_display_btn.setText("📺 Start Display")
        else:
            args = [
                sys.executable, "cam_display/display_camera.py",
                "--root-dir", "retruxosaproject/app_root/active_state/devices",
                "--title", "Live Camera Feed"
            ]
            self.start_process('camera_display', args, "Camera Display")
            self.camera_display_btn.setText("🛑 Stop Display")
            
    def toggle_product_display(self):
        if 'product_display' in self.processes:
            self.stop_process('product_display')
            self.product_display_btn.setText("🔍 Product Visual Display")
        else:
            args = [
                sys.executable, "cam_display/display_camera.py",
                "--root-dir", "retruxosaproject/app_root/active_state/product_visual",
                "--title", "Product Visual Display - AI Detection Results"
            ]
            self.start_process('product_display', args, "Product Visual Display")
            self.product_display_btn.setText("🛑 Stop Product Display")
            
    def open_enhanced_display(self):
        try:
            subprocess.Popen([sys.executable, "cam_display/camera_display_ui.py"], 
                           cwd=os.path.dirname(os.path.abspath(__file__)))
            self.log("📊 Enhanced Display window opened")
        except Exception as e:
            self.log(f"❌ Failed to open Enhanced Display: {e}")
            
    def toggle_scanner_service(self):
        if 'scanner_service' in self.processes:
            self.stop_process('scanner_service')
            self.scanner_service_btn.setText("🔍 Start Scanner")
        else:
            self.start_process('scanner_service', [sys.executable, "product_scan/shelf_scan.py", "service"], "Scanner Service")
            self.scanner_service_btn.setText("🛑 Stop Scanner")
            
    def open_people_counter(self):
        try:
            # Simple subprocess for one-time window opening
            subprocess.Popen([sys.executable, "people_counter/people_counter_ui.py"], 
                           cwd=os.path.dirname(os.path.abspath(__file__)))
            self.log("👥 People Counter opened")
        except Exception as e:
            self.log(f"❌ Failed to open People Counter: {e}")
            
    def test_prediction(self):
        # Simple test to see if we can run prediction
        base_dir = os.path.dirname(os.path.abspath(__file__))
        devices_path = os.path.join(base_dir, "retruxosaproject/app_root/active_state/devices")
        
        if not os.path.exists(devices_path):
            self.log("❌ No devices directory found")
            return
            
        image_files = [f for f in os.listdir(devices_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            self.log("❌ No images found for prediction test")
            return
            
        # Test with first image
        test_image = os.path.join(devices_path, image_files[0])
        output_file = "/tmp/test_prediction.json"
        
        self.log(f"🖼️ Testing prediction on: {image_files[0]}")
        
        process = QProcess(self)
        process.finished.connect(lambda code: self.log("✅ Prediction test completed" if code == 0 else "❌ Prediction test failed"))
        process.start(sys.executable, ["product_scan/shelf_scan.py", "predict", "--input", test_image, "--output", output_file])
        
    def start_process(self, process_id, args, name):
        process = QProcess(self)
        process.finished.connect(lambda code: self.log(f"🔄 {name} finished with code {code}"))
        
        self.processes[process_id] = process
        process.start(args[0], args[1:])
        
        self.log(f"🚀 Started {name}")
        
    def stop_process(self, process_id):
        if process_id in self.processes:
            process = self.processes[process_id]
            process.kill()
            process.waitForFinished(3000)
            del self.processes[process_id]
            self.log(f"🛑 Stopped {process_id}")
            
    def start_all_services(self):
        self.log("🚀 Starting all services...")
        
        # Start camera service first
        if 'camera_service' not in self.processes:
            self.toggle_camera_service()
            
        # Then display after a delay
        QTimer.singleShot(2000, lambda: (
            self.toggle_camera_display() if 'camera_display' not in self.processes else None
        ))
        
        # Product display after setup
        QTimer.singleShot(4000, lambda: (
            self.toggle_product_display() if 'product_display' not in self.processes else None
        ))
        
        # Finally scanner
        QTimer.singleShot(3000, lambda: (
            self.toggle_scanner_service() if 'scanner_service' not in self.processes else None
        ))
        
    def stop_all_services(self):
        self.log("🛑 Stopping all services...")
        
        for process_id in list(self.processes.keys()):
            if process_id != 'setup':  # Don't stop setup process
                self.stop_process(process_id)
                
        # Reset button texts
        self.camera_service_btn.setText("🎥 Start Camera Service")
        self.camera_display_btn.setText("📺 Start Display")
        self.product_display_btn.setText("🔍 Product Visual Display")
        self.scanner_service_btn.setText("🔍 Start Scanner")
        
    def clear_log(self):
        self.log_text.clear()
        
    def log(self, message):
        import time
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        self.log("🔄 Shutting down...")
        
        # Stop all processes
        for process_id in list(self.processes.keys()):
            process = self.processes[process_id]
            process.kill()
            process.waitForFinished(1000)
            
        event.accept()

def main():
    # Prevent segmentation fault by ensuring proper cleanup
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Retrux Shelf-Eye System")
    
    window = RetruxLauncher()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())