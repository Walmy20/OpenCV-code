import time
from datetime import datetime
import pytz
import pandas as pd
import cv2

def verify_stream(link):
    cap = cv2.VideoCapture(link)
    if not cap.isOpened():
        return False
    else:
        cap.release()
        return True

def verify_and_filter_streams(camera_list):
    working_cameras = []
    for camera in camera_list:
        if verify_stream(camera):
            working_cameras.append(camera)
    return working_cameras

print("Starting Cameras")

path = r"\\cwdc2\\MIS\\CCTV REMOTE\\Cameras.xlsx"

df = pd.read_excel(path)
# Lists of your camera RTSP URLs for different areas
cameras_area1 = df['Camera_Area_1'].dropna().tolist()
cameras_area2 = df['Camera_Area_2'].dropna().tolist()
cameras_area3 = df['Camera_Area_3'].dropna().tolist()

# Combine all camera areas into one list
#all_areas = [cameras_area1,cameras_area2 ... ]
all_areas = [verify_and_filter_streams(cameras_area1), 
             verify_and_filter_streams(cameras_area2), 
             verify_and_filter_streams(cameras_area3)]

# 1920x1080 full screen
cv2.namedWindow('Crystal Cameras', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Crystal Cameras', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

start_time = time.time()
while True:
    # Re-verify the cameras every 10 minutes
    if time.time() - start_time >= 600:
        all_areas = [verify_and_filter_streams(cameras_area1), verify_and_filter_streams(cameras_area2), verify_and_filter_streams(cameras_area3)]
        start_time = time.time()

    for i, area in enumerate(all_areas):
        for camera in area:
            if verify_stream(camera): # Another verifying just and case the stream goes down. It will skip that one. Then it will be removed from the list.
                cap = cv2.VideoCapture(camera)
                
                # Read until video is completed
                while cap.isOpened():
                    # Capture frame-by-frame
                    ret, frame = cap.read()
                    
                    # Get the current time including when UTC for camera_area1
                    if i == 0:
                        current_time = datetime.now(pytz.timezone('America/Chicago')).strftime("%m-%d-%Y %I:%M:%S %p")  # 12-hour format
                    else:
                        current_time = time.strftime("%m-%d-%Y %I:%M:%S %p", time.localtime())  # 12-hour format
                    
                    
                    # Put the current time on the frame
                    cv2.putText(frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    # Display the resulting frame
                    cv2.imshow('Crystal Cameras', frame)
                    cv2.resizeWindow('Crystal Cameras', 1920, 1080)

                
                    # Break the loop and switch camera after 20 seconds total
                    if cv2.waitKey(20) and time.time() - start_time >= 20:
                        start_time = time.time()
                        cap.release()
                        break
                
                # When everything is done, release the video capture and video write objects
                cap.release()
