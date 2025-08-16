from oliwo_weights.xoliwo import OliwoModel
from datetime import datetime

if __name__ == "__main__":
    # print("Sample Forward Pass")

    oliwo = OliwoModel()

    # load image
    image = oliwo.load_image('/Users/retruxosaproject/app_root/active_state/devices/camera_005_frame.jpg')

    # predict
    predicted_products = oliwo.predict(image)

    # draw boxes
    ovelayed = oliwo.overlay(image, predicted_products)
    ovelayed.save('/Users/retruxosaproject/app_root/binaries/product_scan/sample/prediction.png')
