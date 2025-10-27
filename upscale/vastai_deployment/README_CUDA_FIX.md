# CUDA Fix для Vast.ai GPU Server

## Проблема

```
UserWarning: CUDA initialization: CUDA driver initialization failed
FATAL: CUT_REQUIRE_CUDA=1 but torch.cuda.is_available() is False
```

## Причина

PyTorch установлен без поддержки CUDA (CPU-only версия) или версия CUDA в PyTorch не соответствует драйверам GPU.

## Решение

### На GPU сервере (прямое подключение)

```bash
cd /workspace/aporto
bash upscale/vastai_deployment/fix_torch_cuda.sh
systemctl restart vast-upscale.service
```

### С локальной машины (через SSH)

```bash
cd ~/Downloads/aporto  # или ваш путь к проекту
chmod +x fix_cuda_remote.sh
./fix_cuda_remote.sh
```

Убедитесь что в `.env` указаны параметры подключения:
```bash
GPU_SSH_HOST=your.gpu.server.com
GPU_SSH_PORT=22
GPU_SSH_USER=root
```

## Диагностика

```bash
# На GPU сервере
cd /workspace/aporto
bash upscale/vastai_deployment/diagnose_cuda.sh
```

## Что делают скрипты?

### fix_torch_cuda.sh
- Удаляет текущий PyTorch
- Устанавливает PyTorch 2.4.1 с CUDA 12.1 (или 11.8 если указано)
- Проверяет работу GPU
- Тестирует CUDA операции

### diagnose_cuda.sh
- Проверяет NVIDIA драйверы (nvidia-smi)
- Показывает версию CUDA в драйвере
- Проверяет версию PyTorch и CUDA support
- Дает рекомендации по исправлению

### fix_cuda_remote.sh
- Подключается к GPU серверу через SSH
- Запускает fix_torch_cuda.sh удаленно
- Перезапускает сервер
- Проверяет логи и статус CUDA

## Проверка успешности

После исправления в логах должно быть:
```
CUDA OK: {'torch_installed': True, 'torch_version': '2.4.1+cu121', 'cuda_available': True, ...}
```

Проверить вручную:
```bash
source .venv/bin/activate
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

Ожидаемый вывод:
```
CUDA: True | GPU: NVIDIA GeForce RTX 3090
```

## Альтернатива: отключить CUDA

Если GPU не нужен, можно отключить требование CUDA в `.env`:
```bash
CUT_REQUIRE_CUDA=0
CUT_FORCE_DEVICE=cpu
```

⚠️ **Внимание:** Работа на CPU будет в 10-100 раз медленнее.

## Совместимость версий

| Компонент | Рекомендуемая версия |
|-----------|---------------------|
| PyTorch | 2.4.1 |
| CUDA (в PyTorch) | 12.1 |
| NVIDIA Driver | >= 525.60.13 |
| Compute Capability | >= 3.5 |

## Troubleshooting

### "nvidia-smi: command not found"
NVIDIA драйверы не установлены. Проверьте что выбран GPU instance на Vast.ai, а не CPU instance.

### "CUDA out of memory"
```bash
systemctl restart vast-upscale.service
```

### Ничего не помогает
Полная переустановка:
```bash
cd /workspace/aporto
rm -rf .venv
bash upscale/vastai_deployment/install.sh
```

## Файлы

- `fix_torch_cuda.sh` - исправление PyTorch CUDA на сервере
- `diagnose_cuda.sh` - диагностика CUDA проблем
- `../../fix_cuda_remote.sh` - удаленное исправление через SSH
- `../../CUDA_TROUBLESHOOTING.md` - полная документация
- `../../QUICK_FIX_CUDA.md` - быстрый старт
