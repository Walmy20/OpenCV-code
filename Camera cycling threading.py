from threading import Thread
import threading
import cv2, time
import pandas as pd

class VideoStreamWidget(object):
    def __init__(self, camera):
        self.camera_link = camera
        self.online = False
        self.capture = None
        self.capture = None
        self.ret = None
        self.frame = None
        self.lock = threading.Lock() # Lock to ensure thread-safety
        # Start background frame grabbing
        self.thread = Thread(target=self.update_frame, args=())
        self.thread.daemon = True
        self.thread.start()

    def verify_stream(self, link):
        cap = cv2.VideoCapture(link)
        if not cap.isOpened():
            return False
        else:
            cap.release()
            return True

    def update_frame(self):
        if self.verify_stream(self.camera_link):
            self.capture = cv2.VideoCapture(self.camera_link)
            print(self.capture)
            self.online = True 

            while self.capture.isOpened() and self.online:
                ret, frame = self.capture.read()
                if not ret:
                    self.capture.release()
                    self.online = False
                    print("Failed to connect",self.camera_link)
                with self.lock:
                    self.frame = frame
                    
    def show_frame(self):
        if self.frame is not None:
            start_time = time.time()
            while True:
                with self.lock:
                    frame = self.frame
                    online = self.online
                if not online: # Check if the stream is online
                    print("Stream is not online")
                    break
                if frame is not None:
                    current_time = time.strftime("%m-%d-%Y %I:%M:%S %p", time.localtime())
                    cv2.putText(frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.imshow("Crystal Cameras", self.frame)
                    cv2.resizeWindow('Crystal Cameras', 1920, 1080)

                if cv2.waitKey(20) and time.time() - start_time >= 15: 
                    start_time = time.time()
                    break

if __name__ == "__main__":
    print("Starting Program")
    df = pd.read_excel('C:\\Users\\Camera_Areas.xlsx')
    # Lists of your camera RTSP URLs for different areas
    cameras_area1 = df['Camera_Area_1'].dropna().tolist()
    cameras_area2 = df['Camera_Area_2'].dropna().tolist()
    cameras_area3 = df['Camera_Area_3'].dropna().tolist()

    # Combine all camera areas into one list
    all_areas = [cameras_area1, cameras_area2, cameras_area3]

    # 1920x1080 full screen
    cv2.namedWindow('Crystal Cameras', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Crystal Cameras', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    video_stream_widgets = [VideoStreamWidget(camera) for area in all_areas for camera in area]

    while True:
        for widget in video_stream_widgets:
            widget.show_frame()
