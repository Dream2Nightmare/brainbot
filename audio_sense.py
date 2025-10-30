# G:\brainbot\core\senses\audio\audio_sense.py

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import speech_recognition as sr
from datetime import datetime

def listen_and_transcribe(timeout=5, phrase_time_limit=10):
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print("🎙️ Listening...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        transcript = recognizer.recognize_google(audio)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "timestamp": timestamp,
            "text": transcript.strip()
        }

    except sr.WaitTimeoutError:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "text": "(No speech detected — silence)"
        }

    except sr.UnknownValueError:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "text": "(Speech unintelligible)"
        }

    except sr.RequestError as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "text": f"(Recognition error: {e})"
        }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "text": f"(Unexpected error: {e})"
        }
