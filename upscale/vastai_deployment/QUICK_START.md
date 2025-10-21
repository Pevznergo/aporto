# Быстрый старт - исправление VAST deployment

## ✅ Все изменения внесены в локальные файлы

### Что исправлено:

1. **upscale_app.py** - использует `VENV_PYTHON` для subprocess
2. **requirements.txt** - закреплены совместимые версии PyTorch
3. **install.sh** - автоматически патчит basicsr и добавляет VENV_PYTHON
4. **Новые скрипты** - диагностика и применение исправлений

## Действия прямо сейчас:

### 1️⃣ Закоммитьте и запушьте (на вашем Mac):

```bash
cd /Users/igortkachenko/Downloads/aporto
git add .
git commit -m "Fix: VAST deployment venv and basicsr compatibility"
git push origin main
```

### 2️⃣ Примените на VAST сервере:

```bash
# Подключитесь
ssh -p 27281 root@116.102.175.41

# Выполните
cd /workspace/aporto
git pull origin main
bash upscale/vastai_deployment/apply_fix.sh
```

### 3️⃣ Проверьте результат:

```bash
# Проверьте логи - должен использоваться правильный Python
tail -f /workspace/server.log

# Должны увидеть:
# Command: /workspace/aporto/.venv/bin/python ...
# Вместо: /venv/main/bin/python3 ...
```

## Что делает apply_fix.sh:

- 🔧 Патчит `basicsr` (functional_tensor → functional)
- 📝 Добавляет `VENV_PYTHON` в `.env`
- ✅ Тестирует импорты
- 🔄 Перезапускает сервис
- ✅ Проверяет статус

## Если что-то пойдет не так:

```bash
# Диагностика
bash upscale/vastai_deployment/diagnose.sh

# Ручное исправление basicsr
bash upscale/vastai_deployment/fix_basicsr.sh

# Просмотр логов
journalctl -u vast-upscale.service -n 100
tail -100 /workspace/server.log
```

## Готово! 🎉
После этих шагов сервер будет использовать правильный venv и все импорты заработают.
