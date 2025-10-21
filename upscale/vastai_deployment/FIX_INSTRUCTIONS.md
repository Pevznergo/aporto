# VAST Deployment Fix Instructions

## Проблема
- Сервер использовал неправильный Python интерпретатор (`/venv/main/bin/python3`)
- `basicsr` имеет несовместимость с `torchvision>=0.19` (импорт из `functional_tensor`)

## Что исправлено в локальных файлах

### 1. `requirements.txt`
- Закреплены версии: `torch==2.4.1`, `torchvision==0.19.1`, `torchaudio==2.4.1`

### 2. `upscale_app.py`
- Добавлена поддержка переменной `VENV_PYTHON` для subprocess вызовов
- Теперь использует правильный интерпретатор из проектного venv

### 3. `install.sh`
- Добавляет `VENV_PYTHON=/workspace/aporto/.venv/bin/python` в `.env`
- Автоматически патчит `basicsr` после установки

### 4. Новые скрипты
- `diagnose.sh` - диагностика текущего состояния сервера
- `apply_fix.sh` - применение исправлений на сервере
- `fix_basicsr.sh` - патч только basicsr
- `hotfix_venv.sh` - быстрое исправление venv проблемы

## Как применить исправления

### Шаг 1: Закоммитьте и запушьте изменения

```bash
cd /Users/igortkachenko/Downloads/aporto
git add .
git commit -m "Fix: VAST deployment venv and basicsr compatibility"
git push origin main
```

### Шаг 2: На VAST сервере выполните

```bash
# Подключитесь по SSH
ssh -p 27281 root@116.102.175.41

# Перейдите в проект
cd /workspace/aporto

# Получите изменения
git pull origin main

# Запустите диагностику (опционально)
bash upscale/vastai_deployment/diagnose.sh

# Примените исправления
bash upscale/vastai_deployment/apply_fix.sh
```

### Шаг 3: Проверьте работу

```bash
# Проверьте статус сервиса
systemctl status vast-upscale.service

# Следите за логами
tail -f /workspace/server.log

# Проверьте health endpoint
curl http://localhost:5000/health
```

## Что делает apply_fix.sh

1. ✅ Находит и патчит `basicsr/data/degradations.py`
2. ✅ Добавляет `VENV_PYTHON` в `.env` если отсутствует
3. ✅ Тестирует импорты в правильном venv
4. ✅ Перезапускает сервис
5. ✅ Проверяет что сервис запущен

## Ручное исправление (если нужно)

Если автоматический скрипт не работает:

```bash
cd /workspace/aporto

# 1. Найти файл basicsr
DEGRADATIONS=$(find .venv -name "degradations.py" -path "*/basicsr/data/degradations.py" | head -n1)
echo "File: $DEGRADATIONS"

# 2. Патч
cp "$DEGRADATIONS" "$DEGRADATIONS.bak"
sed -i 's/functional_tensor/functional/g' "$DEGRADATIONS"

# 3. Добавить в .env
echo "VENV_PYTHON=/workspace/aporto/.venv/bin/python" >> .env

# 4. Перезапуск
systemctl restart vast-upscale.service
```

## Проверка после исправления

В логах должны появиться строки с правильным Python:
```
Command: /workspace/aporto/.venv/bin/python /workspace/aporto/vendor/realesrgan_infer.py ...
```

Вместо старого:
```
Command: /venv/main/bin/python3 /workspace/aporto/vendor/realesrgan_infer.py ...
```

## Troubleshooting

### Если сервис не стартует
```bash
journalctl -u vast-upscale.service -n 50
```

### Если импорты не работают
```bash
/workspace/aporto/.venv/bin/python3 -c "from realesrgan.utils import RealESRGANer; print('OK')"
```

### Если basicsr не пропатчен
```bash
bash upscale/vastai_deployment/fix_basicsr.sh
```

## Контакты

При проблемах проверьте:
- `/workspace/server.log` - логи приложения
- `systemctl status vast-upscale.service` - статус сервиса
- `/workspace/aporto/.env` - переменные окружения
