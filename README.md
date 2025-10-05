# Video Cutter Task Manager

Веб‑сервис c API на FastAPI и фронтендом на Next.js. Возможности:
- Скачивание видео с YouTube (yt-dlp) в папку `videos/` по очереди (один загрузчик).
- Обрезка: 
  - simple: один непрерывный фрагмент по start/end (один обработчик).
  - auto: авто‑подбор клипов через Whisper+GPT (транскрипция → GPT → нарезка/склейка) в папку `clips/<basename>/`.
- Скачивание и обработка идут параллельно (один загрузчик + один обработчик одновременно).
- Веб‑UI на Next.js для добавления/контроля задач.

## Требования
- Python 3.10+
- Node.js 18+
- FFmpeg

Установка FFmpeg (macOS):

```bash
brew install ffmpeg
```

## Настройка окружения
- Установите переменные окружения для бэкенда:
  - OPENAI_API_KEY (обязателен для auto режима)
  - OPENAI_MODEL (опционально, по умолчанию gpt-4o-mini)
  - WHISPER_MODEL (опционально, по умолчанию small)
- Для фронтенда:
  - скопируйте web/.env.local.example в web/.env.local и при необходимости измените NEXT_PUBLIC_API_BASE_URL

## Установка и запуск

Бэкенд (FastAPI):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API будет доступно на http://127.0.0.1:8000

Фронтенд (Next.js):
```bash
cd web
npm install
npm run dev
```
UI будет доступен на http://127.0.0.1:3000

## Использование
- В UI выберите режим simple (укажите start/end) или auto (Whisper+GPT).
- Ссылки на скачанные и обработанные файлы отображаются в таблице.
- Для режима auto результаты и артефакты лежат в `clips/<basename>/`.

## Примечания
- Если схема БД изменилась (мы добавили новые поля), при разработке проще удалить app.db и перезапустить сервер, чтобы таблицы пересоздались.
- Whisper и Torch могут долго устанавливаться и скачивать модель при первом запуске.
- yt-dlp и ffmpeg должны быть доступны в PATH.
