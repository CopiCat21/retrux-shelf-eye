import os
import shutil
import cv2   as cv
import numpy as np

def find_differences(refrence_image_path : str, latest_image_path : str, threshold_value : int = 30):
    
    # Load the two images
    image1 = cv.imread(refrence_image_path)
    image2 = cv.imread(latest_image_path)

    # Check if images are loaded successfully
    if image1 is None or image2 is None:
        print(f"Error: Could not read one or both images.\n  image1: {refrence_image_path}\n  image2: {latest_image_path}")
        return []

    # Ensure the images are the same size
    if image1.shape != image2.shape:
        print("Images must be of the same dimensions")
        return []

    original_height, original_width = image1.shape[:2]

    # Resize images to 1/4 of their original dimensions
    width  = int(original_width * 0.25)
    height = int(original_height * 0.25)
    dim = (width, height)

    image1_resized = cv.resize(image1, dim, interpolation=cv.INTER_AREA)
    image2_resized = cv.resize(image2, dim, interpolation=cv.INTER_AREA)

    # Convert images to grayscale
    gray1 = cv.cvtColor(image1_resized, cv.COLOR_BGR2GRAY)
    gray2 = cv.cvtColor(image2_resized, cv.COLOR_BGR2GRAY)

    # Compute the absolute difference between the two images
    diff = cv.absdiff(gray1, gray2)

    # Threshold the difference image to get the regions with significant differences
    _, threshold = cv.threshold(diff, threshold_value, 255, cv.THRESH_BINARY)

    # Find contours of the regions with differences
    contours, _ = cv.findContours(threshold, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    # Scale the bounding boxes back to the original image dimensions
    bounding_boxes = []
    for contour in contours:
        (x, y, w, h) = cv.boundingRect(contour)
        
        # Scale the coordinates back to the original image size
        x1 = int(x * 4)
        y1 = int(y * 4)
        x2 = int((x + w) * 4)
        y2 = int((y + h) * 4)
        bounding_boxes.append((x1, y1, x2, y2))

    return bounding_boxes

def find_jpg_images(directory) -> list[str]:
    jpg_images : list[str] = []
    for root, _, files in os.walk(directory):
        for file in files:
            file = str(file)
            if file.lower().endswith('.jpg'):
                jpg_images.append(os.path.join(root, file))
    return sorted(jpg_images, key = lambda x: os.path.basename(x).lower())

def create_directory_force(dir_path : str) -> None:
    shutil.rmtree(dir_path, ignore_errors = True)
    os.makedirs(dir_path)

def copy_directory_contents(source_dir : str, target_dir : str):
    """
    Copies all files from source_dir to target_dir.
    Only files directly inside source_dir are copied.
    """
    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Iterate through files in source_dir
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        target_file = os.path.join(target_dir, filename)

        # Copy only files (not subdirectories)
        if os.path.isfile(source_file):
            shutil.copy2(source_file, target_file)
            print(f"Copied: {source_file} -> {target_file}")

def grab_file_from_path(fpath : str) -> tuple[str, str]:

    # get full name
    full_name = os.path.basename(fpath)

    # get without extension
    base_name = os.path.splitext(full_name)[0]

    return (full_name, base_name)


def compute_iou_xyxy(box1: list[int], box2: list[int]) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_width = max(0, x2 - x1)
    inter_height = max(0, y2 - y1)
    inter_area = inter_width * inter_height

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0.0

    return inter_area / union_area

def get_matching_prod_names(boxes: list[list[int]], devices: list[dict[str, any]]) -> list[str]:
    matching_names = set()
    for box in boxes:
        for device in devices:
            iou = compute_iou_xyxy(box, device['coords'])
            if iou > 0.5:
                matching_names.add(device['name'])
    return list(matching_names)

if __name__ == "__main__":
        
    # Example usage
    image1_path = cv.imread(refrence_image_path)
    image2_path = cv.imread(latest_image_path)
    bounding_boxes = find_differences(image1_path, image2_path)

    # Print the bounding boxes in xyxy format
    for bbox in bounding_boxes:
        print(f"Bounding Box: {bbox}")
