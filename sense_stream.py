#G:\Reflection\core\senses\sense_stream.py
import threading
import time
import os
from pathlib import Path

from senses.senses import SensesController

class SenseStream:
    def __init__(self, base_path, memory=None, log_function=None):
        self._running = False

def start_sensory_stream(base_path, logic, memory=None, log=None, interval=30):
    controller = SenseStream(base_path=base_path, memory=memory, log_function=log)
    senses = SensesController(base_path=base_path, memory=memory, log_function=log)
    video_path = Path(base_path) / "memory" / "video"
    video_path.mkdir(parents=True, exist_ok=True)

    def stream():
        if log: log("🌌 Sensory stream initiated...")
        controller._running = True
        while controller._running:
            try:
                senses.sense_screen()
                senses.sense_camera_image(save_path=video_path)
                senses.sense_camera_video(duration=10, save_path=video_path)
                senses.sense_audio()
                logic.scan_and_analyze()
                cleanup_raw_media(video_path, log=log)
                time.sleep(interval)
            except Exception as e:
                if log: log(f"❌ Sensory stream error: {e}")
                time.sleep(interval)

    threading.Thread(target=stream, daemon=True).start()
    return controller

def cleanup_raw_media(folder, log=None):
    if log: log("🧹 Cleaning up raw media files...")
    try:
        for filename in os.listdir(folder):
            if filename.lower().endswith((".avi", ".wav", ".mp3", ".mp4", ".png", ".jpg", ".jpeg", ".bmp")):
                path = os.path.join(folder, filename)
                os.remove(path)
                if log: log(f"🗑️ Deleted: {filename}")
    except Exception as e:
        if log: log(f"❌ Cleanup failed: {e}")
