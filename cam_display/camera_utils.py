import cv2

def list_available_cameras(max_to_test=10):
    """Test camera indices from 0 to max_to_test-1 and return list of working ones."""
    available_cameras = []
    for i in range(max_to_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras.append(i)
            cap.release()
    return available_cameras
