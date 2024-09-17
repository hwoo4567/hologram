import cv2
import numpy as np
import mediapipe as mp
import typing

FINGER_CLOSE_THRESHOLD = 0.06
PICKING_GESTURE_THRESHOLD = 0.03
STABLE_RADIUS = 0.01

mp_draw = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

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
    def __init__(self, model, frame, stabilization=False):
        """frame: image(MatLike) read from cap.read()"""
        
        self.frame = frame
        
        if stabilization:
            self.stabilizer = Stabilizer.get()
        else:
            self.stabilizer = None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if rgb_frame is not None:
            self.results = model.process(rgb_frame)
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
                print(self.frame.shape)
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


if __name__ == "__main__":
    drawingModule = mp.solutions.drawing_utils
    handsModule = mp.solutions.hands

    with handsModule.Hands(
        static_image_mode=False,
        min_detection_confidence=0.4,
        min_tracking_confidence=0.4,
        max_num_hands=2
    ) as hands:
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            recog = HandRecog(hands, frame)
            print("thumb and index finger are close:", recog.isPickingGesture())
            frame = recog.drawHandPoint()
            
            cv2.imshow('Hand Tracking', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()