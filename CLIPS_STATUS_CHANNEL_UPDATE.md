# Добавление полей Status и Channel для клипов

## Что было сделано

Добавлена возможность устанавливать статус (Published/Cancelled) и канал (1/2/3/4) для каждого клипа на вкладке Clips.

### Изменения в коде:

1. **Backend (Python/FastAPI)**:
   - `app/models.py` - добавлены поля `status` и `channel` в модель `Clip`
   - `app/main.py` - обновлен endpoint `GET /api/clips` для возврата новых полей
   - `app/main.py` - добавлен новый endpoint `PATCH /api/clips/{clip_id}` для обновления клипа

2. **Frontend (Next.js/React)**:
   - `web/src/lib/api.ts` - добавлена функция `updateClip()`
   - `web/src/app/page.tsx` - подключены обработчики onChange для селектов статуса и канала

3. **Database Migration**:
   - `migrate_add_clip_fields.py` - скрипт миграции для добавления полей в БД

## Как применить изменения

### 1. Применить миграцию базы данных

```bash
# Перейти в корневую папку проекта
cd /path/to/aporto

# Запустить миграцию
python3 migrate_add_clip_fields.py
```

Скрипт автоматически определит тип БД (PostgreSQL или SQLite) и добавит необходимые колонки.

### 2. Перезапустить backend

```bash
# Если используется systemd
sudo systemctl restart aporto-api

# Или если запущено вручную
# Остановить текущий процесс (Ctrl+C)
# Запустить заново
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Перезапустить frontend (если используется dev режим)

```bash
cd web
npm run dev
```

Если используется production build, пересобрать:

```bash
cd web
npm run build
npm run start
```

## Использование

1. Откройте вкладку **Clips** в веб-интерфейсе
2. Для каждого клипа доступны два селекта:
   - **Status**: выбор статуса (Published, Cancelled или пусто)
   - **Channel**: выбор канала (1, 2, 3, 4 или пусто)
3. При изменении значения данные **автоматически сохраняются** в БД
4. Можно фильтровать клипы по статусу и каналу

## Проверка

После применения изменений проверьте:

```bash
# Проверка структуры таблицы (SQLite)
sqlite3 app.db "PRAGMA table_info(clip);"

# Проверка структуры таблицы (PostgreSQL)
psql $POSTGRES_URL -c "\d clip"
```

Должны быть видны поля `status` и `channel`.

## API

### Получить список клипов
```http
GET /api/clips
```

Response включает новые поля:
```json
{
  "id": 1,
  "task_id": 123,
  "short_id": 1,
  "title": "Название клипа",
  "description": "Описание",
  "status": "Published",
  "channel": "1",
  "file_path": "/path/to/clip.mp4",
  "created_at": "2025-10-27T10:00:00",
  "fragments": []
}
```

### Обновить клип
```http
PATCH /api/clips/{clip_id}
Content-Type: application/json

{
  "status": "Published",
  "channel": "2"
}
```

Response:
```json
{
  "id": 1,
  "status": "Published",
  "channel": "2",
  "message": "Clip updated successfully"
}
```

## Troubleshooting

### Ошибка: "column status already exists"
Поля уже добавлены. Миграция безопасна для повторного запуска.

### Ошибка: "Failed to update clip status"
Проверьте:
1. Backend запущен и доступен
2. CORS настроены правильно
3. В консоли браузера (F12) нет ошибок сети

### Селекты не сохраняют значения
Проверьте:
1. Миграция применена: `python3 migrate_add_clip_fields.py`
2. Backend перезапущен после применения миграции
3. В консоли браузера нет ошибок JavaScript

## Откат изменений

Если нужно откатить изменения:

```sql
-- SQLite
ALTER TABLE clip DROP COLUMN status;
ALTER TABLE clip DROP COLUMN channel;

-- PostgreSQL
ALTER TABLE clip DROP COLUMN IF EXISTS status;
ALTER TABLE clip DROP COLUMN IF EXISTS channel;
```

Или используйте git для отката кода:
```bash
git checkout HEAD~1 app/models.py app/main.py web/src/lib/api.ts web/src/app/page.tsx
```
