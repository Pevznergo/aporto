# Deploy Healthcheck to VPS

## Files to copy to your VPS:

1. `test_healthcheck_fixed.py` - Main test script
2. Updated `app/main.py` (with healthcheck API endpoint)  
3. Updated `app/worker.py` (with healthcheck worker)

## Steps:

### 1. Copy files to VPS
```bash
# Copy test script
scp test_healthcheck_fixed.py user@your-vps:/path/to/aporto/

# Copy updated app files
scp app/main.py user@your-vps:/path/to/aporto/app/
scp app/worker.py user@your-vps:/path/to/aporto/app/
```

### 2. On VPS - Restart orchestrator
```bash
# Stop current orchestrator
sudo systemctl stop aporto-orchestrator
# OR kill manually: pkill -f "python.*main.py"

# Start orchestrator
cd /path/to/aporto
python app/main.py
# OR via systemctl if configured:
# sudo systemctl start aporto-orchestrator
```

### 3. Test healthcheck
```bash
cd /path/to/aporto
python test_healthcheck_fixed.py
```

## Expected output:
- ✅ API responding on port 8000
- 🏥 Healthcheck enabled with 5min interval  
- 📊 Queue stats showing current status
- 👀 Optional monitoring mode

## Monitoring:
- Check logs: `tail -f /path/to/logs` for `[healthcheck]` messages
- API endpoint: `http://localhost:8000/api/queue/stats`
- Healthcheck runs every 5 minutes automatically

## Environment Variables:
Make sure these are set in your `.env` file:
```
UPSCALE_UPLOAD_CONCURRENCY=1
UPSCALE_CONCURRENCY=2  
UPSCALE_RESULT_DOWNLOAD_CONCURRENCY=1
```