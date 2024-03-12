import os
gstreamer_path = "C:\\gstreamer\\1.0\\msvc_x86_64\\bin"
os.add_dll_directory(gstreamer_path)

import cv2
import pandas as pd
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QGridLayout, QSizePolicy, QComboBox, QVBoxLayout
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
            process.terminate()
            return 'H264'
        elif 'H265' in output:
            process.terminate()
            return 'H265'
    print(f"H.264 or H.265 decoder not found! Skipping RTSP Url: {camera}")
    return None

def set_cap(camera):
     codec = get_codec(camera)
     if codec == 'H264':
        print('Encoding H264')
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
            "rtph264depay ! h264parse ! decodebin ! "
            "videoscale ! video/x-raw,width=640,height=480 ! "
            "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
     elif codec == 'H265':
        print('Encoding H265')
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
            "rtph265depay ! h265parse ! decodebin ! "
            "videoscale ! video/x-raw,width=640,height=480 ! "
            "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
     else:
        print(f"Unsupported video encoding for RTSP Url: {camera}")
        return None

def set_cap_high(camera):
     codec = get_codec(camera)
     if codec == 'H264':
        print('High-Res Encoding H264')
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
            "rtph264depay ! h264parse ! decodebin ! "
            "videoscale ! video/x-raw,width=1280,height=720 ! "
            "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
     elif codec == 'H265':
        print('High-Res Encoding H265')
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
            "rtph265depay ! h265parse ! decodebin ! "
            "videoscale ! video/x-raw,width=1280,height=720 ! "
            "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
        return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
     else:
        print(f"Unsupported video encoding for RTSP Url: {camera}")
        return None

class VideoThread(QThread):
    changePixmap = pyqtSignal(QPixmap)

    def __init__(self, camera, label, high_res=False):
        QThread.__init__(self)
        self.camera = camera
        self.label = label
        self.high_res = high_res

    def run(self):
        print("VideoThread started") 
        cap = set_cap_high(self.camera) if self.high_res else set_cap(self.camera)
        self.cap = cap
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

            # This if was created for Person tracking 
            if self.high_res and ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = QPixmap.fromImage(convert_to_Qt_format)
                self.changePixmap.emit(p)
                
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = QPixmap.fromImage(convert_to_Qt_format)
                self.changePixmap.emit(p)
    @pyqtSlot(QPixmap)
    def updatePixmap(self, image):
        self.label.setPixmap(image)
    
    def stop(self):
        if self.cap is None: # If cap is None just Stop the Qthread
            self.quit()
        else:
            self.cap.release()  # Stop the video capture
            self.quit()  # Stop the QThread


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Cameras CWD-Video'
        self.full_screen = True  # Add a flag to indicate full screen mode
        self.path = r"C:\\Users\\walmym\\Desktop\\Downloads\\Scripts\\Camera App\\Camera.xlsx"
        self.df = pd.read_excel(self.path)
        #self.cameras = self.df['Cameras'].dropna().tolist()
        self.groups = {group: self.df[group].dropna().tolist() for group in ["Group1", "Group2", "Group3"]}  # Define your groups here
        self.cameras = self.groups["Group1"]
        self.initUI()

    def initUI(self):
        print("initUI called") 
        self.setWindowTitle(self.title)
        #layout = QGridLayout()
        #self.setLayout(layout)

            # Create a vertical box layout and add it to the window
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        # Create a combo box for group selection
        self.comboBox = QComboBox(self)
        self.comboBox.addItems(self.groups.keys())
        self.comboBox.currentIndexChanged.connect(self.update_cameras)
        vbox.addWidget(self.comboBox)  # Add the combo box to the vertical box layout

        # Create a grid layout for the labels
        layout = QGridLayout()
        vbox.addLayout(layout)  # Add the grid layout to the vertical box layout

        # Create labels for displaying the video
        self.labels = [QLabel(self) for _ in range(6)]
        for i, label in enumerate(self.labels):
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Set size policy to expanding
            label.setScaledContents(True)  # Set scale contents to true

            label.mousePressEvent = self.get_label_click_handler(i)  # Add mouse click event handler
            layout.addWidget(label, i // 3, i % 3)  # Arrange labels in a 4x3 grid


        # Create and start video threads for each camera
        self.threads = [VideoThread(camera, label) for camera, label in zip(self.cameras, self.labels)]
        for thread in self.threads:
            thread.changePixmap.connect(thread.updatePixmap)
            thread.start()

        # Make the window full screen
        self.showFullScreen()     
        
    def get_label_click_handler(self, i):
        def handler(event):
            self.threads[i].stop()  # Stop the previous thread

            # Start a new high-resolution thread
            self.threads[i] = VideoThread(self.cameras[i], self.labels[i], high_res=True)
            self.threads[i].changePixmap.connect(self.threads[i].updatePixmap)
            self.threads[i].start()
            # Hide all labels
            for label in self.labels:
                label.hide()
            # Show only the clicked label
            self.labels[i].show()
            self.full_screen = False  # Set full screen flag to False
        return handler
    
    def update_cameras(self, index):
        group_name = self.comboBox.itemText(index)
        self.cameras = self.groups[group_name]
        # Stop the previous threads and start new ones with the selected group cameras 
        for thread in self.threads:
            thread.stop()

        self.threads = [VideoThread(camera, label, high_res=False) for camera, label in zip(self.cameras, self.labels)]

        for thread in self.threads:
            thread.changePixmap.connect(thread.updatePixmap)
            thread.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:  # If the 'Escape' key is pressed
            if not self.full_screen:  # If the application is not in full screen mode
                for thread in self.threads:
                    thread.stop()  # Stop the previous threads
                
                # Restart all threads with normal resolution
                self.threads = [VideoThread(camera, label, high_res=False) for camera, label in zip(self.cameras, self.labels)]

                for thread in self.threads:
                    thread.changePixmap.connect(thread.updatePixmap)
                    thread.start()
                # Show all labels
                for label in self.labels:
                    label.show()
                self.full_screen = True  # Set full screen flag to True

                # Show the combo box
                #self.comboBox.show()
        super().keyPressEvent(event)

       
if __name__ == '__main__':
    print("Starting Camera Program ...")
    app = QApplication(sys.argv)
    ex = App()

    # Get the screen size of the primary monitor
    screen = app.primaryScreen()
    size = screen.size()
    # Set the width and height of the application window to match the primary monitor
    ex.setFixedSize(size.width(), size.height())

    ex.show()
    sys.exit(app.exec_())
