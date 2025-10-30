# G:\brainbot\core\senses\video\video_sense.py

import pyautogui
import pytesseract
from PIL import Image
from datetime import datetime
import cv2
import numpy as np
import os

def record_screen(ocr=True):
    try:
        screenshot = pyautogui.screenshot()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        if ocr:
            text = pytesseract.image_to_string(screenshot)
            return {
                "timestamp": timestamp,
                "mode": "screen + OCR",
                "text": text.strip() or "(No text detected)"
            }
        else:
            return {
                "timestamp": timestamp,
                "mode": "screen only",
                "text": "(OCR disabled)"
            }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "error",
            "text": f"⚠️ Screen capture failed: {e}"
        }

def motion_detected(threshold=50000):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False

    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    cap.release()

    if not ret:
        return False

    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    motion_score = np.sum(thresh)

    return motion_score > threshold

def capture_webcam_image(save_path=None):
    if not motion_detected():
        return {"status": "skipped", "message": "🧘 No motion detected. Image capture skipped."}

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"status": "error", "message": "⚠️ Webcam not accessible."}

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"status": "error", "message": "⚠️ Failed to capture image from webcam."}

        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"webcam_{timestamp}.png"
        if save_path and not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename) if save_path else filename

        if save_path:
            cv2.imwrite(full_path, frame)
            return {"status": "success", "path": full_path, "timestamp": timestamp}
        else:
            return {"status": "success", "image": frame, "timestamp": timestamp}

    except Exception as e:
        return {"status": "error", "message": f"⚠️ Webcam capture failed: {e}"}

def capture_webcam_video(duration=10, save_path="G:\\Dream\\Core\\memory\\video"):
    if not motion_detected():
        return {"status": "skipped", "message": "🧘 No motion detected. Video capture skipped."}

    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return {"status": "error", "message": "⚠️ Webcam not accessible."}

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = 20
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"webcam_{timestamp}.avi"
        if save_path and not os.path.exists(save_path):
            os.makedirs(save_path, exist_ok=True)
        full_path = os.path.join(save_path, filename)

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(full_path, fourcc, fps, (width, height))

        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < duration:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        cap.release()
        out.release()

        return {
            "status": "success",
            "path": full_path,
            "duration": duration,
            "timestamp": timestamp
        }

    except Exception as e:
        return {"status": "error", "message": f"⚠️ Video capture failed: {e}"}
