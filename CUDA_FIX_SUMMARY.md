# CUDA Fix - Сводка решения

## Проблема
```
CUDA initialization: CUDA driver initialization failed
FATAL: CUT_REQUIRE_CUDA=1 but torch.cuda.is_available() is False
```

**Причина:** PyTorch установлен без CUDA поддержки (CPU-only версия) или несовпадение версий CUDA.

## 🎯 Решение за 2 минуты

### На GPU сервере:
```bash
cd /workspace/aporto
chmod +x upscale/vastai_deployment/*.sh
bash upscale/vastai_deployment/fix_torch_cuda.sh
systemctl restart vast-upscale.service
```

### Или с локальной машины через SSH:
```bash
cd /Users/igortkachenko/Downloads/aporto
chmod +x fix_cuda_remote.sh
./fix_cuda_remote.sh
```

## 📁 Созданные файлы

### Основные скрипты:
1. **`upscale/vastai_deployment/fix_torch_cuda.sh`**
   - Переустанавливает PyTorch с CUDA 12.1
   - Проверяет работу GPU
   - Использование: `bash upscale/vastai_deployment/fix_torch_cuda.sh [11.8|12.1]`

2. **`upscale/vastai_deployment/diagnose_cuda.sh`**
   - Диагностика CUDA проблем
   - Проверка драйверов, PyTorch, GPU
   - Использование: `bash upscale/vastai_deployment/diagnose_cuda.sh`

3. **`fix_cuda_remote.sh`** (в корне проекта)
   - Удаленное исправление через SSH
   - Автоматизирует все шаги
   - Использование: `./fix_cuda_remote.sh`

### Документация:
1. **`QUICK_FIX_CUDA.md`** - быстрый старт (начните отсюда!)
2. **`CUDA_TROUBLESHOOTING.md`** - полное руководство по troubleshooting
3. **`upscale/vastai_deployment/README_CUDA_FIX.md`** - README для GPU сервера
4. **`CUDA_FIX_SUMMARY.md`** - этот файл (сводка)

## 🔧 Что делает fix_torch_cuda.sh?

```
1. Проверяет NVIDIA драйверы (nvidia-smi)
2. Удаляет текущий PyTorch
3. Устанавливает PyTorch 2.4.1 с CUDA 12.1
4. Проверяет torch.cuda.is_available()
5. Тестирует CUDA операции
6. Выводит информацию о GPU
```

## 🔍 Диагностика

Если что-то не работает:

```bash
# На сервере
cd /workspace/aporto
bash upscale/vastai_deployment/diagnose_cuda.sh
```

Проверяет:
- ✅ NVIDIA драйверы (nvidia-smi)
- ✅ Версия CUDA в драйверах
- ✅ PyTorch версия и CUDA support
- ✅ Доступность GPU
- ✅ Дает рекомендации

## ✅ Проверка результата

### В логах сервера:
```bash
tail -f /workspace/server.log
```
Должно быть:
```
CUDA OK: {'torch_installed': True, 'cuda_available': True, 'cuda_device_count': 1, ...}
```

### Вручную:
```bash
source .venv/bin/activate
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```
Ожидаемый вывод:
```
CUDA: True
GPU: NVIDIA GeForce RTX 3090
```

## 🚨 Частые проблемы

### 1. "nvidia-smi: command not found"
**Решение:** Проверьте что выбран GPU instance на Vast.ai, а не CPU.

### 2. CUDA available: False после fix
**Решение:** 
```bash
# Попробуйте CUDA 11.8
bash upscale/vastai_deployment/fix_torch_cuda.sh 11.8
```

### 3. "CUDA out of memory"
**Решение:**
```bash
systemctl restart vast-upscale.service
```

### 4. Ничего не помогает
**Решение:** Полная переустановка:
```bash
cd /workspace/aporto
rm -rf .venv
bash upscale/vastai_deployment/install.sh
```

## 📊 Таблица совместимости

| Драйвер CUDA | PyTorch CUDA | Статус |
|--------------|--------------|--------|
| 12.x         | 12.1         | ✅ Работает |
| 11.8+        | 12.1         | ✅ Работает (обратная совместимость) |
| 11.x         | 11.8         | ✅ Работает |
| 10.x         | 12.1         | ❌ Не работает |

## 🎓 Полезные команды

```bash
# Проверить CUDA драйвер
nvidia-smi

# Проверить PyTorch CUDA
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"

# Проверить GPU память
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Перезапустить сервер
systemctl restart vast-upscale.service

# Логи в реальном времени
tail -f /workspace/server.log

# Статус сервера
systemctl status vast-upscale.service
```

## 🆘 Если ничего не помогло

Соберите диагностическую информацию:

```bash
cd /workspace/aporto
bash upscale/vastai_deployment/diagnose_cuda.sh > ~/cuda_diagnostics.txt
tail -100 /workspace/server.log >> ~/cuda_diagnostics.txt
nvidia-smi >> ~/cuda_diagnostics.txt
```

И отправьте файл `~/cuda_diagnostics.txt` для анализа.

## 📖 Дополнительная информация

- **PyTorch версия:** 2.4.1
- **Рекомендуемая CUDA:** 12.1 (fallback: 11.8)
- **Минимальный драйвер:** 525.60.13
- **Минимальная Compute Capability:** 3.5

## 🔗 Полезные ссылки

- [PyTorch CUDA installation](https://pytorch.org/get-started/locally/)
- [NVIDIA CUDA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/)
- [Vast.ai GPU instances](https://vast.ai/)
