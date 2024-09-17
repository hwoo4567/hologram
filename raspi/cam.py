from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from picamera2 import Picamera2
import sys

class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set the window title and size
        self.setWindowTitle("PiCamera2 Image in QMainWindow")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the camera
        self.picam2 = Picamera2()

        # Configure the camera for still image capture
        camera_config = self.picam2.create_still_configuration()
        self.picam2.configure(camera_config)

        # Start the camera
        self.picam2.start()

        # Capture an image
        image = self.picam2.capture_array()

        # Stop the camera (optional, can keep running if needed)
        self.picam2.stop()

        # Convert the image to QImage
        height, width, channels = image.shape
        bytes_per_line = channels * width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # Display the image using QLabel
        label = QLabel(self)
        pixmap = QPixmap.fromImage(qimage)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        # Resize the label to fit the window
        self.setCentralWidget(label)

# PyQt Application setup
app = QApplication(sys.argv)

# Create and display the camera window
window = CameraWindow()
window.show()

# Start the application's event loop
sys.exit(app.exec_())
