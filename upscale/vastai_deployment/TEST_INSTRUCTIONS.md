# Инструкции по тестированию

## ✅ Исправлено

1. **Модель скачана** - `realesr-general-x4v3.pth` теперь имеет правильный размер (4.7MB вместо 0 байт)
2. **Правильный Python** - используется `/workspace/aporto/.venv/bin/python`
3. **basicsr пропатчен** - импорт исправлен
4. **VENV_PYTHON настроен** - переменная окружения добавлена

## Быстрый тест (на VAST сервере)

### Вариант 1: Автоматический тест

```bash
ssh -p 27281 root@116.102.175.41

cd /workspace/aporto
git pull origin main  # если запушили изменения

# Запустить быстрый тест (создаст 1-сек видео и апскейлит)
bash upscale/vastai_deployment/test_upscale_quick.sh
```

### Вариант 2: Ручной тест

```bash
ssh -p 27281 root@116.102.175.41

cd /workspace/aporto
source .env

# Создать тестовое видео (1 секунда)
bash upscale/vastai_deployment/create_test_video.sh /tmp/test.mp4

# Проверить что модель на месте
ls -lh /workspace/aporto/upscale/models/*.pth

# Тест импорта
.venv/bin/python -c "
from realesrgan.utils import RealESRGANer
from gfpgan import GFPGANer
print('✅ Imports OK')
"

# Тест через vendor скрипт (создаст пару фреймов)
mkdir -p /tmp/test_frames /tmp/test_output
ffmpeg -i /tmp/test.mp4 -vf fps=5 /tmp/test_frames/frame_%04d.png

.venv/bin/python vendor/realesrgan_infer.py \
    -i /tmp/test_frames \
    -o /tmp/test_output \
    -n realesr-general-x4v3 \
    --outscale 4 \
    --face_enhance

ls -lh /tmp/test_output/
```

### Вариант 3: Через API

```bash
# Убедитесь что сервер запущен
curl http://localhost:5000/health

# Отправить задачу
curl -X POST http://localhost:5000/upscale \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/tmp/test.mp4",
    "output_path": "/tmp/test_upscaled.mp4"
  }'

# Проверить статус (используйте job_id из ответа)
curl http://localhost:5000/job/1
```

## Ожидаемый результат

```
✅ Imports OK
✅ Model loaded: /workspace/aporto/upscale/models/realesr-general-x4v3.pth
✅ GFPGAN enabled with weights: /workspace/aporto/upscale/models/GFPGANv1.4.pth
Enhanced 5 images to: /tmp/test_output
```

## Если что-то не работает

### Проблема: Модель не найдена

```bash
# Проверить размер модели
ls -lh /workspace/aporto/upscale/models/realesr-general-x4v3.pth

# Если 0 байт - скачать заново
cd /workspace/aporto/upscale/models
rm realesr-general-x4v3.pth
wget https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth
```

### Проблема: Импорты не работают

```bash
# Запустить диагностику
bash upscale/vastai_deployment/diagnose.sh

# Применить исправления
bash upscale/vastai_deployment/apply_fix.sh
```

### Проблема: Сервер использует старый код

```bash
# Найти и убить процесс
ps aux | grep server.py | grep -v grep
kill <PID>

# Запустить с правильным окружением
cd /workspace/aporto
source .env
.venv/bin/python upscale/vastai_deployment/server.py > /workspace/server.log 2>&1 &

# Проверить логи
tail -f /workspace/server.log
```

## Проверка что все работает правильно

В логах должны быть команды с правильным Python:

```
Command: /workspace/aporto/.venv/bin/python /workspace/aporto/vendor/realesrgan_infer.py ...
```

НЕ:
```
Command: /venv/main/bin/python3 ...  ❌
```

И размер модели должен быть ~4.7MB:
```bash
$ ls -lh /workspace/aporto/upscale/models/realesr-general-x4v3.pth
-rw-rw-r-- 1 root root 4.7M Aug 30 2022 realesr-general-x4v3.pth
```
