# Video Cutter Task Manager

## 🚀 Быстрый старт

### Локальная разработка с серверным API

1. **Обновите конфигурацию фронтенда:**
```bash
cd web
echo "NEXT_PUBLIC_API_BASE_URL=http://74.208.193.3:8000" > .env.local
```

2. **Обновите CORS в бэкенде (app/main.py):**
```python
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://74.208.193.3:3000,https://studio.aporto.tech").split(",")
```

3. **Запустите локальный фронтенд:**
```bash
cd web
npm run dev
# Откройте http://localhost:3000
```

4. **Бэкенд на сервере уже запущен:**
   - API: `http://74.208.193.3:8000/api/*`
   - Фронтенд: `https://studio.aporto.tech`

## 📁 Структура проекта

- `app/` - FastAPI бэкенд
- `web/` - Next.js фронтенд
- `upscale/` - модули для улучшения качества видео

## 🔧 API Endpoints

- `GET /api/tasks` - список задач обработки
- `GET /api/downloads` - скачанные видео
- `GET /api/clips` - созданные клипы
- `GET /api/upscale/tasks` - задачи улучшения качества
- `GET /api/upscale/status` - статус upscale системы

## 🌐 Развертывание

### Обновление сервера:

1. **Синхронизируйте код:**
```bash
git add .
git commit -m "Configure server API integration"
git push
```

2. **Обновите сервер:**
```bash
# На сервере
cd /opt/aporto
git pull
./start_server_backend.sh
./update_server_frontend.sh
```

3. **Проверьте работу:**
```bash
curl https://studio.aporto.tech/api/tasks
```

## 🔒 Безопасность

- CORS настроен для разрешения запросов с `studio.aporto.tech`
- API доступен только для авторизованных доменов
- SSL/TLS настроен для HTTPS соединений

## 📝 Изменения для серверного API

- ✅ Обновлен CORS для разрешения серверных запросов
- ✅ Next.js настроен для проксирования API на сервер
- ✅ Nginx конфигурация для правильной маршрутизации
- ✅ Локальная разработка с серверным бэкендом
