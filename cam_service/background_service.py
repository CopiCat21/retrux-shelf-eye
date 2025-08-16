import time
import copy
import random
import threading
import subprocess

import cv2   as cv
import numpy as np

class BackgroundCameraService:
    def __init__(self, task_id : str, camera_index : int, fpath : str):
        self.task_id   = task_id
        self.camera_id = camera_index
        self.fpath     = fpath

        # setup external thread
        self.thread        = threading.Thread(target = self.run)
        self.thread.daemon = True
        self.stop_event    = threading.Event()

    def iterative_laplacian(self, iterations : int = 100) -> np.ndarray:
        
        # intial seed frame
        ret, frame  = self.cam_capture.read()
        
        best_frame = np.zeros_like(frame)
        best_focus = -1

        for _ in range(iterations):
            ret, frame  = self.cam_capture.read()
            
            # break on invalid
            if not ret:
                break

            # valid frame here !
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)  # Convert to grayscale
            laplacian = cv.Laplacian(gray, cv.CV_64F)     # Apply Laplacian filter
            current_focus = np.var(laplacian)             # Compute variance of Laplacian

            if current_focus > best_focus:
                best_frame = copy.copy(frame)
        
        return best_frame    

    def exec_capture_frame(self) -> None:

        # create camera device
        self.cam_capture = cv.VideoCapture(self.camera_id)
        self.cam_capture.set(cv.CAP_PROP_FRAME_WIDTH,  2592) 
        self.cam_capture.set(cv.CAP_PROP_FRAME_HEIGHT, 1944)  
        self.cam_capture.set(cv.CAP_PROP_AUTOFOCUS,    1)     # Enable Autofocus

        # grab initial seed frame
        ret, _  = self.cam_capture.read()

        # frame is valid
        if ret:
            best_frame = self.iterative_laplacian(7)
            best_frame = cv.flip(best_frame, 0) # flip vertical
            best_frame = cv.flip(best_frame, 1) # flip horizontal
            cv.imwrite(self.fpath, best_frame)
        else:
            print("Invalid Camera ! ->", self.camera_id)        

        # relese camera
        self.cam_capture.release()

    def run(self):
        while not self.stop_event.is_set():
            start_time = time.time()
            print(f"Capture of Camera {self.camera_id} Started At: {time.ctime(start_time)}")

            # task execution time between 2 to 9 seconds
            self.exec_capture_frame()

            #end_time = time.time()
            #print(f"Task {self.task_id} finished at: {time.ctime(end_time)}")

            # Calculate the next interval with randomness
            interval = max(0, 5 + random.uniform(-1, 1))
            time.sleep(interval)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()