import os
import shutil
import threading
import time
import random

# local relative imports
from scanner            import scan_camera
from background_service import BackgroundCameraService

if __name__ == "__main__":
    print("Background Camera Server System")

    # Jangan di Ganti
    root_directory = "../retruxosaproject/app_root/active_state"
    root_directory = os.path.join(root_directory, 'devices')

    # clear directory
    shutil.rmtree(root_directory, ignore_errors = True)
    os.makedirs(root_directory)

    # scan for cameras
    print("Searching For Valid Cameras...")
    valid_cameras = scan_camera()
    print(f"Found {len(valid_cameras)} Cameras")

    # setup service list
    running_services : list[BackgroundCameraService] = []

    # setup for camera directories
    for camera_id in valid_cameras:

        # create directory format
        camera_str = str(camera_id).zfill(3)

        # create camera directory
        # camera_root_dir = os.path.join(root_directory, camera_str)
        # os.makedirs(camera_root_dir, exist_ok = True)
        
        # create file path
        latest_frame_file = os.path.join(root_directory, f'camera_{camera_str}_frame.jpg')

        camera_service = BackgroundCameraService(camera_str, camera_id, latest_frame_file)
        running_services.append(camera_service)
    
    print("Starting Background Services...")
    for camera_service in running_services:
        print(f"Starting {camera_service.camera_id} ...")
        camera_service.start()
        time.sleep(1.5 + random.uniform(-1, 1))
    
    print("All Service Is Running")

    try:
        
        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping all services...")
        for task in running_services:
            task.stop()
        for task in running_services:
            task.thread.join()
    print("All Services is Finished...")