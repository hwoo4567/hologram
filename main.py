from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
import sys
import cv2
import mediapipe as mp
import numpy as np
from picamera2 import Picamera2

import ui
import hand

import os
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")


# 기준 벡터 (0, 1) (y축 단위 벡터)
reference_vector = np.array([0, -1])
def calculate_angle(a):
    global reference_vector
    # 벡터 크기 (norm)
    norm_reference = np.linalg.norm(reference_vector)
    norm_a = np.linalg.norm(a)
    
    # 두 벡터의 내적
    dot_product = np.dot(reference_vector, a)
    
    # 각도 (라디안 단위)
    cos_theta = dot_product / (norm_reference * norm_a)
    theta_radians = np.arccos(cos_theta)
    
    # 외적을 사용하여 회전 방향을 확인
    cross_product = np.cross(reference_vector, a)
    
    # 시계방향(음수), 반시계방향(양수) 판별
    if cross_product > 0:
        angle_degrees = np.degrees(theta_radians)
    else:
        angle_degrees = 360 - np.degrees(theta_radians)
    
    if angle_degrees >= 4:
        reference_vector = a
    return angle_degrees


class WithCameraUI(ui.ImageRotationUI):
    def __init__(self, model, mp_draw, mp_hands):
        self.picam2 = Picamera2()
        camera_config = self.picam2.create_preview_configuration(main={"size": (640, 480)})
        self.picam2.configure(camera_config)
        self.picam2.start()

        self.model = model
        self.mp_draw = mp_draw
        self.mp_hands = mp_hands
        super().__init__()
     
    def update_images(self):
        super().update_images()
        
    def get_next_index(self) -> int:
        current_index = super().get_next_index()
        frame = self.picam2.capture_array()
        frame = np.ascontiguousarray(frame, dtype=np.uint8)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        recog = hand.HandRecog(self.model, self.mp_draw, self.mp_hands, frame_rgb)
        
        print("thumb and index finger are close:", recog.isPickingGesture())
        if not recog.isPickingGesture():
            return current_index

        # if doing picking gesture
        
        # wrist index: 0
        wrist_point = np.array([*recog.getPointFromIdx(0)])
        # middle mcp index: 9
        middle_mcp_point = np.array([*recog.getPointFromIdx(9)])
        
        hand_direction_vec = middle_mcp_point - wrist_point
        angle = calculate_angle(hand_direction_vec)
        print(angle)
        try:
            result_idx = int(angle // 4)
            return (current_index + result_idx) % self.max_image_index
        except ValueError:
            return current_index

    def closeEvent(self, e: QtGui.QCloseEvent):
        self.cap.release()
        super().closeEvent(e)


drawingModule = mp.solutions.drawing_utils
handsModule = mp.solutions.hands
with handsModule.Hands(
    static_image_mode=False,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4,
    max_num_hands=2
) as hands:
    app = QApplication(sys.argv)
    window = WithCameraUI(hands, drawingModule, handsModule)
    sys.exit(app.exec_())