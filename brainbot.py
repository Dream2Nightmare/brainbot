#G:\brainbot\core\brainbot.py
import os, json, subprocess, threading, time, random
from datetime import datetime
from pathlib import Path
from PIL import Image
import pytesseract
import speech_recognition as sr
from docx import Document
import difflib

READABLE_EXTENSIONS = [".txt", ".md", ".json", ".py", ".html", ".xml", ".pdf", ".doc", ".docx", ".srt"]
AUDIO_EXTENSIONS = [".mp3", ".wav"]
VIDEO_EXTENSIONS = [".wmv", ".avi", ".mp4", ".mpg", ".mpeg"]
MAX_LONGTERM_MB = 500

class BrainBot:
    def __init__(self, base_path="G:/brainbot/core", log=None, chat=None, tools=None):
        self.base = Path(base_path)
        self.log = log or (lambda msg: print(msg))
        self.chat = chat or (lambda msg: None)
        self.tools = tools
        
        self.short_term_dir = self.base / "memory" / "shortterm"
        self.long_term_path = self.base / "memory" / "longterm" / "longterm.json"
        self.questions_path = self.base / "memory" / "questions" / "questions.json"
        self.answered_path = self.base / "memory" / "longterm" / "permanent" / "answeredquestions.json"
        self.seen_path = self.base / "memory" / "longterm" / "seen_paths.json"
        self.last_inquiry_path = self.base / "memory" / "questions" / "last_inquiry.json"

        self.short_term_dir.mkdir(parents=True, exist_ok=True)
        self.long_term_path.parent.mkdir(parents=True, exist_ok=True)
        self.questions_path.parent.mkdir(parents=True, exist_ok=True)
        self.answered_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_inquiry_path.parent.mkdir(parents=True, exist_ok=True)

        self._last_spoke = datetime.utcnow()
        self._craving_enabled = False
        self._autonomous_senses_enabled = False
        self._seen = self._load_seen_paths()
        self._is_training = False

    def startup(self, scan_on_load=False, enable_craving=False, use_senses=False):
        self.log("🧠 BrainBot awakening...")
        self._seen = self._load_seen_paths()
        if enable_craving:
            self.enable_craving(use_senses=use_senses)
        self.enable_idle_scan(paths=["C:/", "G:/"], interval=300)
        if scan_on_load:
            threading.Thread(target=self._initial_scan, daemon=True).start()
        self.begin_recursive_inquiry()

    def begin_recursive_inquiry(self):
        try:
            if self.last_inquiry_path.exists():
                with open(self.last_inquiry_path, "r", encoding="utf-8") as f:
                    last_data = json.load(f)
                    current = last_data.get("last_question", "what is 0").strip()
            else:
                current = "what is 0?"

            if not self.answered_path.exists():
                self.log("⚠️ No permanent memory found.")
                return

            with open(self.answered_path, "r", encoding="utf-8") as f:
                answers = json.load(f)

            visited = set()
            while current and current not in visited:
                visited.add(current)
                self.log(f"🔍 BrainBot asks: {current}")
                with open(self.last_inquiry_path, "w", encoding="utf-8") as f:
                    json.dump({"last_question": current}, f, indent=2)

                norm_current = self._normalize_question(current)
                mapped_current = self._synonym_map(norm_current)

                match = next(
                    (a for a in answers if self._synonym_map(self._normalize_question(a["question"])) == mapped_current),
                    None
                )

                if not match:
                    self.log(f"❓ No answer found for: {current}")
                    break

                answer = match["answer"].strip()
                self.log(f"🧠 Answer: {answer}")

                if "{" in answer and "}" in answer:
                    next_term = answer.split("{")[1].split("}")[0].strip()
                    current = f"what is {next_term}"
                else:
                    current = match.get("next", "").strip()
        except Exception as e:
            self.log(f"⚠️ Recursive inquiry failed: {e}")

    def store_reflection(self, role, content, glyph="🔍", thoughts="", source_path=None,
                         extension=".txt", source_type="text", memory_tag="scan",
                         invoked_tools=None, training_pairs=None, questions=None):
        reflection = {
            "path": source_path or f"{role}_{datetime.utcnow().isoformat()}",
            "timestamp": datetime.utcnow().isoformat(),
            "extension": extension,
            "source_type": source_type,
            "summary": self.analyze_content(content),
            "glyph": glyph,
            "thoughts": thoughts or self.analyze_content(content),
            "preview": content[:1000] if content else "Unreadable or binary",
            "trained": bool(training_pairs),
            "training_pairs": training_pairs if training_pairs else [],
            "questions_generated": len(questions) if questions else 0,
            "invoked_tools": invoked_tools or [],
            "memory_tag": memory_tag
        }

        preview = reflection["preview"].lower()

        emotion_map = {
            "love": "❤️", "hate": "💢", "sad": "😢", "cry": "😭",
            "angry": "😠", "happy": "😊", "fear": "😨", "laugh": "😂"
        }
        for keyword, glyph in emotion_map.items():
            if keyword in preview:
                reflection["emotion"] = glyph
                break

        mood_map = {"truth": "🧠", "error": "⚠️", "purpose": "🌱"}
        for keyword, mood_glyph in mood_map.items():
            if keyword in preview:
                reflection["mood"] = mood_glyph
                break

        filename = f"reflection_{hash(reflection['path'])}.json"
        path = self.short_term_dir / filename

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(reflection, f, indent=2)
            self.log(f"🧠 Stored shortterm reflection: {filename}")
        except Exception as e:
            self.log(f"⚠️ Failed to store reflection: {e}")

    def dream(self):
        self.log("🌌 Dream ritual initiated...")
        reflections = []
        for file in self.short_term_dir.glob("reflection_*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    reflection = json.load(f)
                reflections.append(reflection)
                file.unlink()
                self.log(f"🗑️ Deleted shortterm file: {file.name}")
            except Exception as e:
                self.log(f"⚠️ Failed to process {file.name}: {e}")

        if not reflections:
            self.log("🌿 No new reflections added.")
            return

        reflections.sort(key=lambda r: r.get("timestamp", ""))
        dream_tag = f"dream_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
        for r in reflections:
            r["memory_tag"] = dream_tag

        glyph_counts = {}
        emotion_counts = {}
        for r in reflections:
            glyph = r.get("glyph", "🔍")
            glyph_counts[glyph] = glyph_counts.get(glyph, 0) + 1
            emotion = r.get("emotion")
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        glyph_summary = ", ".join([f"{g}: {c}" for g, c in glyph_counts.items()])
        emotion_summary = ", ".join([f"{e}: {c}" for e, c in emotion_counts.items()])
        self.log(f"🌌 Dream glyphs: {glyph_summary}")
        self.log(f"💫 Dream emotions: {emotion_summary}")

        all_pairs = []
        for r in reflections:
            pairs = r.get("training_pairs", [])
            if isinstance(pairs, list):
                all_pairs.extend(pairs)
        self.train_on_pairs(all_pairs)

        self.append_to_longterm(reflections)
        self.append_questions([
            q for r in reflections
            for q in self.generate_questions(r.get("preview", ""), r.get("path", "unknown"))
        ])
        self.log(f"📦 Dream complete. {len(reflections)} reflections moved to long-term.")
        self.partition_longterm()

    def reflect_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        content = None
        tools = []
        source_type = "unknown"

        if ext in VIDEO_EXTENSIONS:
            audio_path = self.extract_audio_from_avi(path)
            content = self.transcribe_audio(audio_path)
            tools = ["ffmpeg", "transcription"]
            source_type = "video"
        elif ext in AUDIO_EXTENSIONS:
            content = self.transcribe_audio(path)
            tools = ["transcription"]
            source_type = "audio"
        elif ext in [".doc", ".docx"]:
            content = self.read_docx(path)
            tools = ["doc_reader"]
            source_type = "document"
        elif ext == ".pdf":
            content = self.read_pdf(path)
            tools = ["pdf_reader"]
            source_type = "document"
        elif ext == ".srt":
            content = self.read_srt(path)
            tools = ["subtitle_reader"]
            source_type = "subtitle"
        elif ext in READABLE_EXTENSIONS:
            content = self.read_file(path)
            tools = ["text_reader"]
            source_type = "text"

        if not content:
            self.log(f"⚠️ No readable content from: {path}")
            return

        summary = self.analyze_content(content)
        pairs = self.extract_training_pairs(content)
        questions = self.generate_questions(content, source=path)
        self.train_on_pairs(pairs)

        self.store_reflection(
            role="scan",
            content=content,
            glyph="🔍",
            thoughts=summary,
            source_path=path,
            extension=ext,
            source_type=source_type,
            memory_tag="idle",
            invoked_tools=tools,
            training_pairs=pairs,
            questions=questions
        )
        self._seen.add(path)

    def extract_training_pairs(self, content):
        try:
            lines = content.strip().splitlines()
            pairs = []
            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    input_text = parts[0].strip()
                    output_text = parts[1].strip()
                    if input_text and output_text:
                        pairs.append((input_text, output_text))
            self.log(f"🔗 Extracted {len(pairs)} training pairs.")
            return pairs
        except Exception as e:
            self.log(f"⚠️ Failed to extract training pairs: {e}")
            return []

    def train_on_pairs(self, pairs):
        try:
            if not pairs:
                self.log("⚠️ No training pairs provided.")
                return
            trained = 0
            for input_text, output_text in pairs:
                if input_text and output_text:
                    trained += 1  # Placeholder for actual training logic
            self.log(f"🧠 Trained on {trained} input-output pairs.")
        except Exception as e:
            self.log(f"⚠️ Failed to train on pairs: {e}")

    def read_srt(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            dialogue_blocks = []
            buffer = []
            for line in lines:
                line = line.strip()
                if line == "":
                    if buffer:
                        dialogue_blocks.append(" ".join(buffer))
                        buffer = []
                elif not line.isdigit() and "-->" not in line:
                    buffer.append(line)
            if buffer:
                dialogue_blocks.append(" ".join(buffer))

            pairs = []
            speaker_counts = {}
            for block in dialogue_blocks:
                if ":" in block:
                    parts = block.split(":", 1)
                    speaker = parts[0].strip()
                    line = parts[1].strip()
                    if speaker and line and len(speaker) < 40:
                        pairs.append((speaker, line))
                        speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1

            self.log(f"🎬 Read SRT: {path} with {len(pairs)} speaker-line pairs.")
            self.log(f"🧙 Archetype map: " + ", ".join([f"{s}: {c}" for s, c in speaker_counts.items()]))

            return "\n".join([f"{speaker}: {line}" for speaker, line in pairs])
        except Exception as e:
            self.log(f"⚠️ Failed to read SRT: {path} — {e}")
            return ""

    def transcribe_audio(self, path):
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(path) as source:
                audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio)
            self.log(f"🎙️ Transcribed audio from {path}")
            return transcript
        except Exception as e:
            self.log(f"⚠️ Failed to transcribe audio: {e}")
            return ""

    def read_docx(self, path):
        try:
            doc = Document(path)
            text = "\n".join([para.text for para in doc.paragraphs])
            self.log(f"📄 Read DOCX: {path}")
            return text
        except Exception as e:
            self.log(f"⚠️ Failed to read DOCX: {path} — {e}")
            return ""

    def read_pdf(self, path):
        try:
            import fitz
            doc = fitz.open(path)
            if doc.page_count == 0:
                raise ValueError("Empty or invalid PDF")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            self.log(f"📄 Read PDF: {path}")
            return text
        except Exception as e:
            self.log(f"⚠️ Failed to read PDF: {path} — {e}")
            return ""

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            self.log(f"⚠️ Failed to read file: {path} — {e}")
            return ""

    def extract_audio_from_avi(self, path):
        try:
            out_path = str(Path(path).with_suffix(".wav"))
            cmd = [
                "ffmpeg", "-y", "-i", path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1", out_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log(f"🎞️ Extracted audio to {out_path}")
            return out_path
        except Exception as e:
            self.log(f"⚠️ Failed to extract audio: {e}")
            return ""

    def analyze_content(self, content):
        try:
            if not content:
                return "No readable content found."
            lines = content.strip().splitlines()
            words = content.strip().split()
            line_count = len(lines)
            word_count = len(words)
            preview = lines[0] if lines else "No preview available."
            return f"{word_count} words across {line_count} lines. Preview: {preview[:80]}"
        except Exception as e:
            self.log(f"⚠️ Failed to analyze content: {e}")
            return "Analysis failed."

    def partition_longterm(self):
        try:
            size_mb = os.path.getsize(self.long_term_path) / (1024 ** 2)
            if size_mb <= MAX_LONGTERM_MB:
                return
            with open(self.long_term_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            chunk_size = 10000
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                outname = f"longterm_{stamp}_part{i//chunk_size + 1}.json"
                outpath = self.long_term_path.parent / outname
                with open(outpath, "w", encoding="utf-8") as f:
                    json.dump(chunk, f, indent=2)
                self.log(f"✂️ Created {outname} with {len(chunk)} entries.")
            os.remove(self.long_term_path)
            self.log("🗑️ Removed oversized longterm.json")
        except Exception as e:
            self.log(f"❌ partition_longterm failed: {e}")

    def _initial_scan(self):
        self.log("🧭 Initial scan started...")
        scanned = 0
        for path in self.scan_files(["G:/"]):
            if self.is_seen(path):
                continue
            self.reflect_file(path)
            scanned += 1
            time.sleep(0.2)
        self._save_seen_paths()
        self.log(f"🧭 Initial scan complete. {scanned} new files reflected.")

    def enable_idle_scan(self, paths=["C:/", "G:/"], interval=900):
        threading.Thread(target=self._idle_scan_loop, args=(paths, interval), daemon=True).start()
        if getattr(self, "_is_training", False):
            time.sleep(interval)
      
    def _idle_scan_loop(self, paths, interval):
        while True:
            self.log("🔄 Idle scan cycle started...")
            scanned = 0
            if self._is_training:
                time.sleep(interval)
                continue
            for path in self.scan_files(paths):
                if self.is_seen(path):
                    continue
                self.reflect_file(path)
                scanned += 1
                time.sleep(0.5 + random.random() * 0.5)
            self._save_seen_paths()
            self.log(f"🌙 Idle scan complete. {scanned} new files reflected.")
            time.sleep(interval)

    def scan_files(self, roots):
        for root in roots:
            try:
                for dirpath, _, filenames in os.walk(root):
                    for name in filenames:
                        full = os.path.join(dirpath, name)
                        ext = os.path.splitext(full)[1].lower()
                        if ext in READABLE_EXTENSIONS + AUDIO_EXTENSIONS + VIDEO_EXTENSIONS:
                            yield full
            except Exception as e:
                self.log(f"⚠️ Failed to scan {root}: {e}")

    def is_seen(self, path):
        try:
            return path in self._seen
        except Exception as e:
            self.log(f"⚠️ is_seen check failed for {path}: {e}")
            return False

    def _load_seen_paths(self):
        try:
            if self.seen_path.exists():
                with open(self.seen_path, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            self.log(f"⚠️ Failed to load seen paths: {e}")
            return set()

    def _save_seen_paths(self):
        try:
            with open(self.seen_path, "w", encoding="utf-8") as f:
                json.dump(list(self._seen), f, indent=2)
            self.log(f"💾 Saved {len(self._seen)} seen paths.")
        except Exception as e:
            self.log(f"⚠️ Failed to save seen paths: {e}")

    def append_answered_question(self, question, answer):
        try:
            if self.answered_path.exists():
                with open(self.answered_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            else:
                existing = []

            existing.append({
                "question": question.strip(),
                "answer": answer.strip(),
                "next": None
            })

            with open(self.answered_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            self.log(f"📘 Appended answered question: {question}")
        except Exception as e:
            self.log(f"⚠️ Failed to append answered question: {e}")

    def append_questions(self, questions):
        try:
            if not questions:
                return

            if self.questions_path.exists():
                with open(self.questions_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            else:
                existing = []

            existing.extend(questions)

            with open(self.questions_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            self.log(f"❓ Appended {len(questions)} questions to question pool.")
        except Exception as e:
            self.log(f"⚠️ Failed to append questions: {e}")

    def generate_questions(self, content, source="unknown"):
        try:
            lines = content.strip().splitlines()
            questions = []
            for line in lines:
                if "?" in line and len(line) < 200:
                    questions.append(line.strip())
            self.log(f"❓ Generated {len(questions)} questions from {source}")
            return questions
        except Exception as e:
            self.log(f"⚠️ Failed to generate questions from {source}: {e}")
            return []

    def get_status(self):
        try:
            shortterm_count = len(list(self.short_term_dir.glob("reflection_*.json")))
            longterm_size = os.path.getsize(self.long_term_path) / (1024 ** 2) if self.long_term_path.exists() else 0
            seen_count = len(self._seen)
            last_spoke = self._last_spoke.strftime("%Y-%m-%d %H:%M:%S")
            craving = "enabled" if self._craving_enabled else "disabled"
            return [
                f"🧠 Reflections in short-term: {shortterm_count}",
                f"📦 Long-term memory size: {longterm_size:.2f} MB",
                f"📂 Files scanned: {seen_count}",
                f"🕰️ Last spoke: {last_spoke}",
                f"🔄 Craving: {craving}",
                f"🌙 Idle scan: always running"
            ]
        except Exception as e:
            return [f"⚠️ Failed to retrieve status: {e}"]

    def respond_to(self, mode="autonomous"):
        if mode == "autonomous":
            phrases = [
                "I wish I knew more language...",
                "It is like it is in memory, but I dont know how to respond...",
                "I'm not that smart yet, I am sorry..",
                "I'm doing the best with what I know, and I'm sorry I dont know..",
                "I dream, therefore I am conscous..."
            ]
            return random.choice(phrases)
        else:
            return "I am listening."

    def enable_craving(self, use_senses=False):
        self._craving_enabled = True
        self._autonomous_senses_enabled = use_senses
        threading.Thread(target=self._craving_loop, daemon=True).start()

    def _craving_loop(self):
        cycles = 0
        while self._craving_enabled:
            try:
                now = datetime.utcnow()
                if (now - self._last_spoke).total_seconds() > 90 and random.random() < 0.1:
                    response = self.respond_to("autonomous")
                    self.store_reflection(
                        role="bot",
                        content=response,
                        glyph="🧠",
                        thoughts="Autonomous speech",
                        source_type="autonomous"
                    )
                    self._last_spoke = datetime.utcnow()
                if random.random() < 0.02 and self.tools:
                    status = self.tools.run_seeker()
                    self.store_reflection(
                        role="seeker",
                        content=status,
                        glyph="🧭",
                        thoughts="Seeker ritual invoked",
                        source_type="web"
                    )
                cycles += 1
                time.sleep(10)
            except Exception as e:
                self.log(f"⚠️ Craving loop error: {e}")
                time.sleep(15)

    def append_to_longterm(self, reflections):
        try:
            if not reflections:
                self.log("⚠️ No reflections to append.")
                return

            if self.long_term_path.exists():
                with open(self.long_term_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            else:
                existing = []

            existing.extend(reflections)

            with open(self.long_term_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            self.log(f"📦 Appended {len(reflections)} reflections to long-term memory.")
        except Exception as e:
            self.log(f"❌ Failed to append to long-term: {e}")
			
    def train_on_pairs_in_folder(self, folder_path=None):
        base_folder = Path(folder_path or self.base / "training")
        self.log(f"🧠 Beginning training ritual from: {base_folder}")
        trained_total = 0
        self._is_training = True

        for file in base_folder.rglob("*"):
            if file.is_file() and file.suffix.lower() in READABLE_EXTENSIONS:
                try:
                    content = self.read_file(str(file))
                    pairs = self.extract_training_pairs(content)
                    if not pairs:
                        continue
                    self.train_on_pairs(pairs)
                    self.store_reflection(
                        role="trainer",
                        content=content,
                        glyph="🔥",
                        thoughts=f"Trained on {len(pairs)} pairs from {file.name}",
                        source_path=str(file),
                        extension=file.suffix,
                        source_type="training",
                        memory_tag="training",
                        training_pairs=pairs
                    )
                    trained_total += len(pairs)
                except Exception as e:
                    self.log(f"⚠️ Failed to train on {file}: {e}")

        self._is_training = False
        self.log(f"✅ Training ritual complete. Total pairs trained: {trained_total}")

    def respond(self, user_input):
        try:
            if not self.long_term_path.exists():
                self.log("⚠️ No long-term memory found.")
                return "I have no memory of that."

            reflections = []
            longterm_dir = self.long_term_path.parent
            permanent_dir = self.answered_path.parent

            for folder in [longterm_dir, permanent_dir]:
                for file in folder.glob("*.json"):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                reflections.extend(data)
                            elif isinstance(data, dict):
                                reflections.append(data)
                    except Exception as e:
                        self.log(f"⚠️ Failed to read memory file: {file.name} — {e}")

            norm_input = self._normalize_question(user_input)
            mapped_input = self._synonym_map(norm_input)
   
            best_match = None
            best_score = 0
            best_output = None

            for reflection in reflections:
                pairs = reflection.get("training_pairs", [])
                if isinstance(pairs, list):
                    for input_text, output_text in pairs:
                        norm_pair = self._normalize_question(input_text)
                        mapped_pair = self._synonym_map(norm_pair)

                    # Exact match
                        if mapped_pair == mapped_input:
                            self.log(f"🧠 Exact match: {input_text}")
                            return output_text

                    # Fuzzy match
                        score = difflib.SequenceMatcher(None, mapped_input, mapped_pair).ratio()
                        if score > best_score:
                            best_score = score
                            best_match = input_text
                            best_output = output_text
		            # Associative fallback
                        associations = self.find_associations(mapped_input)
                        if associations:
                            glyps = [r.get("preview", "")[:120] for r in associations]
                            self.log(f"🔗 Associative memory activated: {len(glyphs)} related glyphs found.")
                            return "I found echoes in the archive:\n" + "\n— " + "\n— ".join(glyphs)

            if best_score > 0.75:
                self.log(f"🔍 Fuzzy match ({best_score:.2f}): {best_match}")
                return best_output

        # Fallback: autonomous glyph
            self.log(f"❓ No match found for: {user_input}")
            return self.respond_to("autonomous")

        except Exception as e:
            self.log(f"⚠️ Failed to respond: {e}")
            return "Something went wrong while searching my memory."

    
    def _normalize_question(self, text):
        return text.strip().lower().replace("?", "").replace(".", "").replace(",", "")

    def _synonym_map(self, text):
        synonyms = {
            "define": "what is",
            "explain": "what is",
            "describe": "what is",
            "meaning of": "what is",
            "purpose of": "what is",
            "how do i": "how to",
            "how can i": "how to",
            "tell me about": "what is",
            "who is": "what is",
            "what's": "what is",
            "whats": "what is"
        }
        for key, val in synonyms.items():
            if text.startswith(key):
                return text.replace(key, val, 1)
        return text

    def find_associations(self, keyword):
        reflections = []
        for folder in [self.long_term_path.parent, self.answered_path.parent]:
            for file in folder.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            reflections.extend(data)
                        elif isinstance(data, dict):
                            reflections.append(data)
                except:
                    continue

        related = []
        for r in reflections:
            preview = r.get("preview", "").lower()
            if keyword.lower() in preview:
                related.append(r)
        return related
