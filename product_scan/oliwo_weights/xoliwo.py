import os
import torch
import platform
import json
from PIL          import Image, ImageDraw, ImageOps
from sahi         import AutoDetectionModel
from sahi.predict import get_sliced_prediction, predict, get_prediction
from transformers import (
    RTDetrImageProcessor, 
    DetrForObjectDetection
)

class OliwoModel:
    def __init__(self):
        
        # get model path
        model_path = os.path.dirname(os.path.realpath(__file__))

        # check if device is MacOS or Not..
        current_platform = platform.system().lower()

        # set device to cpu or cuda or mps if on mac
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.device = torch.device('mps') if current_platform == "darwin" else self.device

        self.__base_image_processor__ : RTDetrImageProcessor = RTDetrImageProcessor.from_pretrained(
            model_path, local_files_only = True
        )

        self.__model__ : DetrForObjectDetection = DetrForObjectDetection.from_pretrained(
            model_path, local_files_only = True
        ).to(self.device)

        __detection_classes__ = ['stock']

        self.__detection_model__ = AutoDetectionModel.from_pretrained(
            model_type            = 'huggingface',
            model                 = self.__model__,
            processor             = self.__base_image_processor__,
            confidence_threshold  = 0.8,
            device                = 'cpu'
        )

        print("|")
        print("| Oliwo Model Setup with :", self.device)
        print("| Model Directory        :", model_path)
        print("|")

    
    def predict(self, input_image : Image.Image) -> list[list[int]]:
        prediction_result = get_sliced_prediction(
            input_image,
            self.__detection_model__,
            slice_height = 512,
            slice_width  = 512,
            overlap_height_ratio = 0.45,
            overlap_width_ratio  = 0.45,
            verbose = 0
        )
        
        # Extract bounding boxes
        bounding_boxes = []
        for object_prediction in prediction_result.object_prediction_list:
            predicted_boxes = object_prediction.bbox.to_xyxy()
            predicted_boxes = [int(x) for x in predicted_boxes]
            bounding_boxes.append(predicted_boxes)
            
        return bounding_boxes
    
    def predict_to_file(self, image_path : str, output_file : str) -> None:
        
        # load image 
        print("| Input >", image_path)
        image = self.load_image(image_path)

        # predict xyxy
        predicte_products = self.predict(image)

        # create information name
        pred_prod : list[dict[str, any]] = []
        for i in range(len(predicte_products)):
            
            # create placeholder product name
            indx_str = str(i).zfill(3)
            indx_str = f'product_{indx_str}'

            # create product values
            x = {
                'name'   : indx_str,
                'coords' : predicte_products[i]
            }
            pred_prod.append(x)

        # convert to json
        with open(output_file, "w") as f:
            json.dump(pred_prod, f, indent = 2)

        print("| Output >", output_file)        

    def predict_yolo(self, input_image : Image.Image) -> list[list[float]]:
        # get image dimensions
        img_width, img_height = input_image.size

        # object prediction in xyxy 
        object_prediction_list = self.predict(input_image)
        
        # Extract bounding boxes
        bounding_boxes = []
        for object_prediction in object_prediction_list:
            x_min, y_min, x_max, y_max = object_prediction
            x_center = (x_min + x_max) / 2.0 / img_width
            y_center = (y_min + y_max) / 2.0 / img_height
            width    = (x_max - x_min) / img_width
            height   = (y_max - y_min) / img_height
            bounding_boxes.append([0, x_center, y_center, width, height])            
        return bounding_boxes

    def overlay(self, source_image : Image.Image, predictions : list[list[float]], fill_alpha : int = 64, line_width : int = 3) -> Image.Image:
        # Convert image to RGBA if not already
        if source_image.mode != 'RGBA':
            source_image = source_image.convert('RGBA')
        
        # Create a new image for overlay
        overlay = Image.new('RGBA', source_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw semi-transparent red boxes
        for bbox in predictions:
            draw.rectangle(
                bbox, 
                outline = (128, 0, 128, 128), 
                fill    = (255, 0, 0,   fill_alpha),
                width   = line_width
            )
        
        # Composite the overlay with the original image
        combined = Image.alpha_composite(source_image, overlay)
        combined = combined.convert("RGB")
        return combined

    def load_image(self, fpath : str) -> Image.Image:
        image_cam : Image.Image = Image.open(fpath)
        image_cam : Image.Image = ImageOps.exif_transpose(image_cam)
        return image_cam
    
if __name__ == "__main__":
    print("OLIWO MODEL")
    
    model = OliwoModel('./oliwo_weights')
    
    image_cam : Image.Image = Image.open('./sample_inputs/exsource_1.jpg')
    image_cam : Image.Image = ImageOps.exif_transpose(image_cam)

    #predictions = model.predict(image_cam)
    
    #mask_visual  = model.draw(image_cam, predictions)
    #mask_visual.save('./annotated_images.png')
    
    prediction_yolo = model.predict_yolo(image_cam)

    # export
    
    with open('./target_sample/refrence_image.txt', 'w') as f:
        for coord in prediction_yolo:
            f.write(" ".join(map(str, coord)) + "\n")
    
    image_cam.save('./target_sample/refrence_image.png')
