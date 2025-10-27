# 🚨 Быстрое решение CUDA проблемы

## Ошибка
```
FATAL: CUT_REQUIRE_CUDA=1 but torch.cuda.is_available() is False
```

## ⚡ Быстрое исправление (2 минуты)

### Вариант 1: На GPU сервере напрямую

SSH подключитесь к серверу и выполните:

```bash
# 1. Перейдите в директорию проекта
cd /workspace/aporto

# 2. Сделайте скрипты исполняемыми (только первый раз)
chmod +x upscale/vastai_deployment/*.sh

# 3. Запустите исправление
bash upscale/vastai_deployment/fix_torch_cuda.sh

# 4. Перезапустите сервер
systemctl restart vast-upscale.service

# 5. Проверьте логи (должно показать "CUDA OK")
tail -f /workspace/server.log
```

### Вариант 2: С локальной машины (через SSH)

Если у вас есть SSH доступ к серверу, можно запустить с локальной машины:

```bash
# На вашей локальной машине
cd /Users/igortkachenko/Downloads/aporto  # путь к проекту

# Убедитесь что в .env указаны параметры SSH:
# GPU_SSH_HOST=your.gpu.server.com
# GPU_SSH_PORT=22
# GPU_SSH_USER=root

# Сделайте скрипт исполняемым (только первый раз)
chmod +x fix_cuda_remote.sh

# Запустите удаленное исправление
./fix_cuda_remote.sh
```

Скрипт автоматически:
- Подключится к GPU серверу
- Запустит исправление CUDA
- Перезапустит сервер
- Покажет результат

## ✅ Проверка успеха

После выполнения команд вы должны увидеть в логах:
```
CUDA OK: {'torch_installed': True, 'cuda_available': True, ...}
```

## 🔍 Если не помогло

1. **Запустите диагностику:**
   ```bash
   bash upscale/vastai_deployment/diagnose_cuda.sh
   ```

2. **Попробуйте другую версию CUDA:**
   ```bash
   # Для старых GPU
   bash upscale/vastai_deployment/fix_torch_cuda.sh 11.8
   ```

3. **Проверьте драйверы NVIDIA:**
   ```bash
   nvidia-smi
   ```
   
   Если команда не работает - проблема с драйверами или выбран не GPU instance на Vast.ai.

## 📖 Полная документация

См. [CUDA_TROUBLESHOOTING.md](./CUDA_TROUBLESHOOTING.md) для детальной информации.

## Что делает fix_torch_cuda.sh?

1. ✅ Удаляет текущую версию PyTorch
2. ✅ Устанавливает PyTorch 2.4.1 с CUDA 12.1
3. ✅ Проверяет доступность CUDA
4. ✅ Тестирует работу GPU

Скрипт безопасен и можно запускать несколько раз.
