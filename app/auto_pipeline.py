import os
import json
import ssl
import subprocess
import whisper
import torch
from openai import OpenAI
from datetime import datetime
from typing import Any, Dict, List, Tuple


ssl._create_default_https_context = ssl._create_unverified_context


class AutoPipeline:
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
        self.model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "whisper_models")
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Load Whisper model with FP32 for CPU
        self.model = whisper.load_model(model_size, download_root=self.model_dir).to(torch.float32)
        
        # OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)

    def transcribe_video(self, video_path: str, transcript_path: str) -> List[Dict[str, Any]]:
        """Transcribe video using Whisper and save to JSON"""
        result = self.model.transcribe(video_path, language="en", fp16=False)
        segments = result["segments"]
        transcript = [
            {"start": s["start"], "end": s["end"], "text": s["text"]}
            for s in segments
        ]
        
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        return transcript

    def ask_gpt(self, transcript: List[Dict[str, Any]], clips_path: str) -> List[Dict[str, Any]]:
        """Send transcript to GPT for clip selection"""
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
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            clips_json = response.choices[0].message.content or "[]"
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            clips_json = "[]"
        
        # Save raw response
        with open(clips_path, "w", encoding="utf-8") as f:
            f.write(clips_json)
        
        # Parse and return
        try:
            clips_data = json.loads(clips_json)
            return clips_data if isinstance(clips_data, list) else []
        except Exception:
            return []

    def cut_clips(self, video_path: str, clips: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """Cut clips using ffmpeg, return list of created clip paths"""
        os.makedirs(output_dir, exist_ok=True)
        created_clips = []
        
        for i, clip in enumerate(clips, start=1):
            title = clip.get("title", f"clip{i}")
            safe_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", ".", "!", "?", ":", ",", "'", "&", " ")).rstrip()
            safe_title = safe_title.replace(" ", "_")
            out_file = os.path.join(output_dir, f"clip_{i}_{safe_title}.mp4")
            
            fragments = clip.get("fragments", [])
            if not fragments:
                continue
            
            try:
                if len(fragments) == 1:
                    # Single fragment
                    fragment = fragments[0]
                    start_ts = fragment["start"]
                    end_ts = fragment["end"]
                    
                    cmd = [
                        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", video_path,
                        "-ss", start_ts, "-to", end_ts,
                        "-c:v", "libx264", "-c:a", "aac",
                        "-crf", "18", "-preset", "medium", "-b:a", "192k",
                        "-avoid_negative_ts", "make_zero", "-fflags", "+genpts",
                        out_file
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        created_clips.append(out_file)
                else:
                    # Multiple fragments - extract and concatenate
                    temp_files = []
                    for j, fragment in enumerate(fragments):
                        temp_file = os.path.join(output_dir, f"temp_clip_{i}_{j}.mp4")
                        temp_files.append(temp_file)
                        
                        cmd = [
                            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                            "-i", video_path,
                            "-ss", fragment["start"], "-to", fragment["end"],
                            "-c:v", "libx264", "-c:a", "aac",
                            "-crf", "18", "-preset", "medium", "-b:a", "192k",
                            "-avoid_negative_ts", "make_zero", "-fflags", "+genpts",
                            temp_file
                        ]
                        subprocess.run(cmd, capture_output=True)
                    
                    # Concatenate valid temp files
                    valid_temps = [f for f in temp_files if os.path.exists(f)]
                    if len(valid_temps) > 1:
                        # Build concat filter
                        input_args = []
                        concat_inputs = []
                        for idx, temp_file in enumerate(valid_temps):
                            input_args.extend(["-i", temp_file])
                            concat_inputs.append(f"[{idx}:v][{idx}:a]")
                        
                        filter_complex = f"{''.join(concat_inputs)}concat=n={len(valid_temps)}:v=1:a=1[outv][outa]"
                        
                        cmd = [
                            "ffmpeg", "-y"
                        ] + input_args + [
                            "-filter_complex", filter_complex,
                            "-map", "[outv]", "-map", "[outa]",
                            "-c:v", "libx264", "-c:a", "aac",
                            "-crf", "18", "-preset", "medium", "-b:a", "192k",
                            out_file
                        ]
                        result = subprocess.run(cmd, capture_output=True)
                        if result.returncode == 0:
                            created_clips.append(out_file)
                    elif len(valid_temps) == 1:
                        # Single valid temp
                        import shutil
                        shutil.copy2(valid_temps[0], out_file)
                        created_clips.append(out_file)
                    
                    # Cleanup temp files
                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            
            except Exception as e:
                print(f"Error creating clip {i}: {e}")
        
        return created_clips

    def process_auto_task(
        self, 
        video_path: str, 
        output_dir: str
    ) -> Tuple[str, str, List[str]]:
        """
        Complete auto processing pipeline.
        Returns (transcript_path, clips_json_path, clip_files)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        transcript_path = os.path.join(output_dir, f"{base_name}_transcript.json")
        clips_json_path = os.path.join(output_dir, f"{base_name}_clips.json")
        
        # 1. Transcribe
        transcript = self.transcribe_video(video_path, transcript_path)
        
        # 2. Get clips from GPT
        clips = self.ask_gpt(transcript, clips_json_path)
        
        # 3. Cut clips
        clip_files = self.cut_clips(video_path, clips, output_dir)
        
        return transcript_path, clips_json_path, clip_files