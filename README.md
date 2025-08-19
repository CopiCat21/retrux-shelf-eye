# 🎯 Retrux Shelf-Eye System

**Intelligent Retail Monitoring & Analytics Platform**

A comprehensive AI-powered system for retail shelf monitoring, product detection, and people counting using computer vision and machine learning.

## 🚀 Features

### 📹 Camera System
- **Multi-camera support** with automatic detection
- **Real-time frame capture** and processing
- **Background service** for continuous operation
- **Grid-based display** with timestamp overlay

### 🔍 Product Scanner
- **AI-powered product detection** using OliwoModel
- **Shelf inventory monitoring** with state tracking
- **Difference detection** between reference and current images
- **Real-time visual output** with bounding boxes
- **JSON-based product information** storage

### 👥 People Counter
- **YOLO-based people detection** in video files
- **Batch processing** support for multiple videos
- **Progress tracking** with real-time updates
- **Results history** and statistics

### 📊 Display Systems
- **Raw camera feed** display
- **AI detection results** visualization
- **Side-by-side comparison** view
- **Enhanced dual monitoring** interface

## 📁 Project Structure

```
retrux-shelf-eye/
├── README.md                           # This documentation
├── main_launcher.py                 # Main control panel
├── cam_service/
│   ├── camera_server.py               # Camera capture service
│   ├── camera_service_ui.py           # Camera service GUI
│   ├── scanner.py                     # Camera detection utility
│   └── background_service.py          # Background camera handler
├── cam_display/
│   ├── display_camera.py              # Basic camera display
│   ├── camera_display_ui.py           # Camera display GUI
│   ├── camera_display_enhanced.py     # Enhanced dual display
│   └── grid_display.py               # Grid layout utilities
├── people_counter/
│   ├── count.py                       # YOLO people detection
│   ├── count-people.zsh              # Shell wrapper
│   ├── people_counter_ui.py           # People counter GUI
│   └── *.mp4                         # Video files for processing
├── product_scan/
│   ├── shelf_scan_fixed.py           # Main scanner logic (fixed paths)
│   ├── shelf_scanner.zsh             # Shell wrapper
│   ├── product_scanner_ui.py         # Product scanner GUI
│   └── oliwo_weights/
│       ├── xoliwo.py                 # AI model implementation
│       └── xcodiff.py                # Image difference detection
└── retruxosaproject/                  # Data storage
    └── app_root/
        ├── active_state/
        │   ├── devices/              # Input camera images
        │   └── product_visual/       # AI detection output
        ├── last_state/              # Reference images
        ├── product_information/     # Product detection JSON
        └── product_state/           # Inventory state tracking
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)
- Webcam/camera (optional, for live capture)

### 1. Clone Repository
```bash
git clone <repository-url>
cd retrux-shelf-eye
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Directory Structure
The system will automatically create required directories, but you can prepare sample images:
```bash
# Add sample images to the devices folder
mkdir -p retruxosaproject/app_root/active_state/devices
# Copy your .jpg images here
```

## 🚀 Quick Start

### Method 1: Using Main Launcher (Recommended)
```bash
python main_launcher.py
```

**First-time setup:**
1. Click **"🔄 Refresh Status"** to check system
2. Add images to `devices/` folder
3. Click **"⚙️ Run Setup"** to initialize AI detection
4. Click **"🚀 Start All"** to begin monitoring

### Method 2: Individual Components
```bash
# Camera Service
python cam_service/camera_service_ui.py

# Enhanced Display
python cam_display/camera_display_ui.py

# People Counter
python people_counter/people_counter_ui.py

# Product Scanner
python product_scan/product_scanner_ui.py
```

## 📋 Usage Guide

### 🎯 Main Control Panel

The main launcher provides centralized control:

#### 📹 Camera & Display System
- **🎥 Start Camera Service**: Begins camera capture
- **📺 Raw Camera Display**: Shows original camera feeds
- **🔍 AI Detection Display**: Shows processed images with detections
- **📊 Enhanced Display (Dual)**: Side-by-side comparison view
- **👥 People Counter**: Opens people counting interface

#### 🛒 Product Scanner & System
- **⚙️ Run Setup**: Initialize AI detection system (run once)
- **🔍 Start Scanner**: Begin real-time product monitoring
- **🖼️ Test Prediction**: Test AI detection on single image

#### 🚀 Quick Actions
- **🚀 Start All**: Launch complete system automatically
- **🛑 Stop All**: Stop all running services

### 🔄 Typical Workflow

1. **Initial Setup** (One-time):
   ```
   Place images in devices/ → Run Setup → Setup complete!
   ```

2. **Daily Operation**:
   ```
   Start All Services → Monitor displays → Review results
   ```

3. **People Counting**:
   ```
   Add video files → Open People Counter → Select video → Run analysis
   ```

### 🎨 Display Options

#### Raw Camera Display
- Shows original images from `devices/` folder
- Grid layout with timestamp
- Real-time updates

#### AI Detection Display  
- Shows processed images from `product_visual/` folder
- Includes bounding boxes and detection labels
- Color-coded results

#### Enhanced Dual Display
- **3 tabs**: Raw Feed, AI Results, Side-by-Side
- **Real-time comparison** between input and output
- **Synchronized updates** across displays

## 🧠 AI Models

### OliwoModel (Product Detection)
- **Model Type**: DETR (Detection Transformer)
- **Classes**: Product detection with bounding boxes
- **Input**: JPG/PNG images
- **Output**: JSON with coordinates and confidence scores

### YOLO (People Detection)
- **Model**: YOLOv11n (default, auto-download)
- **Classes**: Person detection
- **Input**: Video files (MP4, AVI, MOV, etc.)
- **Output**: People count with confidence