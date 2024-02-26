import os
gstreamer_path = "C:\\gstreamer\\1.0\\msvc_x86_64\\bin"
os.add_dll_directory(gstreamer_path)

import time
import cv2
import subprocess

def get_codec(camera):
    command = ["C:\\gstreamer\\1.0\\msvc_x86_64\\bin\\gst-launch-1.0.exe", "-v", "rtspsrc", "location="+camera, "!", "decodebin", "!", "fakesink", "silent=false", "-m"]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        # Wait for 5 seconds to get the output
        stdout, _ = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        # If the command does not end after 5 seconds, terminate it
        process.terminate()
        stdout, _ = process.communicate()

    output = stdout.decode()
    
    if 'H264' in output:
        print('Encoding H264')
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
               "rtph264depay ! h264parse ! decodebin ! "
               "videoconvert !  video/x-raw,format=BGR ! appsink drop=true")
    elif 'H265' in output:
        print('Encoding H265')
        gst_str = ("rtspsrc location=" + camera + " latency=0 ! "
               "rtph265depay ! h265parse ! decodebin ! "
               "videorate !  video/x-raw,framerate=24/1 !"
                "videoconvert ! appsink drop=true")
    else:
        raise RuntimeError('H.264 or H.265 decoder not found!')
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

#camera = r"rtsp://admin:Cwds11354@6d5f3a5def2ee7b027cd918692a99c7d.21.camera.verkada-lan.com:8554/standard"
#camera = r"rtsp://admin:Cwds11354@192.168.4.3:554/Streaming/channels/101"

camera = r"rtsp://admin:admin12345@12.131.44.139:10802/Streaming/channels/101"

# Determine the codec of the stream and stream it
cap = get_codec(camera)

# 1920x1080 full screen
cv2.namedWindow('Crystal Cameras', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Crystal Cameras', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

start_time = time.time()
num_frame = 1000

# Read until video is completed
#while cap.isOpened():
for _ in range(num_frame):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Display the resulting frame
    cv2.imshow('Crystal Cameras', frame)
    cv2.resizeWindow('Crystal Cameras', 1920, 1080)


    # Break the loop and switch camera after 30 seconds total
    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

# When everything is done, release the video capture and video write objects and get fps
end_time = time.time()
fps = num_frame / (end_time - start_time)
print('FPS:', fps)
cap.release()
cv2.destroyAllWindows()
            