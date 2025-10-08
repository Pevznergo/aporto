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

app = Flask(__name__)

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

def _require_gfpgan_on_start():
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, 'models', 'GFPGANv1.4.pth')
    if not os.path.isfile(path):
        print(f"FATAL: Required GFPGAN weights not found: {path}. Place GFPGANv1.4.pth in models/ and restart.")
        sys.exit(1)

# ==== Cutting/transcription helpers ====

def _load_whisper_model(model_size: str):
    if whisper is None:
        raise RuntimeError("whisper not installed on server")
    m = whisper.load_model(model_size)
    if torch is not None and torch.cuda.is_available():
        m = m.to('cuda')
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
        url,
    ]
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
    client = OpenAI(api_key=api_key)
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

OUTPUT FORMAT - JSON array with EXACTLY this structure:
[
  {{
    "short_id": 1,
    "title": "Catchy Title With Emoji",
    "duration_estimate": "18 sec",
    "fragments": [
      {{ "start": "00:05:23.100", "end": "00:05:28.400", "text": "exact text", "visual_suggestion": "idea" }}
    ],
    "hook_strength": "high/medium/low",
    "why_it_works": "Brief"
  }}
]
Return ONLY the valid JSON array. No other text.

Here is the transcript:
{json.dumps(transcript, ensure_ascii=False)}
"""
    try:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.choices[0].message.content or "[]"
    except Exception as e:
        content = "[]"
    with open(out_json, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _safe_name_from_path(path: str) -> str:
    base = os.path.splitext(os.path.basename(path))[0]
    safe = "".join(c for c in base if c.isalnum() or c in ("_", "-", ".", " ")).strip().replace(" ", "_")
    return safe or base


def _cut_clips_ffmpeg(video_path: str, clips: list, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for i, clip in enumerate(clips, start=1):
        title = clip.get('title') or f'clip{i}'
        safe_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", ".", "!", "?", ":", ",", "'", "&", " ")).rstrip().replace(" ", "_")
        out_file = os.path.join(out_dir, f"clip_{i}_{safe_title}.mp4")
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
    Payload: {"url": str, "model_size": str?, "to_dir": str?, "out_dir": str?}
    Returns: {"job_id": int, "status": "processing"}
    """
    global job_counter
    try:
        data = request.get_json()
        url = data.get('url')
        model_size = data.get('model_size') or os.environ.get('WHISPER_MODEL', 'small')
        to_dir = data.get('to_dir') or TO_CUT_DIR
        out_dir = data.get('out_dir') or CUTED_DIR
        if not url:
            return jsonify({"error": "Missing url"}), 400
        # Prepare job
        job_counter += 1
        job_id = job_counter
        jobs[job_id] = {"status": "processing", "type": "cut", "start_time": time.time()}
        # Background thread
        t = threading.Thread(target=process_cut_job, args=(job_id, url, model_size, to_dir, out_dir))
        t.daemon = True
        t.start()
        return jsonify({"job_id": job_id, "status": "processing"}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def process_cut_job(job_id: int, url: str, model_size: str, to_dir: str, out_dir: str):
    try:
        # 1) Download
        video_path = _yt_dlp_download(url, to_dir)
        safe = _safe_name_from_path(video_path)
        # Prepare output dir per-video
        dest_dir = os.path.join(out_dir, safe)
        os.makedirs(dest_dir, exist_ok=True)
        # 2) Transcribe
        model = _load_whisper_model(model_size)
        tr_path = os.path.join(dest_dir, f"{safe}_transcript.json")
        transcript = _transcribe_to_json(model, video_path, tr_path)
        # 3) Ask OpenAI for clips
        clips_json_path = os.path.join(dest_dir, f"{safe}_clips.json")
        clips = _ask_openai_for_clips(transcript, clips_json_path)
        # 4) Cut
        made = _cut_clips_ffmpeg(video_path, clips, dest_dir)
        # 5) Zip outputs for download
        archive_path = os.path.join(out_dir, f"{safe}.zip")
        import zipfile
        with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(dest_dir):
                for f in files:
                    p = os.path.join(root, f)
                    arcname = os.path.relpath(p, out_dir)
                    zf.write(p, arcname)
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['output_dir'] = dest_dir
        jobs[job_id]['output_archive'] = archive_path
        jobs[job_id]['end_time'] = time.time()
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['end_time'] = time.time()


@app.route('/cut_job/<int:job_id>', methods=['GET'])
def get_cut_job(job_id: int):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    j = jobs[job_id]
    if j.get('type') != 'cut' and 'output_archive' not in j:
        # not a cut job
        return jsonify({"error": "Not a cut job"}), 400
    resp = {"job_id": job_id, "status": j.get('status')}
    if 'output_dir' in j:
        resp['output_dir'] = j['output_dir']
    if 'output_archive' in j:
        resp['output_archive'] = j['output_archive']
    if 'error' in j:
        resp['error'] = j['error']
    return jsonify(resp)


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
    
    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=False)
