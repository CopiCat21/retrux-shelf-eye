import os
import time
import argparse
from oliwo_weights.xoliwo import OliwoModel

def find_jpg_images(directory):
    jpg_images = []
    for root, _, files in os.walk(directory):
        for file in files:
            file = str(file)
            if file.lower().endswith('.jpg'):
                jpg_images.append(os.path.join(root, file))
    return sorted(jpg_images, key = lambda x: os.path.basename(x).lower())

if __name__ == "__main__":
    print("Prediction Automatic Update Service")

    # parser for root-directory
    parser = argparse.ArgumentParser(description = 'Camera Display System')
    parser.add_argument('--root-dir',    type = str, required = True, help = 'The root directory path')
    parser.add_argument('--working-dir', type = str, required = True, help = 'The working directory path')
    
    # Parse the arguments
    args = parser.parse_args()

    # Convert the provided path to an absolute path
    root_directory    = str(os.path.abspath(args.root_dir))
    working_directory = str(os.path.abspath(args.working_dir))
    print("Root Directory :", root_directory)
    print("Root Directory :", working_directory)

    # find image lists
    image_file_list = find_jpg_images(root_directory)
    print("Found :", len(image_file_list))

    ## automatic updates here
    oliow_model = OliwoModel()

    # image files
    last_modified_time = [0] * len(image_file_list)

    try:
        while True:
            
            # enumare the file list
            for i, file_path in enumerate(image_file_list):
            
                # Check if the file has been modified
                current_modified = os.path.getmtime(file_path)
                
                # check current modified time
                if current_modified == last_modified_time[i]:
                    continue
                
                file_name = os.path.basename(file_path)

                # last updated time is diffrent
                print("Updating :", file_name)

                # update time
                last_modified_time[i] = current_modified

                # load image frame
                image = oliow_model.load_image(file_path)

                # predict 
                predicted_products = oliow_model.predict(image)

                # create overlay
                ovelayed = oliow_model.overlay(
                    image, 
                    predicted_products,
                    fill_alpha = 0,
                    line_width = 5
                )

                # output path
                output_path = os.path.join(working_directory, file_name)
                ovelayed.save(output_path)

            time.sleep(1)  # Simulate some work
    except KeyboardInterrupt:
        print("Received Ctrl+C. Exiting gracefully...")
    
    print("Exiting...")
