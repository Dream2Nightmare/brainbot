# G:\brainbot\core\senses\senses.py

from pathlib import Path
from datetime import datetime

from .video.video_sense import (
    record_screen,
    capture_webcam_image,
    capture_webcam_video
)
from .audio.audio_sense import listen_and_transcribe

class SensesController:
    def __init__(self, base_path, memory=None, log_function=None, chat_function=None):
        self.base_path = Path(base_path)
        self.memory = memory
        self.log = log_function or (lambda msg: print(msg))
        self.chat = chat_function

    def _store(self, modality, data):
        if not data or not isinstance(data, dict):
            self.log(f"⚠️ Invalid data for modality: {modality}")
            return None

        packet = {
            "timestamp": datetime.utcnow().isoformat(),
            "modality": modality,
            "data": data
        }

        if self.memory:
            try:
                self.memory.store_reflection(
                    role=modality,
                    content=data.get("text", str(data)),
                    glyph=self._glyph_for(modality),
                    thoughts=f"Sensed {modality} input",
                    source_type=modality
                )
            except Exception as e:
                self.log(f"⚠️ Failed to store reflection: {e}")

        return packet

    def _glyph_for(self, modality):
        return {
            "audio": "🎙️",
            "camera_image": "📸",
            "camera_video": "🎥",
            "screen": "🖥️",
            "text": "📝"
        }.get(modality, "🔍")

    def sense_screen(self, ocr=True):
        self.log("🖥️ Sensing screen...")
        result = record_screen(ocr=ocr)
        return self._store("screen", result)

    def sense_camera_image(self, save_path=None):
        self.log("📸 Sensing webcam image...")
        result = capture_webcam_image(save_path=save_path)
        return self._store("camera_image", result)

    def sense_camera_video(self, duration=10, save_path=None):
        save_path = save_path or self.base_path / "memory" / "video"
        self.log(f"🎥 Sensing webcam video ({duration}s)...")
        result = capture_webcam_video(duration=duration, save_path=str(save_path))
        return self._store("camera_video", result)

    def sense_audio(self, timeout=5, phrase_time_limit=10):
        self.log("🎙️ Sensing audio...")
        try:
            result = listen_and_transcribe(timeout=timeout, phrase_time_limit=phrase_time_limit)
            return self._store("audio", result)
        except Exception as e:
            self.log(f"⚠️ Audio sensing failed: {e}")
            return None

    def interpret(self, source="text", content=None):
        if source == "audio":
            result = self.sense_audio()
            return result.get("data", {}).get("text", "") if result else ""

        elif source == "video":
            result = self.sense_screen()
            return result.get("data", {}).get("text", "") if result else ""

        elif source == "text" and content:
            packet = {
                "timestamp": datetime.utcnow().isoformat(),
                "modality": "text",
                "data": {"text": content}
            }
            if self.memory:
                self.memory.store_reflection(
                    role="text",
                    content=content,
                    glyph="📝",
                    thoughts="Text interpretation",
                    source_type="text"
                )
            return content

        else:
            self.log("⚠️ Unknown input source or missing content.")
            return ""
