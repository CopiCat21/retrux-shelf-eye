import sys
import os
import json
import subprocess
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QGridLayout,
    QListWidget, QTabWidget, QTreeWidget, QTreeWidgetItem, QProgressBar,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

class ProductScanThread(QThread):
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    setup_completed = pyqtSignal()
    service_started = pyqtSignal()
    service_stopped = pyqtSignal()
    
    def __init__(self, command, args=None):
        super().__init__()
        self.command = command
        self.args = args or []
        self.process = None
        
    def run(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            shelf_scan_script = os.path.join(script_dir, 'shelf_scan.py')
            
            if not os.path.exists(shelf_scan_script):
                self.status_updated.emit(f"Error: shelf_scan.py not found at {shelf_scan_script}")
                return
                
            cmd = [sys.executable, shelf_scan_script, self.command] + self.args
            self.status_updated.emit(f"Executing: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    self.status_updated.emit(output.strip())
                    
            return_code = self.process.poll()
            
            if return_code == 0:
                if self.command == "setup":
                    self.setup_completed.emit()
                elif self.command == "service":
                    self.service_stopped.emit()
                self.status_updated.emit(f"Command '{self.command}' completed successfully")
            else:
                self.status_updated.emit(f"Command '{self.command}' failed with code {return_code}")
                
        except Exception as e:
            self.status_updated.emit(f"Error executing command: {e}")
            
    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.status_updated.emit("Process terminated")

class ProductScannerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrux Product Scanner")
        self.setGeometry(100, 100, 1200, 800)
        
        self.current_thread = None
        self.setup_completed = False
        
        self.init_ui()
        self.check_setup_status()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Product Scanner Control Panel")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Setup Tab
        setup_tab = self.create_setup_tab()
        tab_widget.addTab(setup_tab, "Setup")
        
        # Service Tab
        service_tab = self.create_service_tab()
        tab_widget.addTab(service_tab, "Service Control")
        
        # Monitoring Tab
        monitoring_tab = self.create_monitoring_tab()
        tab_widget.addTab(monitoring_tab, "System Monitoring")
        
        # Results Tab
        results_tab = self.create_results_tab()
        tab_widget.addTab(results_tab, "Results & Analysis")
        
        layout.addWidget(tab_widget)
        
        # Status log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(150)
        self.status_log.setReadOnly(True)
        log_layout.addWidget(self.status_log)
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        clear_log_btn.setMaximumWidth(100)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        self.log_status("Product Scanner initialized")
        
    def create_setup_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Setup status
        status_group = QGroupBox("Setup Status")
        status_layout = QGridLayout(status_group)
        
        self.setup_status_label = QLabel("Setup Status: Unknown")
        self.setup_status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.setup_status_label, 0, 0)
        
        self.check_status_btn = QPushButton("Check Status")
        self.check_status_btn.clicked.connect(self.check_setup_status)
        status_layout.addWidget(self.check_status_btn, 0, 1)
        
        layout.addWidget(status_group)
        
        # Setup controls
        setup_group = QGroupBox("Setup Operations")
        setup_layout = QVBoxLayout(setup_group)
        
        setup_info = QLabel(
            "Setup Process:\n"
            "1. Copies device images to create reference state\n"
            "2. Runs AI detection on all images using OliwoModel\n"
            "3. Creates product information JSON files\n"
            "4. Initializes inventory state tracking"
        )
        setup_info.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        setup_layout.addWidget(setup_info)
        
        self.run_setup_btn = QPushButton("Run Setup")
        self.run_setup_btn.clicked.connect(self.run_setup)
        setup_layout.addWidget(self.run_setup_btn)
        
        self.setup_progress = QProgressBar()
        self.setup_progress.setVisible(False)
        setup_layout.addWidget(self.setup_progress)
        
        layout.addWidget(setup_group)
        
        # Directory structure
        structure_group = QGroupBox("Directory Structure")
        structure_layout = QVBoxLayout(structure_group)
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabel("Project Structure")
        structure_layout.addWidget(self.directory_tree)
        
        refresh_tree_btn = QPushButton("Refresh Directory Tree")
        refresh_tree_btn.clicked.connect(self.refresh_directory_tree)
        structure_layout.addWidget(refresh_tree_btn)
        
        layout.addWidget(structure_group)
        
        return tab
        
    def create_service_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Service status
        service_status_group = QGroupBox("Service Status")
        service_status_layout = QGridLayout(service_status_group)
        
        self.service_status_label = QLabel("Service: Stopped")
        self.service_status_label.setStyleSheet("font-weight: bold; color: red;")
        service_status_layout.addWidget(self.service_status_label, 0, 0)
        
        layout.addWidget(service_status_group)
        
        # Service controls
        service_control_group = QGroupBox("Service Control")
        service_control_layout = QVBoxLayout(service_control_group)
        
        service_info = QLabel(
            "Service Process:\n"
            "1. Monitors device directory for new/changed images\n"
            "2. Compares with reference images to detect differences\n"
            "3. Runs AI detection on changed areas\n"
            "4. Updates product states (full/reduced/empty)\n"
            "5. Generates annotated visualization images"
        )
        service_info.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        service_control_layout.addWidget(service_info)
        
        button_layout = QHBoxLayout()
        
        self.start_service_btn = QPushButton("Start Service")
        self.start_service_btn.clicked.connect(self.start_service)
        self.start_service_btn.setEnabled(False)
        
        self.stop_service_btn = QPushButton("Stop Service")
        self.stop_service_btn.clicked.connect(self.stop_service)
        self.stop_service_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_service_btn)
        button_layout.addWidget(self.stop_service_btn)
        service_control_layout.addLayout(button_layout)
        
        layout.addWidget(service_control_group)
        
        # Single prediction test
        prediction_group = QGroupBox("Single Prediction Test")
        prediction_layout = QGridLayout(prediction_group)
        
        prediction_layout.addWidget(QLabel("Input Image:"), 0, 0)
        self.input_image_path = QLabel("No image selected")
        prediction_layout.addWidget(self.input_image_path, 0, 1)
        
        self.browse_image_btn = QPushButton("Browse")
        self.browse_image_btn.clicked.connect(self.browse_image)
        prediction_layout.addWidget(self.browse_image_btn, 0, 2)
        
        self.test_prediction_btn = QPushButton("Test Prediction")
        self.test_prediction_btn.clicked.connect(self.test_prediction)
        prediction_layout.addWidget(self.test_prediction_btn, 1, 0)
        
        layout.addWidget(prediction_group)
        
        return tab
        
    def create_monitoring_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File monitoring
        monitoring_group = QGroupBox("File System Monitoring")
        monitoring_layout = QVBoxLayout(monitoring_group)
        
        # Devices directory
        devices_layout = QHBoxLayout()
        devices_layout.addWidget(QLabel("Input Images (devices):"))
        self.devices_count_label = QLabel("0 files")
        devices_layout.addWidget(self.devices_count_label)
        devices_layout.addStretch()
        monitoring_layout.addLayout(devices_layout)
        
        # Product visual directory
        visual_layout = QHBoxLayout()
        visual_layout.addWidget(QLabel("Output Images (product_visual):"))
        self.visual_count_label = QLabel("0 files")
        visual_layout.addWidget(self.visual_count_label)
        visual_layout.addStretch()
        monitoring_layout.addLayout(visual_layout)
        
        self.refresh_counts_btn = QPushButton("Refresh Counts")
        self.refresh_counts_btn.clicked.connect(self.refresh_file_counts)
        monitoring_layout.addWidget(self.refresh_counts_btn)
        
        layout.addWidget(monitoring_group)
        
        # Auto refresh timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.refresh_file_counts)
        
        auto_refresh_group = QGroupBox("Auto Refresh")
        auto_refresh_layout = QHBoxLayout(auto_refresh_group)
        
        self.auto_refresh_btn = QPushButton("Start Auto Refresh")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        auto_refresh_layout.addWidget(self.auto_refresh_btn)
        
        layout.addWidget(auto_refresh_group)
        
        return tab
        
    def create_results_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Product state table
        state_group = QGroupBox("Product State Summary")
        state_layout = QVBoxLayout(state_group)
        
        self.product_state_table = QTableWidget()
        self.product_state_table.setColumnCount(4)
        self.product_state_table.setHorizontalHeaderLabels(["Product", "State", "Coordinates", "Last Updated"])
        self.product_state_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        state_layout.addWidget(self.product_state_table)
        
        self.refresh_states_btn = QPushButton("Refresh Product States")
        self.refresh_states_btn.clicked.connect(self.refresh_product_states)
        state_layout.addWidget(self.refresh_states_btn)
        
        layout.addWidget(state_group)
        
        return tab
        
    def check_setup_status(self):
        # Check if setup directories exist
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        retrux_dir = os.path.join(base_dir, "retruxosaproject", "app_root")
        
        required_dirs = [
            "last_state",
            "product_information", 
            "product_state",
            "active_state/devices",
            "active_state/product_visual"
        ]
        
        existing_dirs = 0
        for dir_name in required_dirs:
            dir_path = os.path.join(retrux_dir, dir_name)
            if os.path.exists(dir_path):
                existing_dirs += 1
                
        if existing_dirs == len(required_dirs):
            self.setup_completed = True
            self.setup_status_label.setText("Setup Status: Completed")
            self.setup_status_label.setStyleSheet("font-weight: bold; color: green;")
            self.start_service_btn.setEnabled(True)
            self.log_status("Setup appears to be completed")
        else:
            self.setup_completed = False
            self.setup_status_label.setText(f"Setup Status: Incomplete ({existing_dirs}/{len(required_dirs)} directories)")
            self.setup_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.start_service_btn.setEnabled(False)
            self.log_status(f"Setup incomplete: {existing_dirs}/{len(required_dirs)} directories found")
            
        self.refresh_directory_tree()
        
    def run_setup(self):
        if self.current_thread and self.current_thread.isRunning():
            self.log_status("Another operation is already running")
            return
            
        self.current_thread = ProductScanThread("setup")
        self.current_thread.status_updated.connect(self.log_status)
        self.current_thread.setup_completed.connect(self.on_setup_completed)
        
        self.current_thread.start()
        
        self.run_setup_btn.setEnabled(False)
        self.setup_progress.setVisible(True)
        self.setup_progress.setRange(0, 0)  # Indeterminate progress
        
    def on_setup_completed(self):
        self.setup_completed = True
        self.setup_status_label.setText("Setup Status: Completed")
        self.setup_status_label.setStyleSheet("font-weight: bold; color: green;")
        self.start_service_btn.setEnabled(True)
        
        self.run_setup_btn.setEnabled(True)
        self.setup_progress.setVisible(False)
        
        self.check_setup_status()
        self.log_status("Setup completed successfully!")
        
    def start_service(self):
        if not self.setup_completed:
            self.log_status("Cannot start service: Setup not completed")
            return
            
        if self.current_thread and self.current_thread.isRunning():
            self.log_status("Another operation is already running")
            return
            
        self.current_thread = ProductScanThread("service")
        self.current_thread.status_updated.connect(self.log_status)
        self.current_thread.service_stopped.connect(self.on_service_stopped)
        
        self.current_thread.start()
        
        self.service_status_label.setText("Service: Running")
        self.service_status_label.setStyleSheet("font-weight: bold; color: green;")
        self.start_service_btn.setEnabled(False)
        self.stop_service_btn.setEnabled(True)
        
        self.log_status("Product scanner service started")
        
    def stop_service(self):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
            
        self.on_service_stopped()
        
    def on_service_stopped(self):
        self.service_status_label.setText("Service: Stopped")
        self.service_status_label.setStyleSheet("font-weight: bold; color: red;")
        self.start_service_btn.setEnabled(self.setup_completed)
        self.stop_service_btn.setEnabled(False)
        
        self.log_status("Product scanner service stopped")
        
    def browse_image(self):
        file_dialog = QFileDialog()
        image_file, _ = file_dialog.getOpenFileName(
            self,
            "Select Image File", 
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp);;All Files (*)"
        )
        
        if image_file:
            self.input_image_path.setText(image_file)
            
    def test_prediction(self):
        image_path = self.input_image_path.text()
        if not image_path or image_path == "No image selected":
            self.log_status("Please select an image file first")
            return
            
        if not os.path.exists(image_path):
            self.log_status(f"Image file not found: {image_path}")
            return
            
        output_file = "/tmp/test_prediction.json"
        
        self.current_thread = ProductScanThread("predict", ["--input", image_path, "--output", output_file])
        self.current_thread.status_updated.connect(self.log_status)
        self.current_thread.start()
        
    def refresh_directory_tree(self):
        self.directory_tree.clear()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        retrux_dir = os.path.join(base_dir, "retruxosaproject")
        
        if os.path.exists(retrux_dir):
            root_item = QTreeWidgetItem(self.directory_tree, ["retruxosaproject"])
            self.add_directory_items(root_item, retrux_dir)
            self.directory_tree.expandAll()
        else:
            no_data_item = QTreeWidgetItem(self.directory_tree, ["No retrux directory found"])
            
    def add_directory_items(self, parent_item, dir_path):
        try:
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                if os.path.isdir(item_path):
                    dir_item = QTreeWidgetItem(parent_item, [f"{item}/"])
                    self.add_directory_items(dir_item, item_path)
                else:
                    file_item = QTreeWidgetItem(parent_item, [item])
        except PermissionError:
            pass
            
    def refresh_file_counts(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Count devices files
        devices_dir = os.path.join(base_dir, "retruxosaproject", "app_root", "active_state", "devices")
        devices_count = 0
        if os.path.exists(devices_dir):
            devices_count = len([f for f in os.listdir(devices_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        self.devices_count_label.setText(f"{devices_count} files")
        
        # Count visual files
        visual_dir = os.path.join(base_dir, "retruxosaproject", "app_root", "active_state", "product_visual")
        visual_count = 0
        if os.path.exists(visual_dir):
            visual_count = len([f for f in os.listdir(visual_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        self.visual_count_label.setText(f"{visual_count} files")
        
    def toggle_auto_refresh(self):
        if self.monitor_timer.isActive():
            self.monitor_timer.stop()
            self.auto_refresh_btn.setText("Start Auto Refresh")
            self.log_status("Auto refresh stopped")
        else:
            self.monitor_timer.start(5000)  # Refresh every 5 seconds
            self.auto_refresh_btn.setText("Stop Auto Refresh")
            self.log_status("Auto refresh started (5 second interval)")
            
    def refresh_product_states(self):
        self.product_state_table.setRowCount(0)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_dir = os.path.join(base_dir, "retruxosaproject", "app_root", "product_state")
        
        if not os.path.exists(state_dir):
            self.log_status("Product state directory not found")
            return
            
        row = 0
        for file in os.listdir(state_dir):
            if file.endswith('.json'):
                try:
                    with open(os.path.join(state_dir, file), 'r') as f:
                        products = json.load(f)
                        
                    for product in products:
                        self.product_state_table.setRowCount(row + 1)
                        
                        self.product_state_table.setItem(row, 0, QTableWidgetItem(product.get('name', 'Unknown')))
                        self.product_state_table.setItem(row, 1, QTableWidgetItem(product.get('state', 'Unknown')))
                        
                        coords = product.get('coords', [])
                        coords_str = f"[{', '.join(map(str, coords))}]" if coords else "No coordinates"
                        self.product_state_table.setItem(row, 2, QTableWidgetItem(coords_str))
                        
                        # File modification time as last updated
                        mod_time = os.path.getmtime(os.path.join(state_dir, file))
                        mod_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mod_time))
                        self.product_state_table.setItem(row, 3, QTableWidgetItem(mod_time_str))
                        
                        row += 1
                        
                except Exception as e:
                    self.log_status(f"Error reading {file}: {e}")
                    
        self.log_status(f"Loaded {row} product states")
        
    def clear_log(self):
        self.status_log.clear()
        self.log_status("Log cleared")
        
    def log_status(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.status_log.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
            self.current_thread.wait()
        if self.monitor_timer.isActive():
            self.monitor_timer.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = ProductScannerWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())