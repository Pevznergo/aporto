#!/bin/bash
# Запуск бэкенда на сервере
SERVER_IP="74.208.193.3"

echo "🚀 Запуск бэкенда на сервере $SERVER_IP..."

# Обновляем CORS на сервере
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "sed -i 's|http://localhost:3000,http://127.0.0.1:3000|http://localhost:3000,http://127.0.0.1:3000,http://74.208.193.3:3000,https://studio.aporto.tech|g' /opt/aporto/app/main.py"

# Устанавливаем зависимости
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /opt/aporto && pip install fastapi uvicorn sqlmodel python-multipart jinja2 python-dotenv"

# Останавливаем старые процессы
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "pkill -f uvicorn"

# Запускаем бэкенд
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /opt/aporto && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" &

echo "✅ Бэкенд запущен на http://$SERVER_IP:8000"
echo "✅ Проверьте: curl http://$SERVER_IP:8000/api/tasks"
