import os
gstreamer_path = "C:\\gstreamer\\1.0\\msvc_x86_64\\bin"
os.add_dll_directory(gstreamer_path)

import cv2
import pandas as pd
from threading import Thread #, Lock
#from queue import Queue
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGridLayout, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
import sys
import numpy as np

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
            return 'H264'
        elif 'H265' in output:
            print('Encoding H265')
            process.terminate()
            return 'H265'
    print(f"H.264 or H.265 decoder not found! Skipping RTSP Url: {camera}")
    return None

def set_cap(camera):
     codec = get_codec(camera)
     if codec == 'H264':
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
            "rtph264depay ! h264parse ! decodebin ! "
            "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
     elif codec == 'H265':
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
            "rtph265depay ! h265parse ! decodebin ! "
            "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
    else:
        print(f"Unsupported video encoding for RTSP Url: {camera}")
        return None


class VideoThread(QThread):
    changePixmap = pyqtSignal(QPixmap)

    def __init__(self, camera, label):
        QThread.__init__(self)
        self.camera = camera
        self.label = label

    def run(self):
        print("VideoThread started") 
        cap = set_cap(self.camera)
        if cap is None:
            # Create a black image if the RTSP URL is incorrect
            rgb_image = np.zeros((480, 640, 3), dtype=np.uint8)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = QPixmap.fromImage(convert_to_Qt_format)
            self.changePixmap.emit(p)
            return
        while True:
            ret, frame = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = QPixmap.fromImage(convert_to_Qt_format)#p = convert_to_Qt_format #p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)
    @pyqtSlot(QPixmap)
    def updatePixmap(self, image):
        self.label.setPixmap(image)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Cameras CWD-Video'
        self.full_screen = True  # Add a flag to indicate full screen mode
        self.initUI()

    def initUI(self):
        print("initUI called") 
        self.setWindowTitle(self.title)
        layout = QGridLayout()
        self.setLayout(layout)

        # Create labels for displaying the video
        self.labels = [QLabel(self) for _ in range(4)]
        for i, label in enumerate(self.labels):
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy to expanding
            if not self.full_screen:  # If the application is not in full screen mode
                label.setFixedSize(640, 480)  # Set fixed size to 640x480 when not in full screen mode
            label.setScaledContents(True)  # Set scale contents to true
            
            label.mousePressEvent = self.get_label_click_handler(i)  # Add mouse click event handler
            layout.addWidget(label, i // 2, i % 2)  # Arrange labels in a 2x2 grid

        # Lists of your camera RTSP URLs for different areas
        path = r"C:\\Users\\walmym\\Desktop\\Downloads\\Scripts\\Camera App\\Camera.xlsx"
        df = pd.read_excel(path)
        cameras = df['Cameras'].dropna().tolist()

        # Create and start video threads for each camera
        self.threads = [VideoThread(camera, label) for camera, label in zip(cameras, self.labels)]
        for thread in self.threads:
            thread.changePixmap.connect(thread.updatePixmap)
            thread.start()

        # Make the window full screen
        self.showFullScreen()     
        



    def get_label_click_handler(self, i):
        def handler(event):
            # Hide all labels
            for label in self.labels:
                label.hide()
            # Show only the clicked label
            self.labels[i].show()
            self.full_screen = False  # Set full screen flag to False
        return handler

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:  # If the 'Escape' key is pressed
            if not self.full_screen:  # If the application is not in full screen mode
                # Show all labels
                for label in self.labels:
                    label.show()
                self.full_screen = True  # Set full screen flag to True
        super().keyPressEvent(event)

       
if __name__ == '__main__':
    print("Starting Camera Program ...")
    app = QApplication(sys.argv)
    ex = App()
    
     # Get the screen size of the primary monitor
    screen = app.primaryScreen()
    size = screen.size()
    print(size)
    # Set the width and height of the application window to match the primary monitor
    ex.setFixedSize(size.width(), size.height())
    
    ex.show()
    sys.exit(app.exec_())
  
