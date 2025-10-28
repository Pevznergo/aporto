#!/usr/bin/env python
"""
Simple HTTP Server for Video Upscaling
Provides a REST API for upscaling videos using Real-ESRGAN.
"""

import os
import sys
import time
import json
import threading
import subprocess
from flask import Flask, request, jsonify, send_file
from upscale_app import upscale_video_with_realesrgan

# Optional imports for GPU-based transcription and cutting
try:
    import whisper
    import torch
    from openai import OpenAI
except Exception:
    whisper = None
    torch = None
    OpenAI = None

# Optional speaker-centered resizing (clipsai)
try:
    from clipsai import resize as clipsai_resize
except Exception:
    clipsai_resize = None

app = Flask(__name__)

# Simple job processing without complex queuing

# ---- Runtime environment introspection helpers ----

def _cuda_status():
    info = {
        "torch_installed": False,
        "torch_version": None,
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_devices": [],
    }
    try:
        import torch  # type: ignore
        info["torch_installed"] = True
        info["torch_version"] = getattr(torch, "__version__", None)
        info["cuda_available"] = bool(torch.cuda.is_available())
        try:
            cnt = torch.cuda.device_count() if info["cuda_available"] else 0
        except Exception:
            cnt = 0
        info["cuda_device_count"] = cnt
        devs = []
        for i in range(cnt):
            try:
                devs.append({
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "capability": tuple(torch.cuda.get_device_capability(i)),
                })
            except Exception:
                pass
        info["cuda_devices"] = devs
    except Exception:
        pass
    return info


def _resolve_model_paths():
    gfpgan = os.environ.get('GFPGAN_MODEL_PATH')
    realesr = os.environ.get('REALESRGAN_MODEL_PATH')
    return {
        "GFPGAN_MODEL_PATH": gfpgan,
        "REALESRGAN_MODEL_PATH": realesr,
    }

# In-memory job tracking
jobs = {}
job_counter = 0

# Base directories for cut pipeline
CUT_BASE = os.environ.get("CUT_BASE_DIR") or "/workspace/cut"
TO_CUT_DIR = os.path.join(CUT_BASE, "to_cut")
CUTED_DIR = os.path.join(CUT_BASE, "cuted")
os.makedirs(TO_CUT_DIR, exist_ok=True)
os.makedirs(CUTED_DIR, exist_ok=True)

def _is_file_stable(path: str, checks: int = 3, interval: float = 1.0, timeout: float = 30.0) -> bool:
    import time
    last = (-1, -1)
    start = time.time()
    while checks > 0 and (time.time() - start) <= timeout:
        try:
            st = os.stat(path)
            cur = (st.st_size, int(st.st_mtime))
        except FileNotFoundError:
            return False
        if cur == last:
            checks -= 1
        else:
            checks = 3
            last = cur
        time.sleep(interval)
    return checks == 0


def _ffprobe_video_ok(path: str) -> tuple[bool, str]:
    try:
        if not os.path.exists(path):
            return False, "Input file not found"
        if not _is_file_stable(path):
            return False, "Input file appears to be still uploading (not stable)"
        try:
            sz = os.path.getsize(path)
        except Exception:
            sz = 0
        if sz <= 0:
            return False, "Input file is empty"
        cmd = [
            'ffprobe', '-v', 'error', '-hide_banner',
            '-select_streams', 'v:0', '-show_entries', 'stream=codec_name',
            '-of', 'csv=p=0', path
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return True, ''
        return False, (r.stderr or r.stdout or 'ffprobe failed')
    except Exception as e:
        return False, str(e)

@app.route('/upscale', methods=['POST'])
def upscale_video():
    """
    Upscale a video file.
    
    Expected JSON payload:
    {
        "input_path": "/path/to/input/video.mp4",
        "output_path": "/path/to/output/video.mp4"
    }
    
    Returns:
    {
        "job_id": 123,
        "status": "processing"
    }
    """
    global job_counter
    
    try:
        data = request.get_json()
        input_path = data.get('input_path')
        output_path = data.get('output_path')
        
        if not input_path or not output_path:
            return jsonify({"error": "Missing input_path or output_path"}), 400
        
        if not os.path.exists(input_path):
            return jsonify({"error": "Input file not found"}), 404
        
        ok, err = _ffprobe_video_ok(input_path)
        if not ok:
            return jsonify({"error": f"Invalid input video: {err}"}), 400
        
        # Create a new job
        job_counter += 1
        job_id = job_counter
        
        jobs[job_id] = {
            "status": "processing",
            "input_path": input_path,
            "output_path": output_path,
            "start_time": time.time()
        }
        
        # Process in background
        thread = threading.Thread(target=process_upscale_job, args=(job_id, input_path, output_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "processing"
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_upscale_job(job_id, input_path, output_path):
    """Process the upscaling job in background."""
    try:
        success = upscale_video_with_realesrgan(input_path, output_path)
        
        jobs[job_id]["status"] = "completed" if success else "failed"
        jobs[job_id]["end_time"] = time.time()
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["end_time"] = time.time()

@app.route('/job/<int:job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of an upscaling job."""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"]
    }
    
    if "error" in job:
        response["error"] = job["error"]
    
    if "start_time" in job:
        response["start_time"] = job["start_time"]
    
    if "end_time" in job:
        response["end_time"] = job["end_time"]
        response["duration"] = job["end_time"] - job["start_time"]
    
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "video-upscale-api"})


@app.route('/env', methods=['GET'])
def env_report():
    """Report runtime environment details (safe, no secrets)."""
    cuda = _cuda_status()
    paths = _resolve_model_paths()
    resp = {
        "service": "video-upscale-api",
        "torch": cuda,
        "models": paths,
        "whisper_installed": bool(whisper is not None),
        "openai_sdk_installed": bool(OpenAI is not None),
        "cut_enable_upscale": str(os.environ.get('CUT_ENABLE_UPSCALE', '')).strip(),
        "cut_force_device": os.environ.get('CUT_FORCE_DEVICE', ''),
    }
    return jsonify(resp)

def _require_gfpgan_on_start():
    base = os.path.dirname(os.path.abspath(__file__))
    # Candidates: vastai_deployment/models and fallback to sibling upscale/models
    candidates = []
    env_path = os.environ.get('GFPGAN_MODEL_PATH')
    if env_path:
        candidates.append(env_path)
    candidates.append(os.path.join(base, 'models', 'GFPGANv1.4.pth'))
    candidates.append(os.path.join(os.path.dirname(base), 'models', 'GFPGANv1.4.pth'))
    found = None
    for p in candidates:
        try:
            if p and os.path.isfile(p):
                found = p
                break
        except Exception:
            pass
    if not found:
        checked = "\n".join(candidates)
        print("FATAL: Required GFPGAN weights not found. Checked:\n" + checked)
        print("Place GFPGANv1.4.pth in one of the listed locations or set GFPGAN_MODEL_PATH.")
        sys.exit(1)
    # Expose the resolved path to downstream code (if it respects GFPGAN_MODEL_PATH)
    os.environ.setdefault('GFPGAN_MODEL_PATH', found)

# ==== Cutting/transcription helpers ====

def _load_whisper_model(model_size: str):
    if whisper is None:
        raise RuntimeError("whisper not installed on server")
    m = whisper.load_model(model_size)
    # Device choice: env CUT_FORCE_DEVICE can be "cuda"|"cpu". Default: cuda if available.
    dev = os.environ.get('CUT_FORCE_DEVICE', '').strip().lower()
    try:
        if dev == 'cuda':
            m = m.to('cuda')
            print("[whisper] forced device: cuda")
        elif dev == 'cpu':
            print("[whisper] forced device: cpu")
        else:
            if torch is not None and torch.cuda.is_available():
                m = m.to('cuda')
                print("[whisper] auto device: cuda")
            else:
                print("[whisper] auto device: cpu")
    except Exception as e:
        print(f"[whisper] device set error: {e}")
    try:
        # best-effort log actual device
        p = next(m.parameters()) if hasattr(m, 'parameters') else None
        if p is not None and hasattr(p, 'device'):
            print(f"[whisper] model device: {p.device}")
    except Exception:
        pass
    return m


def _yt_dlp_download(url: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    # Use yt-dlp CLI to avoid vendor API drift
    cmd = [
        'yt-dlp',
        '-o', '%(title)s.%(ext)s',
        '--restrict-filenames',
        '-f', 'bv*+ba/b',
        '-P', out_dir,
    ]
    # Optional cookies support (env YTDLP_COOKIES_FILE)
    cookies = os.environ.get('YTDLP_COOKIES_FILE')
    if cookies and os.path.isfile(cookies):
        cmd += ['--cookies', cookies]
    # Optional extractor args (e.g., youtube:player-client=android or mweb)
    extractor_args = os.environ.get('YTDLP_EXTRACTOR_ARGS')
    if extractor_args:
        # Expect a single string acceptable by yt-dlp: --extractor-args "youtube:player-client=android"
        cmd += ['--extractor-args', extractor_args]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {r.stderr or r.stdout}")
    # Pick the newest file in out_dir
    entries = [os.path.join(out_dir, f) for f in os.listdir(out_dir)]
    entries = [p for p in entries if os.path.isfile(p)]
    if not entries:
        raise RuntimeError("yt-dlp reported success but no files found")
    newest = max(entries, key=lambda p: os.path.getmtime(p))
    return newest


def _transcribe_to_json(model, video_path: str, out_json: str) -> list:
    fp16 = bool(torch is not None and torch.cuda.is_available())
    result = model.transcribe(video_path, fp16=fp16)
    segs = result.get('segments') or []
    data = [{"start": s.get("start"), "end": s.get("end"), "text": s.get("text")} for s in segs]
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def _ask_openai_for_clips(transcript: list, out_json: str) -> list:
    if OpenAI is None:
        raise RuntimeError("openai SDK not installed on server")
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set on server")
    print(f"[GPT] Preparing to ask OpenAI for clips, transcript segments: {len(transcript)}")
    client = OpenAI(api_key=api_key)
    prompt = f"""
You are an expert video editor and storyteller, specializing in creating viral YouTube Shorts from interview content. Your goal is to find and condense complete mini-stories from the transcript.

TASK: Analyze the provided JSON transcript and CREATE 5 compelling short videos (approximately 20 seconds each) that tell complete, self-contained stories by creatively remixing fragments from different parts of the interview.

TWO-STAGE SELECTION PROCESS

Step 1: Candidate Generation
Identify 10 potential short video ideas (each 15–25 seconds long) that could become strong stories.
Each candidate should follow the storytelling structure below and feel emotionally engaging, clear, and complete.

Step 2: Ranking and Refinement
Rank the 10 candidates from 1 to 10 based on:

Emotional resonance (how much it makes the viewer feel)

Clarity and completeness of the story

Virality potential (likelihood to perform well on YouTube Shorts)

Select the top 5 and refine them into final versions that are polished, well-paced, and satisfying.

CRITICAL RULES:

Use ONLY the exact words and phrases from the provided JSON transcript.
DO NOT invent, paraphrase, or modify any dialogue.
You can cut mid-sentence and use only part of a phrase.
Combine fragments from ANY parts of the interview in ANY order.
Each Short MUST tell a complete story in 15-25 seconds (ideal target: 20 seconds).
Maintain full context in every clip — the viewer must always understand who or what is being discussed.
If a fragment refers to "he," "she," "they," or "it," ensure that earlier in the cut there is clear context establishing who or what is meant.
Avoid cuts that make the story ambiguous or confusing.
The goal is for each Short to feel self-contained, even if built from multiple parts of the interview.

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

OUTPUT FORMAT - JSON array with EXACTLY this structure:

[
  {{
    "short_id": 1,
    "title": "Catchy Title With Emoji",
    "duration_estimate": "18 sec",
    "description": "SEO-friendly description (3 sentences about what the video is about and what happens there) in English with 5-6 hashtags",
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

Return ONLY the valid JSON array. No other text.

Here is the transcript:
{json.dumps(transcript, ensure_ascii=False)}
"""
    try:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"[GPT] Calling OpenAI API with model: {model_name}")
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.choices[0].message.content or "[]"
        print(f"[GPT] Received response from OpenAI, length: {len(content)} chars")
        print(f"[GPT] Response preview: {content[:200]}...")
    except Exception as e:
        print(f"[GPT] ERROR calling OpenAI API: {type(e).__name__}: {e}")
        import traceback
        print(f"[GPT] Traceback:\n{traceback.format_exc()}")
        content = "[]"
    
    print(f"[GPT] Saving response to: {out_json}")
    with open(out_json, 'w', encoding='utf-8') as f:
        f.write(content)
    
    try:
        print(f"[GPT] Parsing JSON response...")
        data = json.loads(content)
        if isinstance(data, list):
            print(f"[GPT] Successfully parsed {len(data)} clips from response")
            return data
        else:
            print(f"[GPT] WARNING: Response is not a list, got type: {type(data)}")
            return []
    except Exception as e:
        print(f"[GPT] ERROR parsing JSON response: {type(e).__name__}: {e}")
        print(f"[GPT] Raw content: {content[:500]}...")
        return []


def _safe_name_from_path(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    safe = "".join(c for c in base if c.isalnum() or c in ("_", "-", ".", " ")).strip().replace(" ", "_")
    return safe or base


def _cut_clips_ffmpeg(video_path: str, clips: list, out_dir: str, clip_suffix: str = "") -> list:
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for i, clip in enumerate(clips, start=1):
        title = clip.get('title') or f'clip{i}'
        safe_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", ".", "!", "?", ":", ",", "'", "&", " ")).rstrip().replace(" ", "_")
        suffix = f"_{clip_suffix}" if clip_suffix else ""
        out_file = os.path.join(out_dir, f"clip_{i}_{safe_title}{suffix}.mp4")
        frs = clip.get('fragments') or []
        if not frs:
            continue
        try:
            if len(frs) == 1:
                s = frs[0]
                cmd = [
                    'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
                    '-i', video_path,
                    '-ss', s['start'], '-to', s['end'],
                    '-c:v', 'libx264', '-c:a', 'aac',
                    '-crf', '18', '-preset', 'medium', '-b:a', '192k',
                    '-avoid_negative_ts', 'make_zero', '-fflags', '+genpts',
                    out_file,
                ]
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode == 0:
                    made.append(out_file)
            else:
                # multi-fragment: extract parts then concat
                tmp_files = []
                for j, s in enumerate(frs):
                    tmp = os.path.join(out_dir, f"tmp_{i}_{j}.mp4")
                    tmp_files.append(tmp)
                    cmd = [
                        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
                        '-i', video_path,
                        '-ss', s['start'], '-to', s['end'],
                        '-c:v', 'libx264', '-c:a', 'aac',
                        '-crf', '18', '-preset', 'medium', '-b:a', '192k',
                        '-avoid_negative_ts', 'make_zero', '-fflags', '+genpts',
                        tmp,
                    ]
                    subprocess.run(cmd, capture_output=True)
                valid = [p for p in tmp_files if os.path.exists(p)]
                if len(valid) >= 1:
                    if len(valid) == 1:
                        import shutil
                        shutil.copy2(valid[0], out_file)
                        made.append(out_file)
                    else:
                        inputs = []
                        concat = []
                        for idx, p in enumerate(valid):
                            inputs += ['-i', p]
                            concat.append(f'[{idx}:v][{idx}:a]')
                        fc = f"{''.join(concat)}concat=n={len(valid)}:v=1:a=1[outv][outa]"
                        cmd = ['ffmpeg', '-y'] + inputs + [
                            '-filter_complex', fc, '-map', '[outv]', '-map', '[outa]',
                            '-c:v', 'libx264', '-c:a', 'aac', '-crf', '18', '-preset', 'medium', '-b:a', '192k', out_file
                        ]
                        r = subprocess.run(cmd, capture_output=True)
                        if r.returncode == 0:
                            made.append(out_file)
                for p in tmp_files:
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
        except Exception:
            pass
    return made


@app.route('/cut_url', methods=['POST'])
def cut_from_url():
    """
    Launch a cutting job directly from a YouTube URL on the GPU host.
    Payload: {
      "url": str,                    # optional if input_path is provided
      "input_path": str?,            # absolute path to an already uploaded file on GPU
      "model_size": str?,
      "to_dir": str?, "out_dir": str?,
      "resize": bool?, "aspect_ratio": [w,h]?,
      "upscale": bool?               # optional, default from env CUT_ENABLE_UPSCALE (default true)
    }
    Returns: {"job_id": int, "status": "processing"}
    """
    global job_counter
    try:
        data = request.get_json()
        print(f"[GPU-CUT] Received cut_url request: {data}")
        url = data.get('url')
        input_path = data.get('input_path')
        provided_title = data.get('title')
        model_size = data.get('model_size') or os.environ.get('WHISPER_MODEL', 'small')
        to_dir = data.get('to_dir') or TO_CUT_DIR
        out_dir = data.get('out_dir') or CUTED_DIR
        resize_flag = bool(data.get('resize') or False)
        aspect = data.get('aspect_ratio') or [9, 16]
        try:
            aspect_tuple = (int(aspect[0]), int(aspect[1])) if isinstance(aspect, (list, tuple)) and len(aspect) == 2 else (9, 16)
        except Exception:
            aspect_tuple = (9, 16)
        # Determine whether to run upscaling step
        upscale_from_req = data.get('upscale') if isinstance(data, dict) else None
        if upscale_from_req is None:
            env_up = os.environ.get('CUT_ENABLE_UPSCALE', '')
            upscale_flag = str(env_up).strip().lower() not in ('0', 'false', 'no')
        else:
            upscale_flag = bool(upscale_from_req)
        # Validate inputs: either input_path exists or we have a URL
        if input_path:
            print(f"[GPU-CUT] Validating input_path: {input_path}")
            if not os.path.isfile(input_path):
                print(f"[GPU-CUT] ERROR: input_path not found: {input_path}")
                return jsonify({"error": f"input_path not found: {input_path}"}), 400
            ok, err = _ffprobe_video_ok(input_path)
            if not ok:
                print(f"[GPU-CUT] ERROR: Invalid input video: {err}")
                return jsonify({"error": f"Invalid input video: {err}"}), 400
            print(f"[GPU-CUT] Input validation successful for: {input_path}")
        elif not url:
            print(f"[GPU-CUT] ERROR: No input_path or url provided")
            return jsonify({"error": "Provide either input_path or url"}), 400
        # Prepare job
        job_counter += 1
        job_id = job_counter
        print(f"[GPU-CUT] Creating job_id={job_id} with model_size={model_size}, resize={resize_flag}, upscale={upscale_flag}")
        jobs[job_id] = {
            "status": "processing",
            "type": "cut",
            "start_time": time.time(),
            "input_path": input_path,
            "to_dir": to_dir,
            "out_dir": out_dir,
            "upscale": upscale_flag
        }
        # Background thread
        print(f"[GPU-CUT] Starting background thread for job_id={job_id}")
        t = threading.Thread(target=process_cut_job, args=(job_id, url, model_size, to_dir, out_dir, resize_flag, aspect_tuple, input_path, provided_title, upscale_flag))
        t.daemon = True
        t.start()
        print(f"[GPU-CUT] Job submitted successfully: job_id={job_id}")
        return jsonify({"job_id": job_id, "status": "processing"}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def process_cut_job(job_id: int, url: str, model_size: str, to_dir: str, out_dir: str, resize_flag: bool, aspect_ratio: tuple[int, int], input_path: str | None = None, title: str | None = None, upscale_flag: bool = True):
    try:
        print(f"[GPU-CUT-{job_id}] Starting cut job processing")
        print(f"[GPU-CUT-{job_id}] Parameters: model_size={model_size}, resize={resize_flag}, aspect_ratio={aspect_ratio}, upscale={upscale_flag}")
        
        # 1) Obtain input path
        if input_path and os.path.isfile(input_path):
            print(f"[GPU-CUT-{job_id}] Using provided input_path: {input_path}")
            video_path = input_path
        else:
            print(f"[GPU-CUT-{job_id}] Downloading video from URL: {url}")
            video_path = _yt_dlp_download(url, to_dir)
            print(f"[GPU-CUT-{job_id}] Download completed: {video_path}")
        if title and isinstance(title, str) and title.strip():
            safe = "".join(c for c in title if c.isalnum() or c in ("_", "-", ".", "!", "?", ":", ",", "'", "&", " ")).rstrip().replace(" ", "_")
            if not safe:
                safe = _safe_name_from_path(video_path)
        else:
            safe = _safe_name_from_path(video_path)
        # Prepare output dir per-video (folder named after source video title)
        dest_dir = os.path.join(out_dir, safe)
        os.makedirs(dest_dir, exist_ok=True)
        # Suffix: first two words from title
        def _first_two_words(name: str) -> str:
            parts = [p for p in name.replace('_', ' ').replace('-', ' ').split() if p]
            return "_".join(parts[:2]) if parts else ""
        clip_suffix = _first_two_words(safe)
        
        # 2) Transcribe
        print(f"[GPU-CUT-{job_id}] Starting transcription with model_size={model_size}")
        print(f"[GPU-CUT-{job_id}] Loading Whisper model...")
        model = _load_whisper_model(model_size)
        print(f"[GPU-CUT-{job_id}] Whisper model loaded successfully")
        
        tr_path = os.path.join(dest_dir, f"{safe}_transcript.json")
        print(f"[GPU-CUT-{job_id}] Transcribing video: {video_path}")
        print(f"[GPU-CUT-{job_id}] Transcript output path: {tr_path}")
        transcript = _transcribe_to_json(model, video_path, tr_path)
        print(f"[GPU-CUT-{job_id}] Transcription completed: {len(transcript)} segments")
        # 3) Ask OpenAI for clips
        print(f"[GPU-CUT-{job_id}] Asking OpenAI for clip suggestions...")
        clips_json_path = os.path.join(dest_dir, f"{safe}_clips.json")
        clips = _ask_openai_for_clips(transcript, clips_json_path)
        print(f"[GPU-CUT-{job_id}] OpenAI returned {len(clips)} clip suggestions")
        
        # 4) Cut
        print(f"[GPU-CUT-{job_id}] Starting clip cutting with ffmpeg...")
        made = _cut_clips_ffmpeg(video_path, clips, dest_dir, clip_suffix=clip_suffix)
        print(f"[GPU-CUT-{job_id}] Cut {len(made)} clips successfully")

        # 5) Optional resize to aspect ratio using clipsai (strict: no fallback). Results must replace original clip files.
        if resize_flag and made:
            print(f"[GPU-CUT-{job_id}] Starting resize to aspect ratio {aspect_ratio}...")
            token = os.environ.get('PYANNOTE_AUTH_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
            if not clipsai_resize:
                raise RuntimeError("clipsai not installed on server, cannot perform speaker-centered resize")
            if not token:
                raise RuntimeError("HUGGINGFACE_TOKEN/PYANNOTE_AUTH_TOKEN is required for speaker-centered resize")
            w, h = aspect_ratio
            import glob, time as _time, shutil as _sh
            for src in made:
                # Run clipsai resize and expect a new mp4 to appear in the same dir
                dirn = os.path.dirname(src)
                before = set(glob.glob(os.path.join(dirn, '*.mp4')))
                t0 = _time.time()
                _ = clipsai_resize(video_file_path=src, pyannote_auth_token=token, aspect_ratio=(w, h))
                # Find a new/updated file
                after = set(glob.glob(os.path.join(dirn, '*.mp4')))
                candidates = [p for p in after if p not in before or os.path.getmtime(p) >= t0]
                if not candidates:
                    raise RuntimeError("clipsai resize did not produce an output file")
                newest = max(candidates, key=lambda p: os.path.getmtime(p))
                # Replace original clip with resized result (atomic move)
                tmp_dst = src + ".resized.tmp.mp4"
                _sh.copy2(newest, tmp_dst)
                os.replace(tmp_dst, src)

        # 6) Optional upscaling of clips in place (write over original filenames inside dest_dir)
        if upscale_flag and made:
            print(f"[GPU-CUT-{job_id}] Starting upscaling of {len(made)} clips...")
            import shutil as _sh
            for src in made:
                name = os.path.basename(src)
                tmp_out = os.path.join(dest_dir, f".{name}.up.tmp.mp4")
                ok = False
                try:
                    ok = upscale_video_with_realesrgan(src, tmp_out)
                except Exception as _e:
                    ok = False
                if not ok or not os.path.exists(tmp_out):
                    raise RuntimeError(f"Upscale failed for {name}")
                # Replace original clip with upscaled clip
                os.replace(tmp_out, src)

        # 7) Zip outputs for download (folder named as source video, files are the final upscaled clips)
        print(f"[GPU-CUT-{job_id}] Creating archive...")
        archive_path = os.path.join(out_dir, f"{safe}.zip")
        import zipfile
        with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            # Always include transcript and clips.json
            for aux in (tr_path, clips_json_path):
                if os.path.exists(aux):
                    zf.write(aux, os.path.relpath(aux, out_dir))
            # Include final clip files (same names as auto mode)
            for p in made:
                if os.path.exists(p):
                    zf.write(p, os.path.relpath(p, out_dir))
        print(f"[GPU-CUT-{job_id}] Job completed successfully!")
        print(f"[GPU-CUT-{job_id}] Output archive: {archive_path}")
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['output_dir'] = dest_dir
        jobs[job_id]['output_archive'] = archive_path
        jobs[job_id]['end_time'] = time.time()
        # Schedule deletion of input video after short delay (if it resides under to_dir)
        try:
            import threading as _th
            def _del():
                import time as _t, os as _os
                _t.sleep(10)
                try:
                    # Delete only if under to_dir
                    if video_path and str(video_path).startswith(str(to_dir)) and _os.path.isfile(video_path):
                        _os.remove(video_path)
                except Exception:
                    pass
            _th.Thread(target=_del, daemon=True).start()
        except Exception:
            pass
    except Exception as e:
        print(f"[GPU-CUT-{job_id}] ERROR: Job failed with exception: {type(e).__name__}: {e}")
        import traceback
        print(f"[GPU-CUT-{job_id}] Traceback:\n{traceback.format_exc()}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['end_time'] = time.time()


@app.route('/cut_job/<int:job_id>', methods=['GET'])
def get_cut_job(job_id: int):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    j = jobs[job_id]
    if j.get('type') != 'cut' and 'output_archive' not in j:
        return jsonify({"error": "Not a cut job"}), 400
    resp = {"job_id": job_id, "status": j.get('status')}
    if 'output_dir' in j:
        resp['output_dir'] = j['output_dir']
    if 'output_archive' in j:
        resp['output_archive'] = j['output_archive']
    if 'error' in j:
        resp['error'] = j['error']
    return jsonify(resp)


@app.route('/clear_queue', methods=['POST'])
def clear_queue():
    """Clear all pending jobs from the queue."""
    global jobs, job_counter
    
    # Count jobs by status
    total = len(jobs)
    pending = sum(1 for j in jobs.values() if j.get('status') in ('queued', 'pending'))
    processing = sum(1 for j in jobs.values() if j.get('status') == 'processing')
    
    # Clear all jobs
    jobs.clear()
    job_counter = 0
    
    return jsonify({
        "ok": True,
        "message": "Queue cleared successfully",
        "cleared": {
            "total": total,
            "pending": pending,
            "processing": processing
        }
    })


@app.route('/queue_status', methods=['GET'])
def queue_status():
    """Get current queue status."""
    status_counts = {}
    for j in jobs.values():
        status = j.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return jsonify({
        "total_jobs": len(jobs),
        "status_counts": status_counts,
        "jobs": [
            {
                "job_id": job_id,
                "status": j.get('status'),
                "type": j.get('type', 'upscale')
            }
            for job_id, j in jobs.items()
        ]
    })

# GPU server processes individual jobs without complex queuing


if __name__ == '__main__':
    print("Starting Video Upscaling/Cutting Server...")
    print("Endpoints:")
    print("  POST /upscale - Submit upscaling job")
    print("  GET /job/<id> - Check job status")
    print("  POST /cut_url - Submit cut-from-URL job")
    print("  GET /cut_job/<id> - Check cut job status")
    print("  GET /health - Health check")

    # Enforce GFPGAN weights presence at startup (project policy)
    _require_gfpgan_on_start()

    # Optional: require CUDA availability at startup
    try:
        require_cuda = str(os.environ.get('CUT_REQUIRE_CUDA', '')).strip().lower() in ('1', 'true', 'yes')
        if require_cuda:
            cs = _cuda_status()
            if not cs.get('cuda_available'):
                print("FATAL: CUT_REQUIRE_CUDA=1 but torch.cuda.is_available() is False. Install CUDA-enabled torch and GPU drivers.")
                sys.exit(1)
            else:
                print("CUDA OK:", cs)
    except Exception:
        pass

    # GPU server ready - processes jobs as they come
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=False)
