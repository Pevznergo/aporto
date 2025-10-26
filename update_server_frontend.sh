#!/bin/bash
# Обновление фронтенда на сервере
SERVER_IP="74.208.193.3"

echo "🚀 Обновление фронтенда на сервере $SERVER_IP..."

# Обновляем .env
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "echo 'NEXT_PUBLIC_API_BASE_URL=http://74.208.193.3:8000' > /var/www/studio.aporto.tech/.env"

# Останавливаем старый Next.js
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "pkill -f next"

# Пересобираем и запускаем
ssh -i ~/.ssh/vast_id_ed25519 root@$SERVER_IP "cd /var/www/studio.aporto.tech && rm -rf .next && npm run build && nohup npm run start -- -p 3000 > /opt/aporto/frontend.log 2>&1 &"

echo "✅ Фронтенд обновлён и запущен"
echo "✅ Доступен на: https://studio.aporto.tech"
echo "✅ API: https://studio.aporto.tech/api/*"
