#!/bin/bash
# Полное развертывание системы на сервере

SERVER_IP="74.208.193.3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Полное развертывание на сервер $SERVER_IP..."

# 1. Синхронизируем код
echo "📥 Синхронизация кода..."
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /opt/aporto && git pull"

# 2. Обновляем CORS в бэкенде
echo "🔧 Обновление CORS настроек..."
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "sed -i 's|http://localhost:3000,http://127.0.0.1:3000|http://localhost:3000,http://127.0.0.1:3000,http://74.208.193.3:3000,https://studio.aporto.tech|g' /opt/aporto/app/main.py"

# 3. Обновляем nginx конфигурацию
echo "🌐 Обновление nginx конфигурации..."
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cp /opt/aporto/nginx_studio.conf /etc/nginx/sites-available/aporto.conf"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "ln -sf /etc/nginx/sites-available/aporto.conf /etc/nginx/sites-enabled/"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "nginx -t && systemctl reload nginx"

# 4. Устанавливаем зависимости бэкенда
echo "📦 Установка зависимостей бэкенда..."
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /opt/aporto && pip install fastapi uvicorn sqlmodel python-multipart jinja2 python-dotenv"

# 5. Запускаем бэкенд
echo "🔄 Запуск бэкенда..."
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "pkill -f uvicorn"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /opt/aporto && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" &

# 6. Обновляем фронтенд
echo "🎨 Обновление фронтенда..."
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "echo 'NEXT_PUBLIC_API_BASE_URL=http://74.208.193.3:8000' > /var/www/studio.aporto.tech/.env"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "pkill -f next"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /var/www/studio.aporto.tech && rm -rf .next && npm run build && nohup npm run start -- -p 3000 > /opt/aporto/frontend.log 2>&1 &"

# 7. Проверяем статус
echo "✅ Проверка статуса..."
sleep 5

echo ""
echo "🎯 Проверка API endpoints:"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "curl -s http://127.0.0.1:8000/api/tasks | jq '. | length'" 2>/dev/null || echo "❌ Бэкенд не отвечает"
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "curl -s http://127.0.0.1:3000 | grep -o 'NEXT_PUBLIC_API_BASE_URL[^\"]*'" 2>/dev/null || echo "❌ Фронтенд не отвечает"

echo ""
echo "🌐 Ссылки для проверки:"
echo "🔗 Фронтенд: https://studio.aporto.tech"
echo "🔗 API: http://74.208.193.3:8000/api/tasks"
echo "🔗 API через nginx: https://studio.aporto.tech/api/tasks"

echo ""
echo "✅ Развертывание завершено!"
echo "📝 Проверьте логи: tail -f /opt/aporto/frontend.log"
