import time
import cv2
import pandas as pd
from threading import Thread, Lock
from queue import Queue

def verify_stream(link):
    cap = cv2.VideoCapture(link)
    if not cap.isOpened():
        print("Camera link failed to open:", link)
        return False
    else:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Camera link failed ret or frame:", link)
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


def this_receive(camera, queue, lock): 
    start_time = time.time()
    gst_str = ("rtspsrc location=" + camera + " latency=10 ! "
               "rtph264depay ! h264parse ! avdec_h264 ! "
               "videoconvert ! appsink")
    cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
            print(f"Failed to open camera: {camera}")
            return
    #ret, next_frame = cap.read()
    #queue.put(next_frame)
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

    
    # Combine all camera areas into one list
    #all_areas = [verify_and_filter_streams(cameras_area1), 
     #            verify_and_filter_streams(cameras_area2), 
      #           verify_and_filter_streams(cameras_area3)]
    all_areas = [cameras_area1, cameras_area2, cameras_area3]

    #print(all_areas)
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