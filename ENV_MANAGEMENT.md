# Environment Variables Management

Это руководство объясняет как правильно управлять переменными окружения в проекте aporto.

## Проблема

Переменные окружения из `.env` файла загружаются только в Python приложение через `python-dotenv`, но не доступны в shell окружении. Это может вызвать путаницу при отладке и использовании утилит командной строки.

## Решение

### 1. Загрузка переменных в shell

```bash
# Загрузить переменные из .env в текущую сессию shell
source load_env.sh

# Проверить что переменные загружены
echo $UPSCALE_CONCURRENCY
echo $VAST_INSTANCE_ID
```

### 2. Запуск приложения с автоматической загрузкой .env

```bash
# Запустить backend с автоматической загрузкой переменных
./start_backend_with_env.sh
```

Этот скрипт:
- Загружает все переменные из `.env`
- Проверяет ключевые переменные
- Запускает uvicorn с правильным окружением
- Выводит диагностическую информацию

### 3. Проверка переменных окружения

```bash
# Проверить все переменные (требует .venv)
.venv/bin/python check_env.py

# Или если активировано виртуальное окружение
python check_env.py
```

### 4. Очистка старых файлов конфигурации

В новой версии JSON файлы настроек больше не используются - всё управляется через `.env`.

```bash
# Удалить старые файлы конфигурации (upscale_settings.json и др.)
python cleanup_old_config.py
```

## Архитектура переменных окружения

### 1. Python приложение (app/main.py)
- Загружает `.env` автоматически через `python-dotenv`
- Переменные доступны через `os.getenv()`

### 2. Shell окружение
- `.env` файл **НЕ** загружается автоматически
- Нужно явно загружать через `source load_env.sh`

### 3. Простое управление конфигурацией
- Все настройки хранятся только в .env файле
- Никаких JSON файлов конфигурации
- Настройки применяются немедленно при запуске

## Переменные по категориям

### OpenAI Configuration
- `OPENAI_API_KEY` (обязательно)
- `OPENAI_MODEL` (по умолчанию: gpt-4o-mini)

### VAST.ai Configuration
- `VAST_API_KEY` (обязательно)
- `VAST_INSTANCE_ID` (обязательно)
- `VAST_SSH_HOST` (обязательно)
- `VAST_SSH_PORT` (обязательно)
- `VAST_SSH_USER` (по умолчанию: root)
- `VAST_UPSCALE_URL` (опционально)

### Upscale Configuration
- `UPSCALE_CONCURRENCY` (по умолчанию: 2)
- `UPSCALE_UPLOAD_CONCURRENCY` (по умолчанию: 1)
- `UPSCALE_RESULT_DOWNLOAD_CONCURRENCY` (по умолчанию: 1)

## Рекомендуемый workflow

1. **При изменении .env:**
   ```bash
   # Просто перезапустить приложение
   ./start_backend_with_env.sh
   ```

2. **При отладке:**
   ```bash
   # 1. Проверить переменные
   .venv/bin/python check_env.py
   
   # 2. Загрузить в shell для ручного тестирования
   source load_env.sh
   echo $UPSCALE_CONCURRENCY
   ```

3. **При деплое на сервер:**
   ```bash
   # На сервере после git pull:
   python cleanup_old_config.py  # только при первом обновлении
   ./start_backend_with_env.sh
   ```

4. **При первом обновлении с JSON настроек:**
   ```bash
   # Удалить старые JSON файлы
   python cleanup_old_config.py
   ```

## Типичные проблемы

### 1. "echo $VAR" возвращает пустое значение
**Причина:** Переменная не загружена в shell  
**Решение:** `source load_env.sh`

### 2. Приложение не видит новые переменные
**Причина:** Нужен перезапуск  
**Решение:** `./start_backend_with_env.sh`

### 3. API /api/upscale/settings возвращает старые данные
**Причина:** Остались старые JSON файлы  
**Решение:** `python cleanup_old_config.py`
