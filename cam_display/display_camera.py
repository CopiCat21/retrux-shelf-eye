import os
import time
import argparse
import cv2 as cv
import numpy as np
from grid_display import create_grid_datetime

def find_jpg_images(directory):
    jpg_images = []
    for root, _, files in os.walk(directory):
        for file in files:
            file = str(file)
            if file.lower().endswith('.jpg'):
                jpg_images.append(os.path.join(root, file))
    return sorted(jpg_images, key = lambda x: os.path.basename(x).lower())


if __name__ == "__main__":
    print("Display Camera System")

    # parser for root-directory
    parser = argparse.ArgumentParser(description = 'Camera Display System')
    parser.add_argument('--root-dir', type = str, required = True,   help = 'The root directory path')
    parser.add_argument('--title',    type = str, default  = 'Feed', help = 'Display title name')
    
    # Parse the arguments
    args = parser.parse_args()

    # Convert the provided path to an absolute path
    root_directory = os.path.abspath(args.root_dir)
    window_title   = str(args.title)
    print("Root Directory :", root_directory)

    # find image lists
    image_file_list = find_jpg_images(root_directory)
    print("Found :", len(image_file_list))

    ## automatic updates here

    # image files
    last_modified_time = [0] * len(image_file_list)

    # image frame list
    images_frames = [np.zeros(shape = (512, 512, 3), dtype = np.uint8)] *len(image_file_list)
    
    # loop
    while True:
    
        # enumare the file list
        for i, file_path in enumerate(image_file_list):
            
            # Check if the file has been modified
            current_modified = os.path.getmtime(file_path)
            
            # check current modified time
            if current_modified != last_modified_time[i]:
                
                print("Updated :", file_path)

                # update time
                last_modified_time[i] = current_modified

                # Read the image file
                image_array = cv.imread(file_path)
                if image_array is None:
                    print(f"Error: Could not read the image file : '{file_path}'")
                    continue

                # update image time
                images_frames[i] = image_array

        # Create a grid of images
        image_grid = create_grid_datetime(images_frames)

        # Display the grid of images
        cv.imshow(window_title, image_grid)
    
        # update info
        current_datetime = time.time()
        current_datetime = time.ctime(current_datetime)
        print("Updated at :", current_datetime, 'total frames :', len(images_frames))
        
        # Wait for 2 seconds before checking again & Break the loop if 'q' is pressed
        if cv.waitKey(800) & 0xFF == ord('q'):
            break
        

    print("Stopped")
    cv.destroyAllWindows()







