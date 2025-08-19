import cv2 as cv

def scan_camera(search_limit: int = 100) -> list[int]:
    valid_cameras: list[int] = []
    for index in range(search_limit):
        print("Searching :", index, "->", flush=True, end=' ')

        # pakai CAP_V4L2 biar lebih stabil di Linux
        cam_capture = cv.VideoCapture(index, cv.CAP_V4L2)

        # kasih waktu kamera init
        if cam_capture.isOpened():
            ret, _ = cam_capture.read()
        else:
            ret = False

        cam_capture.release()

        if ret:
            print('Valid')
            valid_cameras.append(index)
        else:
            print("Invalid")
    
    return valid_cameras

if __name__ == "__main__":
    import pprint as pp

    print("Scanning Cameras !")
    valid_cameras = scan_camera(10)

    print("Valid Cameras :")
    pp.pprint(valid_cameras)

    print("Scanning Complete")
