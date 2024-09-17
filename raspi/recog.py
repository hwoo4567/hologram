# Import the necessary Packages for this software to run
import mediapipe as mp
from picamera2 import Picamera2
import cv2
import numpy as np

# Use MediaPipe to draw the hand framework over the top of hands it identifies in Real-Time
drawingModule = mp.solutions.drawing_utils
handsModule = mp.solutions.hands

# Initialize the Picamera2 object
picam2 = Picamera2()

# Configure the camera settings
camera_config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(camera_config)

# Start the camera
picam2.start()

with handsModule.Hands(
    static_image_mode=False,
    min_detection_confidence=0.4,
    min_tracking_confidence=0.4,
    max_num_hands=2
) as hands:
    while True:
        # Capture the frame
        frame = picam2.capture_array()
        frame = np.ascontiguousarray(frame, dtype=np.uint8)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame to detect hands
        results = hands.process(frame_rgb)

        # Check if hands are detected and draw landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                drawingModule.draw_landmarks(frame_rgb, hand_landmarks, handsModule.HAND_CONNECTIONS)

        # Display the frame with hand landmarks
        cv2.imshow("Frame", frame_rgb)

        # Exit the loop if 'q' is pressed
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

# Release the camera resources
picam2.stop()
cv2.destroyAllWindows()
