# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Two-part app: FastAPI backend (Python) and Next.js frontend (TypeScript).
- Workflow: tasks move through a download queue (yt-dlp) and a processing queue (ffmpeg or Whisper+OpenAI) with one downloader and one processor thread running concurrently.
- Storage: SQLite (SQLModel) at app.db; raw videos in videos/; auto-mode outputs in clips/<video_basename>/.
- Static mounts: backend serves /videos and /clips for downloaded and processed files.

Prereqs
- macOS: brew install ffmpeg
- Python 3.10+ and Node.js 18+

Environment
- Backend .env (repo root):
  - OPENAI_API_KEY – required for auto mode
  - OPENAI_MODEL – optional, default gpt-4o-mini
  - WHISPER_MODEL – optional, default small
  - CORS_ORIGINS – optional, defaults to http://localhost:3000,http://127.0.0.1:3000
- Frontend web/.env.local (copy from web/.env.local.example):
  - NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000

Common commands
- Backend (FastAPI)
  - Create venv and install deps
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
  - Run dev server
    ```bash
    uvicorn app.main:app --reload
    ```
  - Reset local DB schema (dev only)
    ```bash
    rm -f app.db
    ```

- Frontend (Next.js in web/)
  - Install deps
    ```bash
    cd web && npm install
    ```
  - Dev server
    ```bash
    npm run dev
    ```
  - Build and start
    ```bash
    npm run build
    npm start
    ```
  - Lint
    ```bash
    npm run lint
    ```

Backend architecture
- Entry: app/main.py
  - Loads .env if python-dotenv is installed (already in requirements).
  - CORS configured via CORS_ORIGINS.
  - Startup event initializes DB and starts two daemon threads (downloader, processor).
  - Routes:
    - GET / returns server-side rendered Jinja UI (optional during dev).
    - GET /api/tasks – list tasks.
    - GET /api/tasks/{id} – task details.
    - POST /api/tasks – create task: { url, mode: 'simple'|'auto', start, end }.
    - POST /api/tasks/{id}/retry – requeue failed task.
- Data: app/models.py with Task (SQLModel) and TaskStatus lifecycle: queued_download → downloading → queued_process → processing → done|error.
- DB: app/db.py sets up SQLite engine and session; tables auto-created on startup.
- Workers: app/worker.py
  - Queues: download_queue and process_queue.
  - Download: app/ytdlp_wrapper.py saves raw file to videos/ as <id>.<ext>.
  - Simple processing: app/ffmpeg_wrapper.py trims by start/end into videos/<base>_cut.mp4.
  - Auto processing: app/auto_pipeline.py
    - Transcribe with Whisper (model size via WHISPER_MODEL; local model cache in whisper_models/).
    - Ask OpenAI (model via OPENAI_MODEL) for clip plan.
    - Cut clips with ffmpeg to clips/<base>/ and save transcript and clips JSON alongside.

Frontend architecture
- Next.js 14 (app router) under web/src/app.
- page.tsx drives UI:
  - Creates tasks via POST /api/tasks, polls GET /api/tasks every 3s.
  - Renders links to videos/, clips/, transcript JSON, and generated clips JSON served by backend.
- next.config.mjs: minimal; tsconfig present.

Conventions and directories
- videos/ – raw downloads and simple-mode outputs (served at /videos).
- clips/ – auto-mode outputs per video (served at /clips). Each folder contains transcript JSON, clips JSON, and .mp4 clips.

Notes and pitfalls
- Auto mode requires OPENAI_API_KEY and will download Whisper model on first run; this can take time.
- If you change Task fields during development, remove app.db and restart to re-create tables.
- Ensure ffmpeg is on PATH and yt-dlp is available (installed via requirements).
