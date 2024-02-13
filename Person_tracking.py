import time
import cv2
import pandas as pd
from threading import Thread, Lock
from queue import Queue
from collections import defaultdict
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors



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
    cap = cv2.VideoCapture(camera)
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
        #current_time = time.strftime("%m-%d-%Y %I:%M:%S %p", time.localtime())
        #cv2.putText(next_frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        with lock:
            queue.put(next_frame)  
    cap.release()

def main_program(queue,lock):
     # 1920x1080 full screen
    cv2.namedWindow('Crystal Cameras', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Crystal Cameras', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while True:
        with lock:
            if queue.empty() != True:
                frame = queue.get()
                results =  model.track(frame, persist=True, classes = classes)
                if results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu()
                    track_ids = results[0].boxes.id.int().cpu().tolist()
                    clss = results[0].boxes.cls.cpu().tolist()

                    annotator = Annotator(frame, line_width=line_thickness, example=str(names))
                    for box, track_id, cls in zip(boxes, track_ids, clss):
                        annotator.box_label(box, str(names[cls]), color=colors(cls, True))

                cv2.imshow('Crystal Cameras', frame)
                cv2.resizeWindow('Crystal Cameras', 1920, 1080)
                if cv2.waitKey(20) & 0xFF == ord('q'):
                    break
          
if __name__ == '__main__':
    path = r"\\cwdc2\\MIS\\CCTV REMOTE\\Cameras.xlsx"
    #path = input("Please enter directory path: ")
    #path = r"{}".format(path)

    df = pd.read_excel(path)
    # Lists of your camera RTSP URLs for different areas
    cameras_area1 = df['GATEWAY'].dropna().tolist()
    cameras_area2 = df['CP'].dropna().tolist()
    cameras_area3 = df['PA'].dropna().tolist()
    print("Checking Cameras ...")
    # Combine all camera areas into one list
    all_areas = [verify_and_filter_streams(cameras_area1), 
                 verify_and_filter_streams(cameras_area2), 
                 verify_and_filter_streams(cameras_area3)]
    print("Starting Camera Program ...")
    #all_areas = [cameras_area1, cameras_area2, cameras_area3]
    #print(all_areas)
    queue = Queue()
    lock = Lock()

    device = 0
    # Importing YOLOv8 model 
    model = YOLO('yolov8n.pt')
    model.to("cuda") if device == 0 else model.to("cpu")
    # Extract classes name
    names = model.model.names
    track_history = defaultdict(list)
    classes = 0 # Only person
    line_thickness = 2
    track_thickness = 2


    processor = Thread(target=main_program, args=(queue,lock))
    processor.start()
    while True:
        
        for i, area in enumerate(all_areas):
            for camera in area:
                receiver = Thread(target=this_receive, args=(camera, queue, lock))
                receiver.start()
                receiver.join()