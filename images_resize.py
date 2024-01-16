import cv2
import os

def resize_images(directory):
    i = 0
    for filename in os.listdir(directory):
        if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".PNG") or filename.endswith(".JPG"): 
            img = cv2.imread(os.path.join(directory, filename))
            aspect_ratio = img.shape[1] / float(img.shape[0])
            width = 500
            height = int(width / aspect_ratio)
            dim = (width, height)
            resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
            cv2.imwrite(os.path.join(directory, filename), resized)
        i += 1
        print("Image",i,"Done")
path = r"\\cwv6\\Images\\UI Component Images"
resize_images(path)
