import sys
import numpy as np
import cv2
print("platform:", sys.platform)

total_cam_open = False

if sys.platform != "win32":
    from picamera2 import Picamera2

def newCamera():
    global total_cam_open
    total_cam_open = True

    if sys.platform == "win32":
        cap = cv2.VideoCapture(0)
        return cap
    else:
        picam2 = Picamera2()
        camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
        picam2.configure(camera_config)
        picam2.start()
        return picam2

# it returns rgb frame
def getFrame(camera):
    if not total_cam_open:
        return np.zeros([100, 100, 3], dtype=np.uint8)
    
    if sys.platform == "win32":
        if not camera.isOpened():
            raise RuntimeError("windows: camera is not open.")
        ret, frame = camera.read()
        if not ret:
            raise RuntimeError("windows: rat is false.")
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame_rgb
    else:
        frame = picam2.capture_array()
        frame = np.ascontiguousarray(frame, dtype=np.uint8)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame_rgb

def closeCamera(camera):
    global total_cam_open
    total_cam_open = False

    if sys.platform == "win32":
        camera.release()
    else:
        camera.stop()