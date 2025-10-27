#!/bin/bash
# Remote CUDA Fix - запускается с локальной машины
# Автоматически подключается к GPU серверу и исправляет CUDA

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 Remote CUDA Fix Tool${NC}"
echo "========================================"
echo ""

# Проверка параметров
if [ -f ".env" ]; then
    source .env
fi

GPU_SSH_HOST="${GPU_SSH_HOST:-}"
GPU_SSH_PORT="${GPU_SSH_PORT:-22}"
GPU_SSH_USER="${GPU_SSH_USER:-root}"

if [ -z "$GPU_SSH_HOST" ]; then
    echo -e "${RED}❌ GPU_SSH_HOST не найден${NC}"
    echo ""
    echo "Варианты:"
    echo "1. Укажите в .env файле:"
    echo "   GPU_SSH_HOST=your.gpu.server.com"
    echo "   GPU_SSH_PORT=22"
    echo "   GPU_SSH_USER=root"
    echo ""
    echo "2. Или запустите с параметрами:"
    echo "   GPU_SSH_HOST=1.2.3.4 $0"
    exit 1
fi

echo -e "Подключение к: ${GREEN}${GPU_SSH_USER}@${GPU_SSH_HOST}:${GPU_SSH_PORT}${NC}"
echo ""

# Функция для выполнения команд через SSH
run_remote() {
    ssh -p "${GPU_SSH_PORT}" "${GPU_SSH_USER}@${GPU_SSH_HOST}" "$@"
}

# Проверка подключения
echo "1️⃣ Проверка подключения..."
if ! run_remote "echo 'Connection OK'" 2>/dev/null; then
    echo -e "${RED}❌ Не удалось подключиться к серверу${NC}"
    echo ""
    echo "Проверьте:"
    echo "- SSH доступ: ssh -p ${GPU_SSH_PORT} ${GPU_SSH_USER}@${GPU_SSH_HOST}"
    echo "- Настройки в .env файле"
    exit 1
fi
echo -e "${GREEN}✅ Подключение успешно${NC}"
echo ""

# Проверка текущего состояния CUDA
echo "2️⃣ Проверка текущего состояния CUDA..."
run_remote "cd /workspace/aporto && source .venv/bin/activate && python -c 'import torch; print(\"CUDA available:\", torch.cuda.is_available())'" || true
echo ""

# Запуск исправления
echo "3️⃣ Запуск исправления CUDA..."
echo ""
run_remote "cd /workspace/aporto && bash upscale/vastai_deployment/fix_torch_cuda.sh"
echo ""

# Перезапуск сервера
echo "4️⃣ Перезапуск сервера..."
run_remote "systemctl restart vast-upscale.service"
echo -e "${GREEN}✅ Сервер перезапущен${NC}"
echo ""

# Ожидание запуска
echo "5️⃣ Ожидание запуска сервера..."
sleep 5

# Проверка логов
echo "6️⃣ Проверка логов..."
echo ""
run_remote "tail -30 /workspace/server.log"
echo ""

# Финальная проверка
echo "7️⃣ Финальная проверка CUDA..."
CUDA_STATUS=$(run_remote "cd /workspace/aporto && source .venv/bin/activate && python -c 'import torch; print(torch.cuda.is_available())'" 2>/dev/null || echo "Error")

if [ "$CUDA_STATUS" = "True" ]; then
    echo -e "${GREEN}✅ CUDA работает успешно!${NC}"
    run_remote "cd /workspace/aporto && source .venv/bin/activate && python -c 'import torch; print(f\"GPU: {torch.cuda.get_device_name(0)}\")'"
else
    echo -e "${YELLOW}⚠️  CUDA все еще недоступен${NC}"
    echo ""
    echo "Дополнительная диагностика:"
    run_remote "cd /workspace/aporto && bash upscale/vastai_deployment/diagnose_cuda.sh"
fi

echo ""
echo -e "${GREEN}🎉 Готово!${NC}"
echo ""
echo "Следующие шаги:"
echo "- Проверьте логи: ssh -p ${GPU_SSH_PORT} ${GPU_SSH_USER}@${GPU_SSH_HOST} 'tail -f /workspace/server.log'"
echo "- Тест здоровья: curl http://${GPU_SSH_HOST}:5000/health"
