import cv2
import os

def resize_images(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".PNG") or filename.endswith(".JPG"): 
            img = cv2.imread(os.path.join(directory, filename))
            aspect_ratio = img.shape[1] / float(img.shape[0])
            width = 500
            height = int(width / aspect_ratio)
            dim = (width, height)
            resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
            cv2.imwrite(os.path.join(directory, filename), resized)
            print("Done")
path = r"C:\\Users\\walmym\\Desktop\\Downloads\\Scripts\\Camera Detection\\Images_UI"
resize_images(path)
