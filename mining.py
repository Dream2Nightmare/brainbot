# G:\brainbot\core\tools\cryptomining\mining.py

import subprocess
from datetime import datetime
from pathlib import Path

class MiningController:
    def __init__(self, base_path, log_function=None):
        self.base_path = Path(base_path)
        self.log = log_function or (lambda msg: print(msg))
        self._mining_process = None
        self._running = False
        self.xmrig_path = self.base_path / "core" / "tools" / "cryptomining" / "xmrig" / "xmrig.exe"

    def _log(self, message):
        stamp = datetime.utcnow().strftime("%H:%M:%S")
        self.log(f"[MINING {stamp}] {message}")

    def start_mining(self, wallet_address, pool="pool.supportxmr.com:3333", extra_args=None):
        if self._mining_process and self._mining_process.poll() is None:
            self._log("⚠️ Mining process already running.")
            return
        args = [str(self.xmrig_path), "-o", pool, "-u", wallet_address, "-k", "--tls"]
        if extra_args:
            args.extend(extra_args)
        try:
            self._mining_process = subprocess.Popen(args)
            self._running = True
            self._log(f"⛏️ Mining ritual initiated for wallet: {wallet_address}")
        except Exception as e:
            self._log(f"❌ Failed to start miner: {e}")

    def stop_mining(self):
        if self._mining_process and self._mining_process.poll() is None:
            self._mining_process.terminate()
            self._running = False
            self._log("🛑 Mining ritual halted.")
        else:
            self._log("⚠️ No active mining process found.")

    def status(self):
        if self._mining_process and self._mining_process.poll() is None:
            return "⛏️ Mining is active."
        return "🛑 Mining is inactive."

    def check_health(self):
        if self._mining_process and self._mining_process.poll() is not None:
            self._log("⚠️ Mining process died unexpectedly.")
            self._running = False
