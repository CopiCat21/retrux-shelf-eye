import sys
import os
import subprocess
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QGridLayout,
    QListWidget, QFileDialog, QProgressBar, QComboBox, QSpinBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

class PeopleCountThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    result_ready = pyqtSignal(str, int)
    finished_processing = pyqtSignal()
    
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        
    def run(self):
        try:
            self.status_updated.emit(f"Starting people counting for: {os.path.basename(self.video_path)}")
            self.progress_updated.emit(10)
            
            # Run the count.py script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            count_script = os.path.join(script_dir, 'count.py')
            
            if not os.path.exists(count_script):
                self.status_updated.emit(f"Error: count.py not found at {count_script}")
                return
                
            self.progress_updated.emit(30)
            self.status_updated.emit("Running YOLO detection...")
            
            # Execute the python script
            result = subprocess.run([
                sys.executable, count_script, 
                '--file-path', self.video_path
            ], capture_output=True, text=True, timeout=300)
            
            self.progress_updated.emit(80)
            
            if result.returncode == 0:
                # Parse the output to extract people count
                output = result.stdout
                try:
                    # Look for the line with people count
                    for line in output.splitlines():
                        if line.strip().startswith("#>"):
                            # Extract number between quotes
                            first_quote = line.find("'")
                            second_quote = line.find("'", first_quote + 1)
                            if first_quote != -1 and second_quote != -1:
                                count_str = line[first_quote + 1:second_quote]
                                people_count = int(count_str)
                                
                                self.progress_updated.emit(100)
                                self.result_ready.emit(self.video_path, people_count)
                                self.status_updated.emit(f"Detection completed: {people_count} people found")
                                return
                                
                    self.status_updated.emit("Error: Could not parse detection result")
                    
                except Exception as e:
                    self.status_updated.emit(f"Error parsing result: {e}")
            else:
                self.status_updated.emit(f"Detection failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.status_updated.emit("Detection timed out (5 minutes)")
        except Exception as e:
            self.status_updated.emit(f"Error during detection: {e}")
        finally:
            self.finished_processing.emit()

class PeopleCounterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrux People Counter")
        self.setGeometry(100, 100, 1000, 700)
        
        self.current_thread = None
        self.video_files = []
        self.results_history = []
        
        self.init_ui()
        self.refresh_video_list()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("People Counter System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Video selection section
        video_group = QGroupBox("Video Selection")
        video_layout = QGridLayout(video_group)
        
        video_layout.addWidget(QLabel("Available Videos:"), 0, 0)
        self.video_list = QComboBox()
        self.video_list.currentTextChanged.connect(self.on_video_selected)
        video_layout.addWidget(self.video_list, 0, 1)
        
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.refresh_video_list)
        video_layout.addWidget(self.refresh_btn, 0, 2)
        
        self.browse_btn = QPushButton("Browse for Video")
        self.browse_btn.clicked.connect(self.browse_video)
        video_layout.addWidget(self.browse_btn, 1, 0)
        
        self.selected_video_label = QLabel("No video selected")
        self.selected_video_label.setStyleSheet("font-style: italic;")
        video_layout.addWidget(self.selected_video_label, 1, 1, 1, 2)
        
        layout.addWidget(video_group)
        
        # Processing controls
        process_group = QGroupBox("Processing Controls")
        process_layout = QVBoxLayout(process_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.process_btn = QPushButton("Start People Counting")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop Processing")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.stop_btn)
        process_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        process_layout.addWidget(self.progress_bar)
        
        # Current status
        self.status_label = QLabel("Ready to process videos")
        self.status_label.setStyleSheet("font-weight: bold;")
        process_layout.addWidget(self.status_label)
        
        layout.addWidget(process_group)
        
        # Results section
        results_group = QGroupBox("Processing Results")
        results_layout = QVBoxLayout(results_group)
        
        # Current result display
        current_result_layout = QHBoxLayout()
        current_result_layout.addWidget(QLabel("Last Result:"))
        
        self.result_label = QLabel("No results yet")
        self.result_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: blue;")
        current_result_layout.addWidget(self.result_label)
        
        current_result_layout.addStretch()
        results_layout.addLayout(current_result_layout)
        
        # Results history
        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(150)
        results_layout.addWidget(QLabel("Results History:"))
        results_layout.addWidget(self.results_list)
        
        layout.addWidget(results_group)
        
        # Activity log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Clear log button
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        clear_log_btn.setMaximumWidth(100)
        log_layout.addWidget(clear_log_btn)
        
        layout.addWidget(log_group)
        
        # Initial log
        self.log_status("People Counter initialized")
        
    def refresh_video_list(self):
        self.video_list.clear()
        self.video_files = []
        
        # Look for video files in current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        
        for file in os.listdir(current_dir):
            if file.lower().endswith(video_extensions):
                self.video_files.append(os.path.join(current_dir, file))
                self.video_list.addItem(file)
                
        if self.video_files:
            self.log_status(f"Found {len(self.video_files)} video files")
            self.process_btn.setEnabled(True)
        else:
            self.video_list.addItem("No video files found")
            self.log_status("No video files found. Use 'Browse for Video' to select a file.")
            
    def browse_video(self):
        file_dialog = QFileDialog()
        video_file, _ = file_dialog.getOpenFileName(
            self, 
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm);;All Files (*)"
        )
        
        if video_file:
            self.video_list.clear()
            self.video_list.addItem(os.path.basename(video_file))
            self.video_files = [video_file]
            self.process_btn.setEnabled(True)
            self.log_status(f"Selected video: {os.path.basename(video_file)}")
            
    def on_video_selected(self, video_name):
        if video_name and video_name != "No video files found":
            # Find full path
            for video_path in self.video_files:
                if os.path.basename(video_path) == video_name:
                    self.selected_video_label.setText(f"Selected: {video_name}")
                    break
        else:
            self.selected_video_label.setText("No video selected")
            
    def start_processing(self):
        current_video = self.video_list.currentText()
        if not current_video or current_video == "No video files found":
            self.log_status("No video selected for processing")
            return
            
        # Find full path
        video_path = None
        for path in self.video_files:
            if os.path.basename(path) == current_video:
                video_path = path
                break
                
        if not video_path or not os.path.exists(video_path):
            self.log_status(f"Video file not found: {current_video}")
            return
            
        # Check if YOLO model exists
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'yolo11n.pt')
        if not os.path.exists(model_path):
            self.log_status("Warning: YOLO model (yolo11n.pt) not found. It will be downloaded automatically.")
            
        # Start processing thread
        self.current_thread = PeopleCountThread(video_path)
        self.current_thread.progress_updated.connect(self.update_progress)
        self.current_thread.status_updated.connect(self.log_status)
        self.current_thread.result_ready.connect(self.show_result)
        self.current_thread.finished_processing.connect(self.on_processing_finished)
        
        self.current_thread.start()
        
        # Update UI
        self.process_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing...")
        
    def stop_processing(self):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.terminate()
            self.current_thread.wait()
            self.log_status("Processing stopped by user")
            
        self.on_processing_finished()
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def show_result(self, video_path, people_count):
        video_name = os.path.basename(video_path)
        result_text = f"{video_name}: {people_count} people detected"
        
        self.result_label.setText(f"{people_count} people detected")
        
        # Add to history
        timestamp = time.strftime("%H:%M:%S")
        history_item = f"[{timestamp}] {result_text}"
        self.results_history.append(history_item)
        self.results_list.addItem(history_item)
        
        # Scroll to bottom
        self.results_list.scrollToBottom()
        
    def on_processing_finished(self):
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready to process videos")
        self.current_thread = None
        
    def clear_log(self):
        self.log_text.clear()
        self.log_status("Log cleared")
        
    def log_status(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, event):
        if self.current_thread and self.current_thread.isRunning():
            self.stop_processing()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = PeopleCounterWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())