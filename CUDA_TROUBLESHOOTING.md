# CUDA Troubleshooting Guide

## Проблема: "CUDA driver initialization failed"

Ошибка появляется когда PyTorch не может инициализировать CUDA, хотя GPU есть.

```
FATAL: CUT_REQUIRE_CUDA=1 but torch.cuda.is_available() is False
```

## Причины

1. **PyTorch установлен без CUDA** - установлена CPU-only версия
2. **Несовпадение версий CUDA** - PyTorch скомпилирован для CUDA 12.1, а драйвер поддерживает только 11.x
3. **Проблемы с NVIDIA драйверами** - драйверы не установлены или не работают

## Диагностика

### Шаг 1: Запустите диагностический скрипт

```bash
cd /workspace/aporto
bash upscale/vastai_deployment/diagnose_cuda.sh
```

Этот скрипт проверит:
- ✅ Наличие NVIDIA драйверов
- ✅ Версию CUDA в драйверах
- ✅ Версию PyTorch и поддержку CUDA
- ✅ Доступность GPU

### Шаг 2: Проверьте вывод

**Если nvidia-smi работает:**
```bash
nvidia-smi
```

Вы должны увидеть информацию о GPU и версию CUDA драйвера (например, `CUDA Version: 12.2`).

**Если PyTorch показывает CUDA compiled: None или cpu:**
```python
import torch
print(torch.__version__)  # Например: 2.4.1+cpu - это ПЛОХО, нужно +cu121
print(torch.cuda.is_available())  # False - ПЛОХО
```

## Решение

### Быстрое исправление (рекомендуется)

```bash
cd /workspace/aporto
bash upscale/vastai_deployment/fix_torch_cuda.sh
```

Этот скрипт:
1. Удалит текущий PyTorch
2. Установит PyTorch с CUDA 12.1
3. Проверит работоспособность

### Если GPU старый или CUDA версия ниже 12.0

Попробуйте CUDA 11.8:

```bash
bash upscale/vastai_deployment/fix_torch_cuda.sh 11.8
```

### Проверка после исправления

```bash
# Активируйте venv
source .venv/bin/activate

# Проверьте CUDA
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

**Ожидаемый результат:**
```
CUDA available: True
GPU: NVIDIA GeForce RTX 3090
```

### Перезапустите сервер

```bash
systemctl restart vast-upscale.service
```

### Проверьте логи

```bash
tail -f /workspace/server.log
```

Вы должны увидеть:
```
CUDA OK: {'torch_installed': True, 'cuda_available': True, ...}
```

## Альтернативное решение (если GPU не нужен)

Если вы хотите запустить без CUDA (медленно, не рекомендуется):

### Отключите проверку CUDA

Отредактируйте `/workspace/aporto/.env`:
```bash
CUT_REQUIRE_CUDA=0
CUT_FORCE_DEVICE=cpu
```

Перезапустите сервер:
```bash
systemctl restart vast-upscale.service
```

## Распространенные ошибки

### 1. "No module named 'torch'"

PyTorch не установлен:
```bash
source .venv/bin/activate
pip install -r upscale/vastai_deployment/requirements.txt
```

### 2. "CUDA out of memory"

GPU память заполнена. Перезапустите сервер:
```bash
systemctl restart vast-upscale.service
```

### 3. "nvidia-smi: command not found"

NVIDIA драйверы не установлены. Проверьте конфигурацию Vast.ai instance - должен быть выбран GPU instance.

### 4. "libcudart.so.12.1: cannot open shared object file"

CUDA runtime библиотека не найдена. Переустановите PyTorch:
```bash
bash upscale/vastai_deployment/fix_torch_cuda.sh
```

## Проверка совместимости CUDA

| Драйвер CUDA | PyTorch CUDA | Совместимость |
|--------------|--------------|---------------|
| 12.x         | 12.1         | ✅ Да         |
| 11.8+        | 12.1         | ✅ Да (обратная совместимость) |
| 11.x         | 11.8         | ✅ Да         |
| 10.x         | 12.1         | ❌ Нет        |
| 10.x         | 11.8         | ❌ Нет        |

**Правило:** Версия драйвера должна быть >= версии CUDA в PyTorch.

## Полная переустановка (крайний случай)

Если ничего не помогает:

```bash
cd /workspace/aporto

# Удалите venv
rm -rf .venv

# Переустановите
bash upscale/vastai_deployment/install.sh
```

## Контакты для помощи

Если проблема не решена, соберите информацию:

```bash
cd /workspace/aporto
bash upscale/vastai_deployment/diagnose_cuda.sh > cuda_diagnostics.txt
cat /workspace/server.log >> cuda_diagnostics.txt
```

И отправьте файл `cuda_diagnostics.txt` для анализа.
