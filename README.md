# Video Cutter Task Manager

Короткое руководство по запуску (backend FastAPI + frontend Next.js).

## Требования
- Python 3.10+
- Node.js 18+
- FFmpeg

Установка FFmpeg (macOS):
```bash
brew install ffmpeg
```

## Переменные окружения (.env)
Создайте файл `.env` в корне репозитория. Переменные автоматически загружаются при старте бэкенда (используется python-dotenv, уже в requirements):
```
OPENAI_API_KEY=ваш_ключ_openai
OPENAI_MODEL=gpt-4o-mini    # опционально
WHISPER_MODEL=small         # опционально (размер модели Whisper)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000  # опционально
```

Для фронтенда создайте `web/.env.local` (можно скопировать из `web/.env.local.example`):
```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Установка зависимостей
Бэкенд (из корня репозитория):
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Фронтенд (Next.js в каталоге web/):
```bash
cd web
npm install
```

## Запуск
Бэкенд (FastAPI):
```bash
# убедитесь, что активирован .venv
source .venv/bin/activate
# запускайте через интерпретатор venv, чтобы избежать путаницы с разными uvicorn
python -m uvicorn app.main:app --reload
# API: http://127.0.0.1:8000
```

Фронтенд (Next.js):
```bash
cd web
npm run dev
# UI: http://127.0.0.1:3000
```

## Что делает приложение
- Скачивание видео с YouTube (yt-dlp) в `videos/` (очередь загрузки, один поток).
- Обработка:
  - simple: обрезка одним куском по `start/end` в `videos/<basename>_cut.mp4`.
  - auto: транскрипция (Whisper) → план клипов (OpenAI) → нарезка/склейка в `clips/<basename>/` (+ JSON с транскриптом и клипами).
- Загрузка и обработка идут параллельно (по одному потоку на каждую очередь).
- Бэкенд отдаёт статику: `/videos` и `/clips`.

## Использование
1) Запустите бэкенд и фронтенд (см. выше).
2) В UI выберите режим simple (укажите start/end) или auto.
3) Ссылки на скачанные/обработанные файлы доступны в таблице.

## Полезные команды
- Сброс локальной БД (dev):
```bash
rm -f app.db
```
- Линт фронтенда:
```bash
cd web
npm run lint
```
- Сборка фронтенда:
```bash
cd web
npm run build
npm start
```

## Тонкости и частые проблемы
- Если видите `ModuleNotFoundError: sqlmodel`, запустите сервер так, чтобы использовался Python из `.venv`:
```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```
- Whisper при первом запуске скачивает модель — это может занять время.
- ffmpeg и yt-dlp должны быть доступны в PATH.
