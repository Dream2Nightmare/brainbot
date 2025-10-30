#G:\brainbot\desktop.py
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QLineEdit, QLabel
from PyQt5.QtGui import QPixmap

from core.tools.tools import ToolsController
from core.brainbot import BrainBot

BASE_PATH = Path("G:/brainbot/core")

class DesktopInterface(QWidget):
    def __init__(self):
        super().__init__()
        print("🧠 Initializing DesktopInterface with Tools + BrainBot...")
        self.setWindowTitle("BrainBot Interface")
        self.setGeometry(100, 100, 800, 600)

        # Background
        self.bg_label = QLabel(self)
        bg_path = "G:/brainbot/gui/background.png"
        pixmap = QPixmap(bg_path)
        if not pixmap.isNull():
            self.bg_label.setPixmap(pixmap)
            self.bg_label.setScaledContents(True)
            self.bg_label.lower()
        else:
            print("⚠️ Failed to load background image.")

        # Chat window
        self.chat_window = QTextEdit(self)
        self.chat_window.setReadOnly(True)
        self.chat_window.setGeometry(78, 90, 650, 350)
        self.chat_window.setStyleSheet("""
            background-color: rgba(0, 0, 0, 160); 
            color: white; 
            font-size: 14px;
            border-radius: 10px;
            padding: 8px;
        """)

        # Log window
        self.log_window = QTextEdit(self)
        self.log_window.setReadOnly(True)
        self.log_window.setGeometry(458, 100, 275, 200)
        self.log_window.setStyleSheet("""
            background-color: rgba(0, 0, 0, 140); 
            color: orange; 
            font-size: 12px;
            border-radius: 10px;
            padding: 6px;
        """)

        # Input field
        self.input_field = QLineEdit(self)
        self.input_field.setGeometry(78, 450, 650, 60)
        self.input_field.setStyleSheet("""
            background-color: rgba(0, 0, 0, 200);
            color: cyan;
            font-size: 14px;
            border-radius: 8px;
            padding: 6px;
        """)
        self.input_field.returnPressed.connect(self.handle_input)

        # Initialize modules
        self.tools = ToolsController(base_path=str(BASE_PATH), log_function=self.log)
        self.brain = BrainBot(base_path=str(BASE_PATH), log=self.log, chat=self.chat, tools=self.tools)
        # self.senses = SensesController(base_path=str(BASE_PATH), memory=self.brain, log_function=self.log, chat_function=self.chat)
        # self.brain.senses = self.senses
        self.bot_loaded = False

        print("✅ DesktopInterface initialized with Tools + BrainBot.")
    def log(self, message):
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        QTimer.singleShot(0, lambda: self.log_window.append(formatted))

    def chat(self, message):
        QTimer.singleShot(0, lambda: self.chat_window.append(f"<b>BrainBot:</b> {message}"))

    def handle_input(self):
        text = self.input_field.text().strip()
        self.input_field.clear()
        if not text:
            return
        self.chat_window.append(f"<span style='color: lightgreen'><b>You:</b> {text}</span>")
        self.log(f"User input received: {text}")

        if text.lower() == "/load bot":
            if self.bot_loaded:
                self.chat("⚠️ BrainBot is already loaded.")
            else:
                self.chat("🧠 Summoning BrainBot...")
                self.brain.startup(scan_on_load=True, enable_craving=False)
                self.chat("👋 Hello, I am awake. Scanning for unreflected files...")
                self.bot_loaded = True

        elif text.lower() == "/status":
            status_lines = self.brain.get_status()
            status_html = "<br>".join(status_lines)
            self.chat_window.append(f"<b>📊 BrainBot Status:</b><br>{status_html}")

        elif text.startswith("/dream"):
            self.brain.dream()
            self.chat("🌌 Dream ritual complete. Reflections moved to long-term.")

        elif text.startswith("/forge"):
            parts = text.split(" ", 1)[-1].split(":", 1)
            if len(parts) == 2:
                name, purpose = parts
                from core.tools.pythonforge.forge import generate_function
                success = generate_function(name.strip(), purpose.strip())
                self.chat("🛠️ Forge complete." if success else "⚠️ Forge failed.")
            else:
                self.chat("⚠️ Use format: /forge name:purpose")

        elif text.startswith("/tools"):
            title = self.tools.run_seeker()
            self.chat_window.append(f"<b>🧰 Tools:</b> {title or '(No title returned)'}")

        elif text.startswith("/mine"):
            wallet = text.split(" ", 1)[-1].strip()
            self.tools.mining.start_mining(wallet_address=wallet)
            self.chat(f"⛏️ Mining started for wallet: {wallet}")

        elif text.lower() == "/scansystem":
            self.chat("🔍 Beginning full system scan...")
            threading.Thread(target=self.run_full_scan, daemon=True).start()

        elif text.lower() == "/sensescreen":
            if hasattr(self, "senses"):
                result = self.senses.sense_screen()
                text = result.get("data", {}).get("text", "")
                self.chat(f"🖥️ Screen OCR: {text}")
            else:
                self.chat("⚠️ Senses module is not enabled.")

        elif text.lower() == "/train":
            QTimer.singleShot(0, lambda: self.chat("🔥 Beginning training ritual from /core/training/ ..."))
            def train_and_dream():
                self.brain.train_on_pairs_in_folder()
                # Optional: uncomment to auto-dream after training
                # self.brain.dream()
                # self.chat("🌌 Training complete. Dream ritual moved reflections to long-term.")
            threading.Thread(target=train_and_dream, daemon=True).start()

        elif text.lower() == "/trainstatus":
            count = len(list(self.brain.short_term_dir.glob("reflection_*.json")))
            self.chat(f"🔥 Training reflections stored: {count}")

        elif text.startswith("/"):
            self.chat(f"⚠️ Unknown command: {text}")

        else:
            response = self.brain.respond(text)
            self.chat(response)
    def run_full_scan(self):
        for path in self.brain.scan_files(["C:/", "G:/"]):
            if self.brain.is_seen(path):
                continue
            self.brain.reflect_file(path)
            time.sleep(0.2)
        self.brain._save_seen_paths()
        self.chat("✅ System scan complete. Reflections stored.")

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        super().resizeEvent(event)

if __name__ == "__main__":
    print("🚀 Launching Tools + BrainBot...")
    app = QApplication(sys.argv)
    interface = DesktopInterface()
    interface.show()
    print("🎬 Interface should now be visible.")
    sys.exit(app.exec_())
