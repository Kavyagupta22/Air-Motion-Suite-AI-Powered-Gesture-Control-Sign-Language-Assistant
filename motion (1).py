import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import numpy as np
import screen_brightness_control as sbc
import pyautogui
import os
import time

# --- 1. Model Files Download Setup ---
hand_model_path = 'hand_landmarker.task'

if not os.path.exists(hand_model_path):
    print("Downloading hand_landmarker model file...")
    import urllib.request
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, hand_model_path)
    print("Hand model downloaded successfully!")

# --- 2. MediaPipe Hand Detector Setup ---
BaseOptions = mp.tasks.BaseOptions
VisionRunningMode = mp.tasks.vision.RunningMode

HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
hand_options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=hand_model_path),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=2,  # Dono haath detect karne ke liye
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6
)
hand_detector = HandLandmarker.create_from_options(hand_options)

# --- 3. Webcam Initialize ---
cap = cv2.VideoCapture(0)

bright_bar = 400
bright_per = 0

# Variables for tracking
last_screenshot_time = 0
prev_left_hand_y = 0

print("Camera starting... Press 'q' to exit.")

while cap.isOpened():
    success, img = cap.read()
    if not success:
        print("Camera frame not available.")
        break

    # Frame horizontally flip karein (mirror view)
    img = cv2.flip(img, 1)
    h, w, c = img.shape

    # OpenCV BGR to RGB conversion
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    # Hand detection result
    hand_detection_result = hand_detector.detect(mp_image)

    sign_meaning = "Waiting for Sign..."
    display_status = False
    left_hand_found = False

    if hand_detection_result.hand_landmarks:
        for hand_landmarks in hand_detection_result.hand_landmarks:
            
            # Wrist (landmark 0) ka x coordinate se check karenge ki haath left side hai ya right side
            wrist_x = hand_landmarks[0].x * w

            # --- COUNT EXTENDED FINGERS & FINGER STATES ---
            tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
            pips = [3, 6, 10, 14, 18] # Respective joints
            
            extended = []
            # Thumb check (X-axis)
            if hand_landmarks[4].x > hand_landmarks[3].x:
                extended.append(1)
            else:
                extended.append(0)
                
            # Baaki 4 fingers check (Y-axis)
            extended_count = 0
            for i in range(1, 5):
                if hand_landmarks[tips[i]].y < hand_landmarks[pips[i]].y:
                    extended.append(1)
                    extended_count += 1
                else:
                    extended.append(0)

            # ==========================================
            # 1. RIGHT SIDE HAND -> BRIGHTNESS & SIGN LANGUAGE
            # ==========================================
            if wrist_x > w / 2:  # Screen ke right half me haath hone par
                
                # A. Brightness Control (Thumb Tip #4 & Index Tip #8)
                x1, y1 = int(hand_landmarks[4].x * w), int(hand_landmarks[4].y * h)
                x2, y2 = int(hand_landmarks[8].x * w), int(hand_landmarks[8].y * h)

                cv2.circle(img, (x1, y1), 8, (255, 0, 0), cv2.FILLED)
                cv2.circle(img, (x2, y2), 8, (255, 0, 0), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)

                length = math.hypot(x2 - x1, y2 - y1)

                bright_level = np.interp(length, [25, 250], [0, 100])
                bright_bar = np.interp(length, [25, 250], [400, 150])
                bright_per = np.interp(length, [25, 250], [0, 100])

                bright_level = max(0, min(100, bright_level))
                bright_per = max(0, min(100, bright_per))

                try:
                    sbc.set_brightness(int(bright_level))
                except Exception as e:
                    pass

                # B. Sign Language Recognition (For Deaf-Mute / Communication)
                if extended == [1, 0, 0, 0, 0] and hand_landmarks[4].y < hand_landmarks[3].y:
                    sign_meaning = "YES / GOOD"
                    display_status = True
                elif extended == [1, 1, 1, 1, 1]:
                    sign_meaning = "HELLO / STOP"
                    display_status = True
                elif extended == [0, 0, 0, 0, 0]:
                    sign_meaning = "READY / STRONG"
                    display_status = True
                elif extended == [0, 1, 1, 0, 0]:
                    sign_meaning = "PEACE / VICTORY"
                    display_status = True
                elif extended == [0, 1, 0, 0, 0]:
                    sign_meaning = "ATTENTION"
                    display_status = True

            # ==========================================
            # 2. LEFT SIDE HAND -> TOP-TO-BOTTOM SCREENSHOT
            # ==========================================
            elif wrist_x <= w / 2:  # Screen ke left half me haath hone par
                left_hand_found = True
                current_wrist_y = hand_landmarks[0].y

                # Agar 4 ya zyada ungliyan khuli hain aur haath ko upar se neeche laya gaya hai
                if extended_count >= 3 and prev_left_hand_y != 0:
                    movement_delta = current_wrist_y - prev_left_hand_y
                    
                    if movement_delta > 0.03:  # Downwards movement threshold
                        current_time = time.time()
                        if current_time - last_screenshot_time > 2.0:
                            screenshot = pyautogui.screenshot()
                            timestamp = int(time.time())
                            filename = f"screenshot_{timestamp}.png"
                            screenshot.save(filename)
                            print(f"Screenshot saved as {filename}")
                            last_screenshot_time = current_time

                prev_left_hand_y = current_wrist_y

    if not left_hand_found:
        prev_left_hand_y = 0


    # Screen par "SCREENSHOT TAKEN!" flash karne ke liye logic
    if time.time() - last_screenshot_time < 1.5:
        cv2.putText(img, "SCREENSHOT TAKEN!", (int(w/2) - 180, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)

    # --- 4. UI RENDERING ---
    # Brightness Bar UI (Left side of screen)
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
    cv2.rectangle(img, (50, int(bright_bar)), (85, 400), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, f'{int(bright_per)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 3)

    # Top Right Corner Sign Language / Gesture Display Box
    cv2.rectangle(img, (w - 280, 10), (w - 10, 80), (50, 50, 50), cv2.FILLED)
    cv2.rectangle(img, (w - 280, 10), (w - 10, 80), (0, 255, 0), 2)
    
    cv2.putText(img, "Sign Meaning:", (w - 270, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(img, f"{sign_meaning}", (w - 270, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Gesture Brightness, Screenshot & Sign Translator", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

