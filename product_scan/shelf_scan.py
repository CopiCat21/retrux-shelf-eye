import os
import json
import time
import shutil
import argparse


from oliwo_weights.xoliwo  import OliwoModel
from oliwo_weights.xcodiff import (
    find_differences, 
    find_jpg_images, 
    create_directory_force,
    copy_directory_contents,
    grab_file_from_path,
    get_matching_prod_names
)

# setup root path
absolute_root_directory = './retruxosaproject/app_root/active_state'

def predict_single_file(oliwo : OliwoModel, src : str, trg : str) -> None:
    oliwo.predict_to_file(
        image_path  = src,
        output_file = trg
    )

def load_prdocuts(latest_frame_file : str):
    global absolute_root_directory

    # get directories
    src_dir = os.path.join(absolute_root_directory, 'devices')
    ltt_dir = os.path.join(absolute_root_directory, 'last_state')
    inf_dir = os.path.join(absolute_root_directory, 'product_information')
    stt_dir = os.path.join(absolute_root_directory, 'product_state')

    fname, base_name = grab_file_from_path(latest_frame_file)
    prod_info_jsf = os.path.join(inf_dir, f"{base_name}.json")
    with open(prod_info_jsf, 'r') as file:
        products_list : list[dict[str, any]] = json.load(file)

    # assuming everything at the latest is empty
    product_latest_state = [
        {
            'name'   : x['name'],
            'coords' : x['coords'],
            'state'  : 'full'
        }
        for x in products_list
    ]
    
    prod_info_jsf = os.path.join(stt_dir, f"{base_name}.json")
    if os.path.exists(prod_info_jsf):
        with open(prod_info_jsf, 'r') as file:
            product_latest_state : list[dict[str, any]] = json.load(file)

    return (products_list, product_latest_state)


def compute_device_diff(oliwo : OliwoModel, image_file : str) -> None:
    global absolute_root_directory

    # get directories
    src_dir = os.path.join(absolute_root_directory, 'devices')
    ltt_dir = os.path.join(absolute_root_directory, 'last_state')
    inf_dir = os.path.join(absolute_root_directory, 'product_information')
    stt_dir = os.path.join(absolute_root_directory, 'product_state')
    
    # get file names
    latest_frame_file   = os.path.join(src_dir, f"{image_file}.jpg")
    previous_frame_file = os.path.join(ltt_dir, f"{image_file}.jpg")

    # find all difrences between them
    diffrence_xyxy = find_differences(previous_frame_file, latest_frame_file)

    # predict all boxes
    latest_image = oliwo.load_image(latest_frame_file)
    predicted_xyxy = oliwo.predict(latest_image)
    
    # load all product info

    # Load JSON file
    fname, base_name = grab_file_from_path(latest_frame_file)
    products_list, product_latest_state = load_prdocuts(latest_frame_file)

    # get valid
    img_diff_names = get_matching_prod_names(diffrence_xyxy, products_list)
    img_pred_names = get_matching_prod_names(predicted_xyxy, products_list)

    # loop over everything thing
    for i in range(len(product_latest_state)):

        # get product
        prod = product_latest_state[i]
        prod_name = prod['name']

        # check if exist in both
        exist_in_diff = any([xn == prod_name for xn in img_diff_names])
        exist_in_pred = any([xn == prod_name for xn in img_pred_names])

        if exist_in_diff and exist_in_pred:
            product_latest_state[i]['state'] = 'reduced'
        
        if exist_in_diff and not exist_in_pred:
            product_latest_state[i]['state'] = 'empty'

    # convert to json
    prod_info_jsf = os.path.join(stt_dir, f"{base_name}.json")
    with open(prod_info_jsf, "w") as f:
        json.dump(product_latest_state, f, indent = 2)

    return diffrence_xyxy, predicted_xyxy

def setup_directories(oliwo : OliwoModel) -> None:
    global absolute_root_directory

    # original image dir
    source_dir  = os.path.join(absolute_root_directory, 'devices')
    image_files = find_jpg_images(source_dir)
    print(f"Found {len(image_files)} Devices")

    # setup state directories
    print("Setting up state directory")
    last_state_dir = os.path.join(absolute_root_directory, 'last_state')
    create_directory_force(last_state_dir)
    copy_directory_contents(
        source_dir = source_dir,
        target_dir = last_state_dir
    )

    print("Setup Product Directories")
    information_dir = os.path.join(absolute_root_directory, 'product_information')
    create_directory_force(information_dir)
    for image_file_path in image_files:

        # grab base path
        fname, base_name = grab_file_from_path(image_file_path)

        # output file
        out_file = os.path.join(information_dir, f"{base_name}.json")
        oliwo.predict_to_file(
            image_path  = image_file_path,
            output_file = out_file
        )

    # first pass towards to computations
    product_state_dir = os.path.join(absolute_root_directory, 'product_state')
    create_directory_force(product_state_dir)

    # create initial states
    for image_path in image_files:
        _, base_name = grab_file_from_path(image_path)
        compute_device_diff(oliwo, base_name)

    print("setup Complete")

def running_service(oliwo : OliwoModel):
    global absolute_root_directory

    # get directories
    src_dir = os.path.join(absolute_root_directory, 'devices')
    ltt_dir = os.path.join(absolute_root_directory, 'last_state')
    inf_dir = os.path.join(absolute_root_directory, 'product_information')
    stt_dir = os.path.join(absolute_root_directory, 'product_state')
    vos_dir = os.path.join(absolute_root_directory, 'product_visual')
    os.makedirs(vos_dir, exist_ok = True)

    image_file_list = find_jpg_images(src_dir)
    print(f"Found {len(image_file_list)} Devices")

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
                

                # last updated time is diffrent
                file_name, base_name = grab_file_from_path(file_path)
                print("Updating :", file_name)
                
                diffrence_xyxy, predicted_xyxy = compute_device_diff(oliwo, base_name)

                # update time
                last_modified_time[i] = current_modified

                # load image frame
                image = oliwo.load_image(file_path)

                # create overlay
                ovelayed = oliwo.overlay(
                    image, 
                    predicted_xyxy,
                    fill_alpha = 0,
                    line_width = 5
                )

                # output path
                output_path = os.path.join(vos_dir, file_name)
                ovelayed.save(output_path)

            time.sleep(1)  # Simulate some work
    except KeyboardInterrupt:
        print("Received Ctrl+C. Exiting gracefully...")
    

if __name__ == "__main__":
    print("Shelf Scanner")

    parser = argparse.ArgumentParser(description="Shelf Scan Service")
    subparsers = parser.add_subparsers(dest = "command",  required = True)

    # Predict command
    predict_parser = subparsers.add_parser("predict", help = "Predict Single File")
    predict_parser.add_argument("--input",  required = True, help = "Input image file")
    predict_parser.add_argument("--output", required = True, help = "Output JSON file")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help = "Setup environment")

    # Service command
    service_parser = subparsers.add_parser("service", help = "Start service")

    # Parse the Arguments 
    args = parser.parse_args()

    # selected ars
    selected_command = str(args.command)

    # setup model 
    oliow_model_x = OliwoModel()

    if selected_command == "predict":

        # prediction
        print("## Single Prediction Mode ##")
        predict_single_file(
            oliow_model_x, args.input, args.output
        )

    elif selected_command == "setup":
        print("# Setup Directory")
        setup_directories(oliow_model_x)

    elif selected_command == "service":
        print("Running Shelf Diff Service")
        running_service(oliow_model_x)

    else:
        print("Arguments need to be Selected")

    print("Exiting...")


