# Настройка для работы с серверным API

## 1. Обновите .env.local в папке web:

```bash
echo "NEXT_PUBLIC_API_BASE_URL=http://74.208.193.3:8000" > web/.env.local
```

## 2. Обновите CORS в app/main.py:

```python
# CORS for Next.js frontend
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://74.208.193.3:3000,https://studio.aporto.tech").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 3. Next.js rewrites настроены в next.config.js:

API запросы с фронтенда автоматически проксируются на серверный бэкенд.

## 4. На сервере запустите:

```bash
# Бэкенд
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Фронтенд
cd /var/www/studio.aporto.tech
npm run build
npm run start
```

## 5. Синхронизируйте изменения:

```bash
git add .
git commit -m "Configure frontend to use server API"
git push
```
