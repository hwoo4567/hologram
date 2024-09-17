from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from picamera2 import Picamera2
import sys

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

        # Convert the frame to QImage
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # Scale the image to fit the screen size
        scaled_qimage = qimage.scaled(self.screen_width, self.screen_height, Qt.KeepAspectRatio)

        # Update the QLabel with the new scaled QPixmap
        pixmap = QPixmap.fromImage(scaled_qimage)
        self.label.setPixmap(pixmap)

# PyQt Application setup
app = QApplication(sys.argv)

# Create and display the camera window
window = CameraWindow()
window.showFullScreen()  # Set the window to full screen

# Start the application's event loop
sys.exit(app.exec_())
