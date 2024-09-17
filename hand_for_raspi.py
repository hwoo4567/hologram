from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from picamera2 import Picamera2
import sys
import cv2
import numpy as np
import mediapipe as mp
import typing

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
        """frame: image(MatLike) read from cap.read()"""
        
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
        
        self.hands: typing.NamedTuple = self.results.multi_hand_landmarks
        
    def handExists(self):
        if self.hands:
            return True
        return False

    def drawHandPoint(self):
        if self.hands:
            # 각 손에 대한 반복
            for handLms in self.hands:
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = self.frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)

                    # 지점마다 원을 그람
                    cv2.circle(self.frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                    
                # 점마다 라인을 연결
                mp_draw.draw_landmarks(self.frame, handLms, mp_hands.HAND_CONNECTIONS)

        return self.frame
    
    # finger_n: number of finger (thumb: 1, index: 2, middle: 3 ...)
    def isFingerClose(self, finger_n: int):
        if self.results.multi_hand_world_landmarks:
            # 여러 손이 인식되면 그 중 하나만
            handLms = self.results.multi_hand_world_landmarks[0]
            fingers = handLms.landmark  # index 0 - 20
            
            # n번째 손가락 끝의 번호 : n * 4
            tip_idx = finger_n * 4
            # 손가락 뼈 3개를 벡터로 나타냄
            bone1 = np.array([
                fingers[tip_idx - 2].x - fingers[tip_idx - 3].x,
                fingers[tip_idx - 2].y - fingers[tip_idx - 3].y
            ])
            bone2 = np.array([
                fingers[tip_idx - 1].x - fingers[tip_idx - 2].x,
                fingers[tip_idx - 1].y - fingers[tip_idx - 2].y
            ])
            bone3 = np.array([
                fingers[tip_idx].x - fingers[tip_idx - 1].x,
                fingers[tip_idx].y - fingers[tip_idx - 1].y
            ])
            d = np.linalg.norm(bone1 + bone2 + bone3)
            if d <= FINGER_CLOSE_THRESHOLD:
                return True
            else:
                return False

        return False
    
    def isAllClose(self):
        # 엄지 빼고 전부
        for i in (2, 3, 4, 5):
            if not self.isFingerClose(i):
                return False
        return True
    
    def isPickingGesture(self):
        if self.results.multi_hand_world_landmarks:
            # 여러 손이 인식되면 그 중 하나만
            handLms = self.results.multi_hand_world_landmarks[0]
            fingers = handLms.landmark  # index 0 - 20
            
            thumb_tip = np.array([fingers[4].x, fingers[4].y])
            index_tip = np.array([fingers[8].x, fingers[8].y])
            
            d = np.linalg.norm(thumb_tip - index_tip)
            if d <= PICKING_GESTURE_THRESHOLD:
                return True
            else:
                return False

        return False
    
    def getPointFromIdx(self, idx: int) -> tuple[float, float]:
        if self.hands:
            # 여러 손이 인식되면 그 중 하나만
            handLms = self.hands[0]
            fingers = handLms.landmark  # index 0 - 20
            point = fingers[idx]
            x, y = point.x, point.y
            
            return x, y
        
        # 손이 없으면 항상 중간점
        return 0.5, 0.5
        
    def getStandardPoint(self) -> tuple[float, float]:
        x, y = self.getPointFromIdx(9)  # 중지 손가락 관절 시작 부분
        
        if self.stabilizer is None:
            return x, y
        else:
            return self.stabilizer(x, y)

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

        recog = HandRecog(frame)
        print("thumb and index finger are close:", recog.isPickingGesture())
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
    closeHandModel()
    sys.exit(app.exec_())
