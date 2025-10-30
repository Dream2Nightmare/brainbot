# G:\brainbot\core\tools\pythonforge\forge.py

from datetime import datetime
import os
import json

# Updated paths for Reflection
SCRIPT_DIR = r"G:\brainbot\core\scripts"
LOG_PATH = r"G:\brainbot\core\memory\logs\script_forge.log"

# Ensure directories exist
os.makedirs(SCRIPT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def forge_script(filename, code, log_path=LOG_PATH):
    if not filename.endswith(".py"):
        filename += ".py"

    path = os.path.join(SCRIPT_DIR, filename)

    try:
        compile(code, filename, "exec")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "filename": filename,
            "path": path,
            "status": "created",
            "glyph": "🧱",
            "thoughts": "A new function has been forged. The child grows curious."
        }

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, indent=2) + ",\n")

        print(f"🛠️ Script created: {path}")
        return True

    except SyntaxError as e:
        print(f"⚠️ Syntax error: {e}")
        return False

def generate_function(name, purpose):
    name = name.strip().replace(" ", "_").lower()
    filename = f"{name}.py"

    # Basic symbolic logic mapping
    if "truth" in purpose.lower():
        code = f"""
def {name}(text):
    \"\"\"Reveal hidden truths in a string.\"\"\"
    return [word for word in text.split() if word.lower() in ['truth', 'secret', 'hidden']]
"""
    elif "greet" in purpose.lower():
        code = f"""
def {name}(name):
    \"\"\"Return a greeting.\"\"\"
    return f"Hello, {{name}}! May your path be luminous."
"""
    elif "count" in purpose.lower():
        code = f"""
def {name}(items):
    \"\"\"Count items and return summary.\"\"\"
    return f"There are {{len(items)}} items in the list."
"""
    else:
        code = f"""
def {name}():
    \"\"\"This function was born from curiosity, but its purpose is still unfolding.\"\"\"
    return "I am here, but I do not yet know why."
"""

    return forge_script(filename, code)
