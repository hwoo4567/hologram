import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt, QTimer
import os

class ImageRotationUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Image Rotation UI')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black;")
        
        # 키보드 상태
        self.key_left = False
        self.key_right = False

        # 이미지 경로 설정 (여러 개의 이미지 사용)
        path = "./render/model_1"
        self.image_paths = [os.path.join(path, i) for i in os.listdir(path)]
        self.max_image_index = len(self.image_paths)  # 90개의 이미지를 사용할 예정
        self.current_image_index = 0

        # 이미지 크기 설정 (최대 100x100)
        self.max_size = (500, 500)
        
        # 여백 설정
        self.margin = 20

        # 이미지 라벨 초기화
        self.top_image = QLabel(self)
        self.bottom_image = QLabel(self)
        self.left_image = QLabel(self)
        self.right_image = QLabel(self)

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_images)
        self.timer.start(100)  # 100ms = 0.1초

        self.update_images()

        self.show()
        
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Left:
            self.key_left = True
        if e.key() == Qt.Key.Key_Right:
            self.key_right = True

    def keyReleaseEvent(self,e):
        if e.key() == Qt.Key.Key_Left:
            self.key_left = False
        if e.key() == Qt.Key.Key_Right:
            self.key_right = False
    
    ##############################################################################
    def get_next_index(self) -> int:
        if self.key_left and not self.key_right:
            return (self.current_image_index - 1) % self.max_image_index
        if not self.key_left and self.key_right:
            return (self.current_image_index + 1) % self.max_image_index
        
        return self.current_image_index
    
    ##############################################################################

    def update_images(self):
        # 다음 이미지로 인덱스 증가
        self.current_image_index = self.get_next_index()
        
        # 이미지 로드
        current_image_path = self.image_paths[self.current_image_index]
        original_pixmap = QPixmap(current_image_path)

        # 이미지를 중앙을 향하도록 회전 및 크기 조정 후 배치

        # 상단 이미지
        top_pixmap = original_pixmap.transformed(QTransform().rotate(180))
        top_pixmap = top_pixmap.scaled(self.max_size[0], self.max_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.top_image.setPixmap(top_pixmap)
        self.top_image.setGeometry((800 - top_pixmap.width()) // 2, self.margin, top_pixmap.width(), top_pixmap.height())

        # 하단 이미지
        bottom_pixmap = original_pixmap.transformed(QTransform().rotate(0))
        bottom_pixmap = bottom_pixmap.scaled(self.max_size[0], self.max_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.bottom_image.setPixmap(bottom_pixmap)
        self.bottom_image.setGeometry((800 - bottom_pixmap.width()) // 2, 600 - bottom_pixmap.height() - self.margin, bottom_pixmap.width(), bottom_pixmap.height())

        # 좌측 이미지
        left_pixmap = original_pixmap.transformed(QTransform().rotate(90))
        left_pixmap = left_pixmap.scaled(self.max_size[0], self.max_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.left_image.setPixmap(left_pixmap)
        self.left_image.setGeometry(self.margin, (600 - left_pixmap.height()) // 2, left_pixmap.width(), left_pixmap.height())

        # 우측 이미지
        right_pixmap = original_pixmap.transformed(QTransform().rotate(-90))
        right_pixmap = right_pixmap.scaled(self.max_size[0], self.max_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.right_image.setPixmap(right_pixmap)
        self.right_image.setGeometry(800 - right_pixmap.width() - self.margin, (600 - right_pixmap.height()) // 2, right_pixmap.width(), right_pixmap.height())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageRotationUI()
    sys.exit(app.exec_())
