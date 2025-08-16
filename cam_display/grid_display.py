import cv2
import numpy as np
import math
import time

def resize_image(image : np.ndarray, new_height : int) -> np.ndarray:
    # Get the original dimensions
    height, width = image.shape[:2]

    # Calculate the new width to maintain the aspect ratio
    aspect_ratio = width / height
    new_width = int(new_height * aspect_ratio)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))

    return resized_image

def create_image_grid(images : list[np.ndarray]) -> np.ndarray:
    # Determine the number of images
    num_images = len(images)

    # Calculate the grid size (n x n)
    n = math.ceil(math.sqrt(num_images))

    # Calculate the average height of the images
    total_height = sum(image.shape[0] for image in images)
    average_height = total_height // num_images

    # Resize all images to have the same height while maintaining aspect ratio
    resized_images = [resize_image(image, average_height) for image in images]

    # Calculate the maximum width among the resized images
    max_width = max(image.shape[1] for image in resized_images)

    # Calculate the size of each cell in the grid
    cell_width  = max_width + 5  # Add 5 pixels for the line between images
    cell_height = average_height + 5  # Add 5 pixels for the line between images

    # Create a blank canvas for the grid
    grid_width  = n * cell_width
    grid_height = n * cell_height
    grid = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)

    # Fill the grid with the images
    for i in range(n):
        for j in range(n):
            index = i * n + j
            if index < num_images:
                x = j * cell_width
                y = i * cell_height
                img_height, img_width = resized_images[index].shape[:2]
                grid[y:y+img_height, x:x+img_width] = resized_images[index]

    return grid


def resize_image_by_smallest_side(image : np.ndarray, smallest_side : int = 728) -> np.ndarray:
    # Get the dimensions of the original image
    height, width = image.shape[:2]

    # Determine the scaling factor
    if height < width:
        scaling_factor = smallest_side / height
    else:
        scaling_factor = smallest_side / width

    # Calculate the new dimensions
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))

    return resized_image

def create_fixed_grid(image_list : list[np.ndarray], max_size : int = 728) -> np.ndarray:

    # create grid of images
    image_grid = create_image_grid(image_list)

    # resize to size
    image_grid = resize_image_by_smallest_side(image_grid, max_size)

    return image_grid

def add_datetime_bar(image : np.ndarray) -> np.ndarray:
    # Get the dimensions of the original image
    height, width = image.shape[:2]

    # Define the height of the black bar
    bar_height = 30

    # Create a black bar
    black_bar = np.zeros((bar_height, width, 3), dtype=np.uint8)

    # Combine the black bar and the original image
    image_with_bar = np.vstack((black_bar, image))

    # Get the current date and time
    current_datetime = time.time()
    current_datetime = time.ctime(current_datetime)

    # Put the current date and time on the black bar in green text
    font           = cv2.FONT_HERSHEY_SIMPLEX
    font_scale     = 0.7
    font_thickness = 2
    text_color     = (0, 255, 0)  # Green color
    text_position  = (10, 20)  # Position of the text

    # put the image
    cv2.putText(image_with_bar, current_datetime, text_position, font, font_scale, text_color, font_thickness)
    return image_with_bar


def create_grid_datetime(image_list : list[np.ndarray], max_size : int = 728) -> np.ndarray:

    # create the image grid
    image_grid = create_fixed_grid(image_list, max_size)
    
    # add datetime
    image_grid = add_datetime_bar(image_grid)

    return image_grid

if __name__ == "__main__":
    print('Display Grid Example')

    # Example usage
    # Assume `image_list` is your list of NumPy arrays representing images
    image_list = [
        np.random.randint(0, 255, (120, 100, 3), dtype=np.uint8),  # Example image with height 120 and width 100
        np.random.randint(0, 255, (80, 140, 3), dtype=np.uint8),   # Example image with height 80 and width 140
        np.random.randint(0, 255, (150, 130, 3), dtype=np.uint8),  # Example image with height 150 and width 130
        np.random.randint(0, 255, (90, 110, 3), dtype=np.uint8),   # Example image with height 90 and width 110
        np.random.randint(0, 255, (110, 120, 3), dtype=np.uint8),  # Example image with height 110 and width 120
        np.random.randint(0, 255, (130, 150, 3), dtype=np.uint8),  # Example image with height 130 and width 150
        np.random.randint(0, 255, (100, 90, 3), dtype=np.uint8),   # Example image with height 100 and width 90
    ]

    # Create the grid
    image_grid = create_grid_datetime(image_list, 728)

    # Display the grid
    cv2.imshow('Image Grid', image_grid)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
