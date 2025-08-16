import os
import argparse
from ultralytics import YOLO

def extract_from_stdout(s: str) -> int:
    for line in s.splitlines():
        line = line.strip()
        if line.startswith("#>"):
            # Found the line, now extract the number between single quotes
            first_quote = line.find("'")
            if first_quote == -1:
                raise ValueError(f"Opening quote not found in line: {line}")
            
            second_quote = line.find("'", first_quote + 1)
            if second_quote == -1:
                raise ValueError(f"Closing quote not found in line: {line}")
            
            number_str = line[first_quote + 1 : second_quote]
            if not number_str.isdigit():
                raise ValueError(f"Expected digits between quotes, got: {number_str} in line: {line}")
            
            return int(number_str)

    raise ValueError("No line starting with '#>' containing quoted integer found.")

if __name__ == "__main__":

    # setup args
    # parser for root-directory
    parser = argparse.ArgumentParser(description = 'Camera Display System')
    parser.add_argument('--file-path', type = str, required = True, help = 'Absolute File Path')    

    # Parse the arguments
    args = parser.parse_args()

    # Convert the provided path to an absolute path
    file_path = os.path.abspath(args.file_path)

    # get model path from the file path
    model_path = os.path.dirname(os.path.realpath(__file__))
    model_path = os.path.join(model_path, 'yolo11n.pt') # You can use yolov8s.pt, yolov8m.pt, etc.
    
    # Load the pretrained YOLOv8 model
    model = YOLO(model_path)  

    # Load your image
    results = model(file_path, verbose = False)

    # Get the detections
    detections = results[0].boxes

    # Count the number of people (class 0 in COCO is 'person')
    person_count = sum(1 for box in detections if int(box.cls) == 0)

    print(f"#> Predicted People : '{person_count}'")