"""
sudo apt update
sudo apt install python3-picamera2 python3-pyqt5 libcamera-dev
"""

from PyQt5.QtWidgets import QApplication
from picamera2 import Picamera2, Preview

# Create a Qt application instance
app = QApplication([])

# Create an instance of Picamera2
picam2 = Picamera2()

# Configure the camera for preview (real-time video)
picam2.configure(picam2.create_preview_configuration())

# Create a preview window (Qt-based)
picam2.start_preview(Preview.QTGL)

# Start the camera
picam2.start()

# Run the Qt event loop
app.exec_()

# Stop the camera when done
picam2.stop()
