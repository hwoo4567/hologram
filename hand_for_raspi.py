from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from picamera2 import Picamera2
import sys
import numpy as np
import mediapipe as mp

FINGER_CLOSE_THRESHOLD = 0.06
PICKING_GESTURE_THRESHOLD = 0.03
STABLE_RADIUS = 0.01

mp_draw = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

class Stabilizer:
    singleton = None
    
    def __init__(self) -> None:
        self.prev_vec = None
    
    @classmethod
    def get(cls):
        if cls.singleton is None:
            cls.singleton = Stabilizer()
            return cls.singleton
        else:
            return cls.singleton
        
    def __call__(self, x, y) -> tuple[float, float]:
        vec = np.array([x, y])
        if self.prev_vec is None:
            self.prev_vec = vec
            return x, y

        # stabilization
        diff = np.linalg.norm(self.prev_vec - vec)
        if diff < STABLE_RADIUS:
            return self.prev_vec[0], self.prev_vec[1]
        else:
            self.prev_vec = vec
            return x, y
        
class HandRecog:
    def __init__(self, frame, stabilization=False):
        """frame: image(MatLike) read from picamera2"""
        self.frame = frame
        
        if stabilization:
            self.stabilizer = Stabilizer.get()
        else:
            self.stabilizer = None
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if rgb_frame is not None:
            self.results = hands.process(rgb_frame)
        else:
            raise TypeError("카메라가 존재하지 않습니다.")
        
        self.hands = self.results.multi_hand_landmarks
        
    def handExists(self):
        return bool(self.hands)

    def drawHandPoint(self):
        if self.hands:
            for handLms in self.hands:
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = self.frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(self.frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                    
                mp_draw.draw_landmarks(self.frame, handLms, mp_hands.HAND_CONNECTIONS)

        return self.frame

    def isPickingGesture(self):
        if self.results.multi_hand_world_landmarks:
            handLms = self.results.multi_hand_world_landmarks[0]
            fingers = handLms.landmark  
            
            thumb_tip = np.array([fingers[4].x, fingers[4].y])
            index_tip = np.array([fingers[8].x, fingers[8].y])
            
            d = np.linalg.norm(thumb_tip - index_tip)
            return d <= PICKING_GESTURE_THRESHOLD

        return False
    
    def getStandardPoint(self):
        x, y = self.getPointFromIdx(9)
        return self.stabilizer(x, y) if self.stabilizer else (x, y)

    def getPointFromIdx(self, idx):
        if self.hands:
            handLms = self.hands[0]
            fingers = handLms.landmark  
            point = fingers[idx]
            return point.x, point.y
        return 0.5, 0.5  # Default center if no hand

def closeHandModel():
    hands.close()

class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Get the screen size
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        self.screen_width = screen_size.width()
        self.screen_height = screen_size.height()

        # Set the window to match the screen size
        self.setWindowTitle("Real-Time Camera Feed")
        self.setGeometry(0, 0, self.screen_width, self.screen_height)

        # Initialize the camera
        self.picam2 = Picamera2()

        # Configure the camera for preview mode (lower latency)
        camera_config = self.picam2.create_preview_configuration()
        self.picam2.configure(camera_config)

        # Start the camera
        self.picam2.start()

        # QLabel to display the camera feed
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)

        # Enable scaling of the QLabel contents
        self.label.setScaledContents(True)

        # Setup a timer to update the camera feed
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 ms (approx 33 FPS)

    def update_frame(self):
        # Capture a frame as a NumPy array
        frame = self.picam2.capture_array()

        # Pass the frame to HandRecog for hand tracking
        recog = HandRecog(frame)
        print("thumb and index finger are close:", recog.isPickingGesture())

        # Draw hand points on the frame
        frame = recog.drawHandPoint()

        # Convert the frame to QImage
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # Scale the image to fit the screen size
        scaled_qimage = qimage.scaled(self.screen_width, self.screen_height, Qt.KeepAspectRatio)

        # Update the QLabel with the new scaled QPixmap
        pixmap = QPixmap.fromImage(scaled_qimage)
        self.label.setPixmap(pixmap)

if __name__ == "__main__":
    # PyQt Application setup
    app = QApplication(sys.argv)

    # Create and display the camera window
    window = CameraWindow()
    window.showFullScreen()  # Set the window to full screen

    # Start the application's event loop
    sys.exit(app.exec_())
