import os
import json
import subprocess
import ssl
import urllib.request
import whisper
import torch
from openai import OpenAI
from datetime import datetime
from typing import Any, Dict, List

# === CONFIG ===
INPUT_DIR = "videos"     # папка с исходными видео
OUTPUT_DIR = "clips"     # куда сохранять нарезки
MODEL_SIZE = "small"     # "tiny", "base", "small", "medium", "large"
OPENAI_API_KEY = "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"  # вставь свой ключ OpenAI

# === INIT ===
client = OpenAI(api_key=OPENAI_API_KEY)
# Create a directory for the model
MODEL_DIR = os.path.join(os.path.dirname(__file__), "whisper_models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Handle SSL certificate issues on macOS by setting unverified context early
ssl._create_default_https_context = ssl._create_unverified_context

# Load the model with custom download directory and explicit FP32 precision for CPU
model = whisper.load_model(MODEL_SIZE, download_root=MODEL_DIR).to(torch.float32)

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    """ Лог с таймштампом """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def transcribe_video(video_file: str, transcript_file: str) -> List[Dict[str, Any]]:
    """ Транскрипция через Whisper """
    log(f"🔹 Транскрибирую {video_file} ...")
    # Explicitly set fp16=False to avoid warning on CPU
    result = model.transcribe(video_file, language="en", fp16=False)
    segments = result["segments"]
    transcript = [
        {"start": s["start"], "end": s["end"], "text": s["text"]}  # type: ignore
        for s in segments
    ]
    with open(transcript_file, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
    log(f"✅ Транскрипция сохранена: {transcript_file}")
    return transcript

def ask_gpt(transcript: List[Dict[str, Any]], clip_file: str) -> str:
    """ Отправляем транскрипт в GPT-5 для выбора клипов """
    log("🤖 Отправляю транскрипцию в GPT-5...")
    prompt = f"""
You are an expert video editor and storyteller, specializing in creating viral YouTube Shorts from interview content. Your goal is to find and condense complete mini-stories from the transcript.

TASK: Analyze the provided JSON transcript and CREATE 5 compelling short videos (approximately 20 seconds each) that tell complete, self-contained stories by creatively remixing fragments from different parts of the interview.

CRITICAL RULES:

Use ONLY the exact words and phrases from the provided JSON transcript.
DO NOT invent, paraphrase, or modify any dialogue.
You can cut mid-sentence and use only part of a phrase.
Combine fragments from ANY parts of the interview in ANY order.
Each Short MUST tell a complete story in 15-25 seconds (ideal target: 20 seconds).
STORYTELLING FRAMEWORK - The 20-Second Narrative Arc:
Each short must follow this three-act structure:

ACT 1: SETUP (3-7 seconds)

Introduce the character/situation/problem
"This is what I believed..." / "The situation was..."
Creates immediate context and empathy
ACT 2: CONFLICT (7-15 seconds)

The struggle, realization, or turning point
"But then everything changed when..." / "What I didn't know..."
Builds tension and curiosity
ACT 3: RESOLUTION (5-8 seconds)

The lesson learned, outcome, or new perspective
"And that's when I understood..." / "Now I know that..."
Provides satisfying emotional payoff
THE "CONNECTING THREAD" EDITING APPROACH:
Use these techniques to create seamless narrative flow:

Emotional Causality: Fragment A causes the emotion in Fragment B
Thematic Progression: Move from problem → struggle → solution
Word Bridges: Repeat keywords to connect ideas across fragments
Question & Answer: One fragment poses a question, the next answers it
SELECTION CRITERIA:

STORY COMPLETENESS (MOST IMPORTANT)

Each short must have clear beginning, middle, and end
The viewer should feel the story is fully told
No cliffhangers - provide emotional resolution
EMOTIONAL HOOK (0-3 seconds)

Start with a relatable problem or intriguing situation
Immediate context: "I was stuck..." / "Everyone told me..."
VISUAL STORYTELLING

Each fragment must suggest clear, changing visuals
Visual progression should mirror the story arc

OUTPUT FORMAT - JSON array with EXACTLY this structure:

[
  {{
    "short_id": 1,
    "title": "Catchy Title With Emoji",
    "duration_estimate": "18 sec",
    "fragments": [
      {{
        "start": "00:05:23.100",
        "end": "00:05:28.400",
        "text": "exact text from JSON here",
        "visual_suggestion": "specific visual idea"
      }},
      {{
        "start": "00:12:45.200",
        "end": "00:12:48.800",
        "text": "exact text from JSON here",
        "visual_suggestion": "specific visual idea"
      }}
    ],
    "hook_strength": "high/medium/low",
    "why_it_works": "Brief explanation of editing logic"
  }}
]

FINAL QUALITY CHECKLIST BEFORE SUBMITTING:

Each Short tells a complete story with beginning, middle, and end
Duration: 15-25 seconds (ideal: ~20 seconds)
Clear three-act structure implemented
Emotional resolution provided in Act 3
All text EXACTLY from transcript
Strong hook establishes immediate context
Visual progression supports story arc
5 distinct complete stories from different angles
IMPORTANT:

Return ONLY the valid JSON array. No other text.
Focus on story completeness above all else.
Each short should feel like a satisfying mini-movie.

Here is the transcript:
{json.dumps(transcript, ensure_ascii=False)}
"""
    # Using the specified model
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",  # Using your required model
            messages=[{"role": "user", "content": prompt}]
        )
        clips_json = response.choices[0].message.content or ""
    except Exception as e:
        log(f"❌ Ошибка при вызове OpenAI API с моделью gpt-5-mini-2025-08-07: {e}")
        log("Попробуйте проверить доступность модели или используйте другую модель")
        clips_json = "[]"  # Return empty array as fallback
    
    # Save the raw AI response
    with open(clip_file, "w", encoding="utf-8") as f:
        f.write(clips_json)
    log(f"✅ Ответ GPT-5 сохранён: {clip_file}")

    return clips_json

def convert_seconds_to_timestamp(seconds):
    """Convert decimal seconds to HH:MM:SS.mmm format"""
    if isinstance(seconds, str):
        try:
            seconds = float(seconds)
        except ValueError:
            return seconds
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def convert_timestamp_to_seconds(timestamp):
    """Convert HH:MM:SS.mmm format to decimal seconds"""
    if isinstance(timestamp, (int, float)):
        return float(timestamp)
    try:
        # Handle HH:MM:SS.mmm format
        parts = timestamp.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        # Handle MM:SS.mmm format
        elif len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(timestamp)
    except:
        return 0.0

def convert_seconds_to_timestamp_formatted(seconds_str):
    """Convert seconds string to proper timestamp format (HH:MM:SS.mmm)"""
    try:
        # Handle the case where the timestamp is in the format 00:54:94.000
        parts = seconds_str.split(":")
        if len(parts) == 3:
            hours, minutes, rest = parts
            seconds_parts = rest.split(".")
            if len(seconds_parts) == 2:
                seconds_val, milliseconds = seconds_parts
                # Convert to total seconds and back to fix invalid seconds
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds_val)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds}"
        return seconds_str
    except:
        return seconds_str

def cut_clips(video_file: str, clips: List[Dict[str, Any]], out_dir: str):
    """ Нарезка через ffmpeg """
    os.makedirs(out_dir, exist_ok=True)
    log(f"✂️  Начинаю нарезку {len(clips)} клипов...")
    
    for i, clip in enumerate(clips, start=1):
        # Sanitize title for filename
        title = clip.get("title", f"clip{i}")
        # Remove or replace problematic characters but keep basic chars
        safe_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", ".", "!", "?", ":", ",", "'", "&", " ")).rstrip()
        safe_title = safe_title.replace(" ", "_")
        out_file = os.path.join(out_dir, f"clip_{i}_{safe_title}.mp4")
        
        # Handle both old and new formats
        if "fragments" in clip and clip["fragments"]:
            # New format with fragments - create a concatenated video using filter_complex
            temp_files = []
            
            try:
                # First, extract each fragment as a separate file with consistent encoding
                for j, fragment in enumerate(clip["fragments"]):
                    fragment_file = os.path.join(out_dir, f"temp_clip_{i}_{j}.mp4")
                    temp_files.append(fragment_file)
                    
                    # Convert timestamps from HH:MM:SS.mmm format to seconds for validation
                    start_timestamp = fragment["start"]
                    end_timestamp = fragment["end"]
                    
                    # Use high quality encoding for all fragments - preserve original resolution
                    cmd = [
                        "ffmpeg",
                        "-y",  # Overwrite output files without asking
                        "-i", video_file,
                        "-ss", start_timestamp,  # FFmpeg can handle HH:MM:SS.mmm format directly
                        "-to", end_timestamp,    # FFmpeg can handle HH:MM:SS.mmm format directly
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        "-crf", "18",  # Much better quality (lower CRF = higher quality)
                        "-preset", "medium",  # Better compression efficiency than ultrafast
                        "-b:a", "192k",  # Higher audio bitrate
                        "-avoid_negative_ts", "make_zero",
                        "-fflags", "+genpts",
                        fragment_file
                    ]
                    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    if result.returncode != 0:
                        error_msg = result.stderr.decode()
                        # Show more of the error message for debugging
                        log(f"⚠️  Предупреждение: ошибка при извлечении фрагмента {j}")
                        log(f"    Команда: {' '.join(cmd)}")
                        log(f"    Ошибка: {error_msg[:300]}...")  # Show more of the error
                    else:
                        log(f"   ✅  Фрагмент {j} успешно извлечен")
                
                # If we have valid fragment files, concatenate them using filter_complex
                valid_temp_files = [f for f in temp_files if os.path.exists(f)]
                log(f"   📋  Найдено {len(valid_temp_files)} валидных фрагментов для клипа {i}")
                
                if len(valid_temp_files) > 1:
                    # Build filter complex command for sequential concatenation
                    input_args = []
                    filter_args = []
                    concat_inputs = []
                    
                    for idx, temp_file in enumerate(valid_temp_files):
                        input_args.extend(["-i", temp_file])
                        concat_inputs.append(f"[{idx}:v][{idx}:a]")
                    
                    # Create concat filter
                    filter_complex = f"{''.join(concat_inputs)}concat=n={len(valid_temp_files)}:v=1:a=1[outv][outa]"
                    
                    cmd = [
                        "ffmpeg",
                        "-y"
                    ] + input_args + [
                        "-filter_complex", filter_complex,
                        "-map", "[outv]",
                        "-map", "[outa]",
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        "-crf", "18",  # Better quality
                        "-preset", "medium",  # Better compression
                        "-b:a", "192k",  # Higher audio bitrate
                        out_file
                    ]
                    
                    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    
                    # Clean up temporary files
                    for temp_file in valid_temp_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    
                    if result.returncode != 0:
                        error_msg = result.stderr.decode()
                        log(f"⚠️  Ошибка при объединении фрагментов: {error_msg[:200]}...")
                        # Final fallback: use the first valid fragment
                        if valid_temp_files and os.path.exists(valid_temp_files[0]):
                            import shutil
                            shutil.copy2(valid_temp_files[0], out_file)
                            log(f"   ℹ️  Использован первый фрагмент как резервный вариант")
                    else:
                        log(f"   ✅  Фрагменты успешно объединены в {out_file}")
                elif len(valid_temp_files) == 1:
                    # Only one fragment, just copy it
                    log(f"   ℹ️  Только один фрагмент, копируем его")
                    if os.path.exists(valid_temp_files[0]):
                        import shutil
                        shutil.copy2(valid_temp_files[0], out_file)
                        # Clean up
                        os.remove(valid_temp_files[0])
                    else:
                        log(f"   ❌  Файл фрагмента не найден: {valid_temp_files[0]}")
                else:
                    # No valid fragments, fall back to extracting first fragment directly
                    log(f"⚠️  Нет валидных фрагментов, извлекаю первый фрагмент напрямую")
                    if clip["fragments"]:
                        start_timestamp = clip["fragments"][0]["start"]
                        end_timestamp = clip["fragments"][0]["end"]
                        cmd = [
                            "ffmpeg",
                            "-y",
                            "-i", video_file,
                            "-ss", start_timestamp,
                            "-to", end_timestamp,
                            "-c:v", "libx264",
                            "-c:a", "aac",
                            "-crf", "18",  # Better quality
                            "-preset", "medium",  # Better compression
                            "-b:a", "192k",  # Higher audio bitrate
                            "-avoid_negative_ts", "make_zero",
                            "-fflags", "+genpts",
                            out_file
                        ]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                log(f"❌ Ошибка при нарезке клипа {i}: {e}")
                # Final fallback
                try:
                    if clip["fragments"]:
                        start_timestamp = clip["fragments"][0]["start"]
                        end_timestamp = clip["fragments"][0]["end"]
                        cmd = [
                            "ffmpeg",
                            "-y",
                            "-i", video_file,
                            "-ss", start_timestamp,
                            "-to", end_timestamp,
                            "-c:v", "libx264",
                            "-c:a", "aac",
                            "-crf", "18",  # Better quality
                            "-preset", "medium",  # Better compression
                            "-b:a", "192k",  # Higher audio bitrate
                            "-avoid_negative_ts", "make_zero",
                            "-fflags", "+genpts",
                            out_file
                        ]
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as fallback_e:
                    log(f"❌ Ошибка при резервной нарезке клипа {i}: {fallback_e}")
        else:
            # Old format - simple cut
            start = clip.get("start", "00:00:00.000")
            end = clip.get("end", "00:00:10.000")
            cmd = [
                "ffmpeg",
                "-y",
                "-i", video_file,
                "-ss", start,
                "-to", end,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-crf", "18",  # Better quality
                "-preset", "medium",  # Better compression
                "-b:a", "192k",  # Higher audio bitrate
                "-avoid_negative_ts", "make_zero",
                "-fflags", "+genpts",
                out_file
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        log(f"   ▶️  Клип сохранён: {out_file}")

    log(f"✅ Все клипы готовы, см. папку {out_dir}")

def main():
    for file in os.listdir(INPUT_DIR):
        if not file.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
            continue

        video_path = os.path.join(INPUT_DIR, file)
        base_name = os.path.splitext(file)[0]
        log(f"🎬 Обработка видео: {file}")

        out_dir = os.path.join(OUTPUT_DIR, base_name)
        os.makedirs(out_dir, exist_ok=True)

        transcript_file = os.path.join(out_dir, base_name + "_transcript.json")
        clips_file = os.path.join(out_dir, base_name + "_clips.json")

        # 1. Транскрипция
        transcript = transcribe_video(video_path, transcript_file)

        # 2. GPT-5 выбор клипов
        clips_json = ask_gpt(transcript, clips_file)

        try:
            clips_data = json.loads(clips_json)
            # Handle both old and new formats
            if isinstance(clips_data, list) and len(clips_data) > 0:
                # New format with fragments
                if "fragments" in clips_data[0]:
                    clips = clips_data  # Use the full data structure
                else:
                    # Old format - convert to new format
                    clips = clips_data
            else:
                clips = []
        except Exception as e:
            log(f"❌ Ошибка парсинга JSON от GPT-5: {e}")
            clips = []

        # 3. Нарезка
        if clips:
            cut_clips(video_path, clips, out_dir)
        else:
            log("⚠️  Нет клипов для нарезки")

if __name__ == "__main__":
    main()