import os
import json
import ssl
import subprocess
import whisper
import torch
from openai import OpenAI
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from sqlmodel import Session
from .db import engine
from .models import Clip, ClipFragment


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

    def ask_gpt(self, transcript: List[Dict[str, Any]], clips_path: str, video_title: Optional[str] = None) -> List[Dict[str, Any]]:
        """Send transcript to GPT for clip selection"""
        import logging
        logging.info(f"[GPT] Preparing to ask OpenAI for clips, transcript segments: {len(transcript)}")
        
        # Extract guest name from video title if available
        guest_name_instruction = ""
        if video_title:
            guest_name_instruction = f"""
IMPORTANT - GUEST NAME USAGE:
The original video title is: "{video_title}"

Before creating titles, identify the guest's name from the video title above.
Then follow these rules:
1. Use the guest's actual name at the BEGINNING of the title or description (instead of "He", "She", "They") to establish context
2. After the first mention with the guest's name, you can use pronouns (he/she/they) in subsequent sentences
3. This creates natural flow: start with the name for clarity, then use pronouns

Example: Instead of "She Reveals Her Secret" → "[Guest Name] Reveals Her Secret"
Example: Instead of "How He Built His Empire" → "[Guest Name]: How He Built His Empire" 
Example for description: "[Guest Name] talks about his journey. He explains how he overcame..." (name first, then pronouns)
"""
        
        prompt = f"""
You are an expert video editor and storyteller, specializing in creating viral YouTube Shorts from interview content. Your goal is to find and condense complete mini-stories from the transcript.{guest_name_instruction}

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
If a fragment refers to “he,” “she,” “they,” or “it,” ensure that earlier in the cut there is clear context establishing who or what is meant.
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
            logging.info(f"[GPT] Calling OpenAI API with model: {model_name}")
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            clips_json = response.choices[0].message.content or "[]"
            logging.info(f"[GPT] Received response from OpenAI, length: {len(clips_json)} chars")
            logging.info(f"[GPT] Response preview: {clips_json[:200]}...")
        except Exception as e:
            logging.error(f"[GPT] ERROR calling OpenAI API: {type(e).__name__}: {e}", exc_info=True)
            clips_json = "[]"
        
        # Save raw response
        logging.info(f"[GPT] Saving response to: {clips_path}")
        with open(clips_path, "w", encoding="utf-8") as f:
            f.write(clips_json)
        
        # Parse and return
        try:
            logging.info(f"[GPT] Parsing JSON response...")
            clips_data = json.loads(clips_json)
            if isinstance(clips_data, list):
                logging.info(f"[GPT] Successfully parsed {len(clips_data)} clips from response")
                return clips_data
            else:
                logging.warning(f"[GPT] WARNING: Response is not a list, got type: {type(clips_data)}")
                return []
        except Exception as e:
            logging.error(f"[GPT] ERROR parsing JSON response: {type(e).__name__}: {e}")
            logging.error(f"[GPT] Raw content: {clips_json[:500]}...")
            return []

    def cut_clips(self, video_path: str, clips: List[Dict[str, Any]], output_dir: str, on_progress=None, clip_suffix: str = "") -> List[str]:
        """Cut clips using ffmpeg, return list of created clip paths.
        on_progress(i, total) can be provided to track progress.
        clip_suffix: additional suffix to append at the end of each clip filename (already sanitized).
        """
        os.makedirs(output_dir, exist_ok=True)
        created_clips = []
        total = max(len(clips), 1)
        
        for i, clip in enumerate(clips, start=1):
            title = clip.get("title", f"clip{i}")
            safe_title = "".join(c for c in title if c.isalnum() or c in ("_", "-", ".", "!", "?", ":", ",", "'", "&", " ")).rstrip()
            safe_title = safe_title.replace(" ", "_")
            suffix = f"_{clip_suffix}" if clip_suffix else ""
            out_file = os.path.join(output_dir, f"clip_{i}_{safe_title}{suffix}.mp4")
            
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
                        # Build concat filter - all fragments from same source, so should have same resolution
                        # Just ensure SAR consistency
                        input_args = []
                        concat_parts = []
                        for idx, temp_file in enumerate(valid_temps):
                            input_args.extend(["-i", temp_file])
                            concat_parts.append(f"[{idx}:v][{idx}:a]")
                        
                        filter_complex = f"{''.join(concat_parts)}concat=n={len(valid_temps)}:v=1:a=1[outv][outa]"
                        
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
                        if on_progress:
                            try:
                                on_progress(i, total)
                            except Exception:
                                pass
                    elif len(valid_temps) == 1:
                        # Single valid temp
                        import shutil
                        shutil.copy2(valid_temps[0], out_file)
                        created_clips.append(out_file)
                    
                    if on_progress:
                        try:
                            on_progress(i, total)
                        except Exception:
                            pass
                    
                    # Cleanup temp files
                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            
            except Exception as e:
                print(f"Error creating clip {i}: {e}")
        
        return created_clips

    def save_clips_to_db(self, task_id: int, clips: List[Dict[str, Any]], clip_files: List[str]) -> None:
        """Save clip data with titles/descriptions to database"""
        with Session(engine) as session:
            # Map clip files by their short_id for easy lookup
            clip_file_map = {}
            for file_path in clip_files:
                # Extract clip number from filename (e.g., "clip_1_Some_Title.mp4" -> 1)
                filename = os.path.basename(file_path)
                if filename.startswith("clip_"):
                    try:
                        clip_num = int(filename.split("_")[1])
                        clip_file_map[clip_num] = file_path
                    except (IndexError, ValueError):
                        continue
            
            # Save each clip with its fragments
            for clip_data in clips:
                short_id = clip_data.get("short_id", 0)
                title = clip_data.get("title", f"Clip {short_id}")
                description = clip_data.get("description", "")
                duration_estimate = clip_data.get("duration_estimate", None)
                hook_strength = clip_data.get("hook_strength", None)
                why_it_works = clip_data.get("why_it_works", None)
                file_path = clip_file_map.get(short_id)
                
                # Create clip record
                clip = Clip(
                    task_id=task_id,
                    short_id=short_id,
                    title=title,
                    description=description,
                    duration_estimate=duration_estimate,
                    hook_strength=hook_strength,
                    why_it_works=why_it_works,
                    file_path=file_path
                )
                session.add(clip)
                session.commit()
                session.refresh(clip)
                
                # Save fragments
                fragments = clip_data.get("fragments", [])
                for order, fragment_data in enumerate(fragments):
                    fragment = ClipFragment(
                        clip_id=clip.id,
                        start_time=fragment_data.get("start", ""),
                        end_time=fragment_data.get("end", ""),
                        text=fragment_data.get("text", ""),
                        visual_suggestion=fragment_data.get("visual_suggestion"),
                        order=order
                    )
                    session.add(fragment)
                
                session.commit()

    def process_auto_task(
        self, 
        video_path: str, 
        output_dir: str,
        task_id: Optional[int] = None,
        video_title: Optional[str] = None
    ) -> Tuple[str, str, List[str]]:
        """
        Complete auto processing pipeline.
        Returns (transcript_path, clips_json_path, clip_files)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        transcript_path = os.path.join(output_dir, f"{base_name}_transcript.json")
        clips_json_path = os.path.join(output_dir, f"{base_name}_clips.json")

        # Compute suffix: first two words from base video title
        def _first_two_words(name: str) -> str:
            # replace separators with spaces, then split
            cleaned = name.replace("_", " ").replace("-", " ")
            parts = [p for p in cleaned.split() if p]
            return "_".join(parts[:2]) if parts else ""
        clip_suffix = _first_two_words(base_name)
        
        # 1. Transcribe
        transcript = self.transcribe_video(video_path, transcript_path)
        
        # 2. Get clips from GPT
        clips = self.ask_gpt(transcript, clips_json_path, video_title=video_title)
        
        # 3. Cut clips (append first two words of source title to each filename)
        clip_files = self.cut_clips(video_path, clips, output_dir, clip_suffix=clip_suffix)
        
        # 4. Save clips to database if task_id is provided
        if task_id is not None:
            self.save_clips_to_db(task_id, clips, clip_files)
        
        return transcript_path, clips_json_path, clip_files
