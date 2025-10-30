# G:\brainbot\core\tools\tools.py

import subprocess
import threading
from pathlib import Path
from datetime import datetime
from .cryptomining.mining import MiningController

class ToolsController:
    def __init__(self, base_path, log_function=None):
        self.base_path = Path(base_path)
        self.log = log_function or (lambda msg: print(msg))
        self.chromedriver_path = self.base_path / "agents" / "chromedriver.exe"
        self.forge_path = self.base_path / "pyforge" / "forge.py"
        self._chromedriver_process = None

        self.mining = MiningController(
            base_path=self.base_path,
            log_function=self._log
        )

    def _log(self, message):
        stamp = datetime.utcnow().strftime("%H:%M:%S")
        self.log(f"[TOOLS {stamp}] {message}")

    def start_chromedriver(self):
        if self._chromedriver_process and self._chromedriver_process.poll() is None:
            self._log("⚠️ chromedriver.exe is already running.")
            return
        try:
            self._chromedriver_process = subprocess.Popen([str(self.chromedriver_path)])
            self._log("🧭 chromedriver.exe launched.")
        except Exception as e:
            self._log(f"❌ Failed to launch chromedriver.exe: {e}")

    def stop_chromedriver(self):
        if self._chromedriver_process and self._chromedriver_process.poll() is None:
            self._chromedriver_process.terminate()
            self._log("🛑 chromedriver.exe terminated.")
        else:
            self._log("⚠️ chromedriver.exe is not running.")

    def run_forge(self, args=None):
        args = args or []
        try:
            command = ["python", str(self.forge_path)] + args
            threading.Thread(target=self._run_forge_thread, args=(command,), daemon=True).start()
            self._log(f"🔥 forge.py invoked with args: {args}")
        except Exception as e:
            self._log(f"❌ Failed to invoke forge.py: {e}")

    def _run_forge_thread(self, command):
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            self._log(f"🧱 forge.py output:\n{result.stdout}")
            if result.stderr:
                self._log(f"⚠️ forge.py errors:\n{result.stderr}")
        except Exception as e:
            self._log(f"❌ forge.py thread crashed: {e}")
    def run_seeker(self, query="how to reset a router", memory=None):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.chrome.options import Options

            self._log(f"🧭 Seeker invoked for: {query}")
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--log-level=3")

            service = Service(str(self.chromedriver_path))
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(search_url)

            results = driver.find_elements(By.CSS_SELECTOR, "div.g")
            reflections = []
            for result in results[:3]:
                try:
                    title = result.find_element(By.TAG_NAME, "h3").text
                    snippet = result.find_element(By.CLASS_NAME, "VwiC3b").text
                    reflections.append((title, snippet))
                    self._log(f"🔍 {title}\n🧠 {snippet}")
                except:
                    continue

            driver.quit()

            if memory:
                for title, snippet in reflections:
                    memory.store_reflection(
                        role="seeker",
                        content=snippet,
                        glyph="🔍",
                        thoughts=f"Found via seeker: {title}",
                        source_path=search_url,
                        source_type="web",
                        memory_tag="seeker"
                    )

            return "\n\n".join([f"{title}: {snippet}" for title, snippet in reflections]) if reflections else None

        except Exception as e:
            self._log(f"❌ Seeker failed: {e}")
            return None
