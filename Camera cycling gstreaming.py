import os
# This is need it in case missing DLL when importing cv2
gstreamer_path = "C:\\gstreamer\\1.0\\msvc_x86_64\\bin"
os.add_dll_directory(gstreamer_path)

import time
import cv2
import pandas as pd
from threading import Thread, Lock
from queue import Queue
import subprocess

# Get the Proper Encoding Pipeline for the RTSP Stream
def get_codec(camera):
    command = ["C:\\gstreamer\\1.0\\msvc_x86_64\\bin\\gst-launch-1.0.exe", "-v", "rtspsrc", "location="+camera, "!", "decodebin", "!", "fakesink", "silent=false", "-m"]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if 'H264' in output:
            print('Encoding H264')
            process.terminate()
            gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
                "rtph264depay ! h264parse ! decodebin ! "
                "videorate !  video/x-raw,framerate=24/1 !"
                    "videoconvert ! appsink drop=true")
            return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
        elif 'H265' in output:
            print('Encoding H265')
            process.terminate()
            gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
                "rtph265depay ! h265parse ! decodebin ! "
                "videorate !  video/x-raw,framerate=24/1 !"
                    "videoconvert ! appsink drop=true")
            return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    print(f"H.264 or H.265 decoder not found! Skipping RTSP Url: {camera}")
    return None

# Preprocess the stream in a different Thread
def this_receive(camera, queue, lock): 
    start_time = time.time()
    cap = get_codec(camera)
    
    if cap is None or not cap.isOpened():
            print(f"Failed to open camera: {camera}")
            return
        
    while cap.isOpened() and time.time() - start_time < 25:
        ret, next_frame = cap.read()
        if not ret:
                print(f"Failed to read frame from camera: {camera}")
                break
        current_time = time.strftime("%m-%d-%Y %I:%M:%S %p", time.localtime())
        cv2.putText(next_frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        with lock:
            queue.put(next_frame)  
    cap.release()

# Display the stream in a different Thread
def main_program(queue,lock):
    print("Displaying...")
     # 1920x1080 full screen
    cv2.namedWindow('Crystal Cameras', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Crystal Cameras', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while True:
        with lock:
            if queue.empty() != True:
                frame = queue.get()
                cv2.imshow('Crystal Cameras', frame)
                cv2.resizeWindow('Crystal Cameras', 1920, 1080)
                if cv2.waitKey(20) & 0xFF == ord('q'):
                    break
          
if __name__ == '__main__':
    print("Starting Camera Program ...")
    path = r"\\cwdc2\\MIS\\CCTV REMOTE\\Cameras.xlsx"

    df = pd.read_excel(path)
    # Lists of your camera RTSP URLs for different areas
    cameras_area1 = df['GATEWAY'].dropna().tolist()
    cameras_area2 = df['CP'].dropna().tolist()
    cameras_area3 = df['PA'].dropna().tolist()

    all_areas = [camera_area1,cameras_area2, cameras_area3]
    

    queue = Queue()
    lock = Lock()

    processor = Thread(target=main_program, args=(queue,lock))
    processor.start()

    while True:
        for i, area in enumerate(all_areas):
            for camera in area:
                receiver = Thread(target=this_receive, args=(camera, queue, lock))
                receiver.start()
                receiver.join()
