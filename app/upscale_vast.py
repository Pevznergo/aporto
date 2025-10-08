import os
import time
import json
import subprocess
import requests
import random
import threading
import shlex
from typing import Tuple, Dict

VAST_API_URL = "https://console.vast.ai/api/v0"

class TokenBucket:
    def __init__(self, rate_per_sec: float, burst: int):
        self.rate = max(0.0, rate_per_sec)
        self.capacity = max(1, burst)
        self.tokens = float(self.capacity)
        self.ts = time.time()
        self.lock = threading.Lock()

    def acquire(self):
        if self.rate <= 0:
            return
        while True:
            with self.lock:
                now = time.time()
                # refill tokens
                self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)
                self.ts = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                # need to wait for next token
                need = 1.0 - self.tokens
                delay = need / max(self.rate, 1e-6)
            time.sleep(delay)


class VastManager:
    def __init__(self):
        self.api_key = os.getenv("VAST_API_KEY")
        if not self.api_key:
            raise RuntimeError("VAST_API_KEY is not set in environment")
        # Optional override for upscale API base URL (e.g., http://127.0.0.1:18080)
        self.upscale_url_override = os.getenv("VAST_UPSCALE_URL") or None
        # Default upscale parameters (applied if remote API supports them)
        self.model_name = os.getenv("UPSCALE_MODEL_NAME", "realesr-general-x4v3")
        try:
            self.denoise_strength = float(os.getenv("UPSCALE_DENOISE_STRENGTH", "0.5"))
        except Exception:
            self.denoise_strength = 0.5
        self.face_enhance = str(os.getenv("UPSCALE_FACE_ENHANCE", "1")).lower() in ("1", "true", "yes")
        try:
            self.outscale = int(os.getenv("UPSCALE_OUTSCALE", "4"))
        except Exception:
            self.outscale = 4
        # Docker image for upscale server running on instance (overridden by runtime settings)
        self.cached_instance_id_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "upscale_instance.json")
        # Default HTTP timeout for Vast API calls (seconds)
        # Can be overridden via env VAST_HTTP_TIMEOUT
        try:
            self.http_timeout = float(os.getenv("VAST_HTTP_TIMEOUT", "10"))
        except Exception:
            self.http_timeout = 10.0
        # Rate limiter (env: VAST_RPS, VAST_BURST)
        try:
            rps = float(os.getenv("VAST_RPS", "0.5"))
        except Exception:
            rps = 0.5
        try:
            burst = int(os.getenv("VAST_BURST", "2"))
        except Exception:
            burst = 2
        self._rate_limit = TokenBucket(rate_per_sec=rps, burst=burst)
        # Cache for instance details (env: VAST_DETAILS_TTL seconds)
        try:
            self.details_ttl = float(os.getenv("VAST_DETAILS_TTL", "20"))
        except Exception:
            self.details_ttl = 20.0
        self._details_cache: dict[str, tuple[float, Dict]] = {}
        self._details_lock = threading.Lock()
        # Singleflight for ensure
        self._ensure_lock = threading.Lock()
        self._ensuring = False
        self._ensure_waiters: list[threading.Event] = []
        self._last_ensure_details: Dict | None = None
        # Cooldown for stopping instance (env: VAST_STOP_COOLDOWN seconds)
        try:
            self.stop_cooldown = float(os.getenv("VAST_STOP_COOLDOWN", "120"))
        except Exception:
            self.stop_cooldown = 120.0
        self._last_stop_ts = 0.0
        # Optional: completely disable auto-stop (env VAST_DISABLE_AUTO_STOP=1)
        self.disable_auto_stop = str(os.getenv("VAST_DISABLE_AUTO_STOP", "")).lower() in ("1", "true", "yes")
        # Activity window to avoid stopping around recent SSH/HTTP work
        try:
            self.stop_activity_window = float(os.getenv("VAST_STOP_ACTIVITY_WINDOW", "300"))
        except Exception:
            self.stop_activity_window = 300.0
        self._last_activity_ts = 0.0
        # Optional override of remote base dir (without trailing /upscale)
        self.remote_base_override = os.getenv("VAST_REMOTE_BASE_DIR") or None

    def _normalize_instance(self, data: Dict) -> Dict:
        """
        Vast API sometimes wraps instance data as {"instances": {...}}.
        Normalize to return the instance dict regardless of shape.
        """
        if isinstance(data, dict) and isinstance(data.get("instances"), dict):
            return data["instances"]
        return data

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _request_json(self, method: str, url: str, **kwargs) -> Dict:
        """HTTP request wrapper with retries/backoff, handling 429 and 5xx.
        Env overrides:
          - VAST_HTTP_RETRIES (default 3)
          - VAST_HTTP_BACKOFF (default 1.0 seconds)
        """
        try:
            retries = int(os.getenv("VAST_HTTP_RETRIES", "3"))
        except Exception:
            retries = 3
        try:
            base_backoff = float(os.getenv("VAST_HTTP_BACKOFF", "1.0"))
        except Exception:
            base_backoff = 1.0

        last_exc = None
        for attempt in range(retries + 1):
            try:
                # global rate limit to avoid 429 bursts
                self._rate_limit.acquire()
                r = requests.request(method, url, headers=self._headers(), timeout=self.http_timeout, **kwargs)
                # Respect rate limiting and transient server errors
                if r.status_code == 429 or 500 <= r.status_code < 600:
                    if attempt < retries:
                        retry_after = r.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            delay = float(retry_after)
                        else:
                            delay = base_backoff * (2 ** attempt)
                        delay += random.uniform(0, 0.25)
                        time.sleep(delay)
                        continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                last_exc = e
                if attempt < retries:
                    delay = base_backoff * (2 ** attempt) + random.uniform(0, 0.25)
                    time.sleep(delay)
                    continue
                raise
        if last_exc:
            raise last_exc
        return {}

    def _save_cached_instance(self, data: Dict):
        try:
            with open(self.cached_instance_id_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_cached_instance(self) -> Dict:
        try:
            if os.path.exists(self.cached_instance_id_path):
                with open(self.cached_instance_id_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def ensure_instance_running(self) -> Dict:
        """
        Ensure the configured Vast instance (VAST_INSTANCE_ID) is running.
        No creation is attempted. If no ID is configured, raise a clear error.
        Coalesces concurrent ensure calls (singleflight).
        """
        # Singleflight gate
        with self._ensure_lock:
            if self._ensuring:
                ev = threading.Event()
                self._ensure_waiters.append(ev)
                wait_on = ev
            else:
                self._ensuring = True
                wait_on = None
        if wait_on is not None:
            # Wait for the in-flight ensure to finish
            wait_on.wait()
            return self._last_ensure_details or {}

        try:
            from .upscale_config import get_upscale_settings
            settings = get_upscale_settings()
            configured_id = settings.get("VAST_INSTANCE_ID") or None
            if not configured_id:
                raise RuntimeError("VAST_INSTANCE_ID is not set in settings. Please set it in the Upscale settings UI.")

            details = self.get_instance_details(configured_id)
            if details.get("actual_status") != "running":
                self.start_instance(configured_id)
                self.wait_for_instance(configured_id, target_state="running", timeout=600)
                details = self.get_instance_details(configured_id)
            # Cache for convenience, but always prefer settings next time
            self._save_cached_instance({"id": configured_id})
            self._last_ensure_details = details
            return details
        finally:
            # Release singleflight and notify waiters
            with self._ensure_lock:
                self._ensuring = False
                for w in self._ensure_waiters:
                    w.set()
                self._ensure_waiters.clear()

    def get_instance_details(self, instance_id: str) -> Dict:
        # Cache lookup
        now = time.time()
        with self._details_lock:
            cached = self._details_cache.get(str(instance_id))
            if cached and (now - cached[0]) <= self.details_ttl:
                return cached[1]
        # Fetch
        data = self._request_json(
            "GET",
            f"{VAST_API_URL}/instances/{instance_id}/",
        )
        norm = self._normalize_instance(data)
        with self._details_lock:
            self._details_cache[str(instance_id)] = (time.time(), norm)
        return norm

    def start_instance(self, instance_id: str) -> Dict:
        data = self._request_json(
            "PUT",
            f"{VAST_API_URL}/instances/{instance_id}/",
            json={"state": "running"},
        )
        return self._normalize_instance(data)

    def stop_instance(self, instance_id: str) -> Dict:
        data = self._request_json(
            "PUT",
            f"{VAST_API_URL}/instances/{instance_id}/",
            json={"state": "stopped"},
        )
        return self._normalize_instance(data)

    def wait_for_instance(self, instance_id: str, target_state: str = "running", timeout: int = 600) -> bool:
        try:
            poll = float(os.getenv("VAST_WAIT_POLL", "15"))
        except Exception:
            poll = 15.0
        start = time.time()
        while time.time() - start < timeout:
            try:
                d = self.get_instance_details(instance_id)
                if d.get("actual_status") == target_state:
                    return True
            except Exception:
                pass
            # jitter 0..0.25s to avoid thundering herd
            time.sleep(poll + random.uniform(0, 0.25))
        return False

    def _get_ssh_info(self, inst: Dict) -> Tuple[str, int, str]:
        """
        Return (ssh_host, ssh_port, user). Vast usually uses ssh_host ssh.vast.ai and a port.
        Allows overriding via env VAST_SSH_HOST and VAST_SSH_PORT.
        """
        # Env overrides first
        ssh_host_override = os.getenv("VAST_SSH_HOST")
        ssh_port_override = os.getenv("VAST_SSH_PORT")
        if ssh_host_override or ssh_port_override:
            host = ssh_host_override or inst.get("ssh_host") or inst.get("hostname") or "ssh.vast.ai"
            try:
                port = int(ssh_port_override) if ssh_port_override else int(inst.get("ssh_port") or 22)
            except Exception:
                port = 22
            user = inst.get("ssh_user") or "root"
            return host, port, user
        # Default: from instance details
        ssh_host = inst.get("ssh_host") or inst.get("hostname") or "ssh.vast.ai"
        # Prefer explicit ssh_port; fallback to 22/tcp mapping if provided in a different shape
        ssh_port = 0
        try:
            ssh_port = int(inst.get("ssh_port") or 0)
        except Exception:
            ssh_port = 0
        if not ssh_port:
            ports = inst.get("ports") or {}
            # vast usually exposes SSH via host port mapping of 22/tcp
            entry = ports.get("22/tcp") or []
            try:
                if isinstance(entry, list) and entry:
                    ssh_port = int(entry[0].get("HostPort") or 0)
            except Exception:
                pass
        user = inst.get("ssh_user") or "root"
        return ssh_host, int(ssh_port or 22), user

    def _ssh_key_path(self) -> str | None:
        # Prefer explicit key env (path to private key)
        key = os.getenv("VAST_SSH_KEY") or os.getenv("UPSCALE_SSH_KEY")
        if key and os.path.isfile(key):
            return key
        return None

    def _ssh_common_opts(self) -> list[str]:
        opts = [
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ServerAliveInterval=10",
            "-o", "ServerAliveCountMax=3",
            "-o", "ConnectTimeout=10",
        ]
        key = self._ssh_key_path()
        if key:
            opts += ["-i", key]
        return opts

    def _wait_for_ssh(self, host: str, port: int, user: str, timeout: float = 120.0) -> bool:
        """Poll SSH reachability before attempting scp. Non-interactive."""
        start = time.time()
        while time.time() - start < timeout:
            cmd = [
                "ssh", "-p", str(port), *self._ssh_common_opts(), f"{user}@{host}", "true"
            ]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode == 0:
                    return True
            except Exception:
                pass
            time.sleep(3)
        return False

    def _remote_base_dir(self, inst: Dict) -> str:
        """Pick a writable base dir on remote. Prefer env override, then DATA_DIRECTORY or /workspace, fallback to /app or $HOME."""
        # Explicit override via env
        if self.remote_base_override:
            return self.remote_base_override.rstrip("/")
        # Try DATA_DIRECTORY from extra_env (list of [key, value])
        base = None
        try:
            extra = inst.get("extra_env") or []
            for kv in extra:
                if isinstance(kv, list) and len(kv) >= 2 and kv[0] == "DATA_DIRECTORY":
                    base = kv[1]
                    break
        except Exception:
            base = None
        if not base:
            base = "/workspace"
        return base

    def _get_http_ip(self, inst: Dict) -> str:
        return inst.get("public_ipaddr") or inst.get("ip_addr") or inst.get("ip") or ""

    def _get_mapped_host_port(self, inst: Dict, key: str) -> int:
        """Return external HostPort mapped for a given internal port key like '5000/tcp'."""
        try:
            ports = inst.get("ports") or {}
            entry = ports.get(key) or []
            if isinstance(entry, list) and entry:
                hp = entry[0].get("HostPort")
                return int(hp) if hp else 0
        except Exception:
            pass
        return 0

    def _public_base_for_port(self, inst: Dict, internal_port: int) -> str:
        """Build http://<public_ip>:<external_port> using Vast port mapping when present."""
        ip = self._get_http_ip(inst)
        if not ip:
            return ""
        mapped = self._get_mapped_host_port(inst, f"{internal_port}/tcp")
        if mapped:
            return f"http://{ip}:{mapped}"
        return f"http://{ip}:{internal_port}"

    def upload_and_plan_paths(self, inst: Dict, local_path: str) -> Tuple[str, str]:
        """
        Upload local file to instance inbox and plan output path.
        Safe upload strategy:
          1) Upload to a temporary path under inbox (hidden .*.part)
          2) Validate size matches local file size
          3) Validate ffprobe can read the video stream
          4) Atomically move temp file to final path
        Returns (remote_input_path, remote_output_path)
        """
        ssh_host, ssh_port, user = self._get_ssh_info(inst)
        # Robust filename extraction
        filename = os.path.basename(os.path.normpath(local_path))
        if not filename:
            raise RuntimeError(f"Invalid local_path: {local_path}")
        # Local size for validation
        try:
            local_size = os.path.getsize(local_path)
        except OSError as e:
            raise RuntimeError(f"Failed to stat local file '{local_path}': {e}")
        # Allow explicit override of inbox/outbox via env
        inbox_override = os.getenv("VAST_REMOTE_INBOX")
        outbox_override = os.getenv("VAST_REMOTE_OUTBOX")
        if inbox_override and outbox_override:
            inbox = inbox_override.rstrip("/")
            outbox = outbox_override.rstrip("/")
        else:
            base = self._remote_base_dir(inst)
            upbase = f"{base}/upscale"
            inbox = f"{upbase}/inbox"
            outbox = f"{upbase}/outbox"
        remote_in = f"{inbox}/{filename}"
        remote_tmp = f"{inbox}/.{filename}.part"
        remote_out = f"{outbox}/{filename}"
        # Wait for SSH to be ready
        if not self._wait_for_ssh(ssh_host, ssh_port, user, timeout=180.0):
            raise RuntimeError(f"SSH not ready on {ssh_host}:{ssh_port}")
        # Mark activity
        self._last_activity_ts = time.time()
        # Create dirs on remote, with fallbacks
        def _mkdir(dir1: str, dir2: str) -> bool:
            cmd = ["ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}", f"mkdir -p {dir1} {dir2}"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"[upscale] mkdir failed on remote: {r.stderr or r.stdout}")
            return r.returncode == 0
        print(f"[upscale] remote paths: inbox={inbox}, outbox={outbox}")
        if not _mkdir(inbox, outbox):
            # Fallback to /app/upscale
            upbase = "/app/upscale"
            inbox = f"{upbase}/inbox"
            outbox = f"{upbase}/outbox"
            remote_in = f"{inbox}/{filename}"
            remote_tmp = f"{inbox}/.{filename}.part"
            remote_out = f"{outbox}/{filename}"
            if not _mkdir(inbox, outbox):
                # Fallback to $HOME/upscale
                upbase = "~/upscale"
                inbox = f"{upbase}/inbox"
                outbox = f"{upbase}/outbox"
                remote_in = f"{inbox}/{filename}"
                remote_tmp = f"{inbox}/.{filename}.part"
                remote_out = f"{outbox}/{filename}"
                if not _mkdir(inbox, outbox):
                    raise RuntimeError("Failed to create remote inbox/outbox directories")
        # Ensure local file is stable before upload
        def _is_local_stable(path: str, checks: int = 3, interval: float = 1.0, timeout: float = 30.0) -> bool:
            start = time.time()
            last = (-1, -1)
            while checks > 0 and (time.time() - start) <= timeout:
                try:
                    st = os.stat(path)
                    cur = (st.st_size, int(st.st_mtime))
                except FileNotFoundError:
                    return False
                if cur == last:
                    checks -= 1
                else:
                    checks = 3
                    last = cur
                time.sleep(interval)
            return checks == 0
        if not _is_local_stable(local_path):
            raise RuntimeError(f"Local file appears to be still writing: {local_path}")

        # scp upload to temporary path (non-interactive, with options)
        scp_cmd = ["scp", "-P", str(ssh_port), *self._ssh_common_opts(), local_path, f"{user}@{ssh_host}:{remote_tmp}"]
        print(f"[upscale] scp upload to temp: {user}@{ssh_host}:{remote_tmp}")
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        # Mark activity
        self._last_activity_ts = time.time()
        if result.returncode != 0:
            raise RuntimeError(f"scp upload failed: {result.stderr or result.stdout}")
        # Validate remote size with tolerance for post-upload local growth
        size_cmd = [
            "ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}",
            f"test -f {shlex.quote(remote_tmp)} && wc -c < {shlex.quote(remote_tmp)}"
        ]
        sz = subprocess.run(size_cmd, capture_output=True, text=True)
        if sz.returncode != 0:
            # Clean up temp on failure
            subprocess.run(["ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}", f"rm -f {shlex.quote(remote_tmp)}"], capture_output=True, text=True)
            raise RuntimeError(f"Remote size check failed for {remote_tmp}: {sz.stderr or sz.stdout}")
        try:
            remote_size = int(sz.stdout.strip())
        except Exception:
            remote_size = -1
        # Re-stat local after upload
        try:
            local_size_after = os.path.getsize(local_path)
        except Exception:
            local_size_after = local_size
        if remote_size != local_size_after:
            # Small grace: retry reading remote size once after 1s
            time.sleep(1.0)
            sz2 = subprocess.run(size_cmd, capture_output=True, text=True)
            try:
                remote_size2 = int((sz2.stdout or '').strip()) if sz2.returncode == 0 else remote_size
            except Exception:
                remote_size2 = remote_size
            if remote_size2 != local_size_after:
                subprocess.run(["ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}", f"rm -f {shlex.quote(remote_tmp)}"], capture_output=True, text=True)
                raise RuntimeError(f"Remote file size mismatch: local={local_size_after} bytes, remote={remote_size2} bytes")
        # Validate video readability via ffprobe on remote
        probe_cmd = [
            "ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}",
            f"ffprobe -v error -hide_banner -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 {shlex.quote(remote_tmp)}"
        ]
        probe = subprocess.run(probe_cmd, capture_output=True, text=True)
        if probe.returncode != 0:
            # Print detailed probe error (stderr) and cleanup
            err = probe.stderr or probe.stdout
            subprocess.run(["ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}", f"rm -f {shlex.quote(remote_tmp)}"], capture_output=True, text=True)
            raise RuntimeError(f"ffprobe failed on uploaded file: {err}")
        # Atomically move temp to final inbox path
        mv_cmd = ["ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}", f"mv -f {shlex.quote(remote_tmp)} {shlex.quote(remote_in)}"]
        mv = subprocess.run(mv_cmd, capture_output=True, text=True)
        if mv.returncode != 0:
            # Best-effort cleanup
            subprocess.run(["ssh", "-p", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}", f"rm -f {shlex.quote(remote_tmp)}"], capture_output=True, text=True)
            raise RuntimeError(f"Failed to move uploaded file into inbox: {mv.stderr or mv.stdout}")
        print(f"[upscale] upload validated and moved into inbox: {remote_in}")
        return remote_in, remote_out

    def submit_job(self, inst: Dict, remote_in: str, remote_out: str) -> str:
        if self.upscale_url_override:
            url = self.upscale_url_override.rstrip('/') + "/upscale"
        else:
            base = self._public_base_for_port(inst, 5000)
            if not base:
                raise RuntimeError("Instance public IP not found")
            url = f"{base}/upscale"
        payload = {
            "input_path": remote_in,
            "output_path": remote_out,
            "model_name": self.model_name,
            "denoise_strength": self.denoise_strength,
            "face_enhance": self.face_enhance,
            "outscale": self.outscale,
        }
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code not in (200, 202):
            raise RuntimeError(f"Failed to submit job: {r.text}")
        data = r.json()
        return str(data.get("job_id"))

    def job_status(self, inst: Dict, job_id: str) -> str:
        if self.upscale_url_override:
            base = self.upscale_url_override.rstrip('/')
            r = requests.get(f"{base}/job/{job_id}", timeout=10)
        else:
            base = self._public_base_for_port(inst, 5000)
            r = requests.get(f"{base}/job/{job_id}", timeout=10)
        if r.status_code != 200:
            return "failed"
        data = r.json()
        return data.get("status", "failed")

    def download_result(self, inst: Dict, remote_out: str, local_dir: str) -> str:
        ssh_host, ssh_port, user = self._get_ssh_info(inst)
        os.makedirs(local_dir, exist_ok=True)
        filename = os.path.basename(remote_out)
        local_path = os.path.join(local_dir, filename)
        scp_cmd = ["scp", "-P", str(ssh_port), *self._ssh_common_opts(), f"{user}@{ssh_host}:{remote_out}", local_path]
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        # Mark activity
        self._last_activity_ts = time.time()
        if result.returncode != 0:
            raise RuntimeError(f"scp download failed: {result.stderr or result.stdout}")
        return os.path.abspath(local_path)

    # ====== CUT (transcribe + cut) support ======
    def _cut_remote_dirs(self, inst: Dict) -> tuple[str, str]:
        base = self._remote_base_dir(inst)
        cut_base = f"{base}/cut"
        to_cut = f"{cut_base}/to_cut"
        cuted = f"{cut_base}/cuted"
        return to_cut, cuted

    def submit_cut_url(self, inst: Dict, url: str, model_size: str = "small", resize: bool = False, aspect_ratio: tuple[int, int] = (9, 16)) -> str:
        # HTTP endpoint on the same server
        if self.upscale_url_override:
            base = self.upscale_url_override.rstrip('/')
        else:
            base = self._public_base_for_port(inst, 5000)
        if not base:
            raise RuntimeError("Instance public IP not found")
        to_dir, out_dir = self._cut_remote_dirs(inst)
        payload = {"url": url, "model_size": model_size, "to_dir": to_dir, "out_dir": out_dir}
        if resize:
            payload["resize"] = True
            payload["aspect_ratio"] = list(aspect_ratio)
        r = requests.post(f"{base}/cut_url", json=payload, timeout=30)
        if r.status_code not in (200, 202):
            raise RuntimeError(f"Failed to submit cut job: {r.text}")
        data = r.json()
        return str(data.get("job_id"))

    def cut_status(self, inst: Dict, job_id: str) -> dict:
        if self.upscale_url_override:
            base = self.upscale_url_override.rstrip('/')
        else:
            base = self._public_base_for_port(inst, 5000)
        r = requests.get(f"{base}/cut_job/{job_id}", timeout=15)
        if r.status_code != 200:
            return {"status": "failed"}
        return r.json()

    def _find_l4_offer(self) -> Dict:
        # Deprecated: creation flow is disabled by policy
        raise RuntimeError("Instance creation via API is disabled. Set VAST_INSTANCE_ID in settings.")
        # Find an L4 bundle offer
        data = self._request_json(
            "GET",
            f"{VAST_API_URL}/bundles/?q=gpu_name:L4",
        )
        # Data structure may vary; select first available offer
        if isinstance(data, dict) and 'offers' in data:
            offers = data['offers']
        else:
            offers = data if isinstance(data, list) else []
        if not offers:
            raise RuntimeError("No L4 offers found via Vast API bundles endpoint")
        return offers[0]

    def _create_via_orders(self, cfg: Dict) -> Dict:
        # Deprecated: creation flow is disabled by policy
        raise RuntimeError("Instance creation via API is disabled. Set VAST_INSTANCE_ID in settings.")

    def stop_instance_if_idle(self):
        # Allow disabling auto stop entirely
        if self.disable_auto_stop:
            return
        # Enforce cooldown to avoid rapid stop/start cycles
        now = time.time()
        if (now - self._last_stop_ts) < self.stop_cooldown:
            return
        # Avoid stopping if there was recent activity (SSH/HTTP)
        if (now - self._last_activity_ts) < self.stop_activity_window:
            return
        # Prefer configured ID; fall back to cached
        try:
            from .upscale_config import get_upscale_settings
            s = get_upscale_settings()
            instance_id = s.get("VAST_INSTANCE_ID") or None
        except Exception:
            instance_id = None
        if not instance_id:
            cached = self._load_cached_instance()
            instance_id = cached.get("id")
        if instance_id:
            try:
                self.stop_instance(instance_id)
                self._last_stop_ts = time.time()
            except Exception:
                pass

    def get_status(self) -> str:
        """Return 'running', 'stopped', or 'unknown' based on instance state.
        Prefers cached instance; falls back to VAST_INSTANCE_ID from settings.
        """
        cached = self._load_cached_instance()
        instance_id = cached.get("id")
        if not instance_id:
            try:
                from .upscale_config import get_upscale_settings
                s = get_upscale_settings()
                instance_id = s.get("VAST_INSTANCE_ID") or None
            except Exception:
                instance_id = None
        if not instance_id:
            return "stopped"
        try:
            d = self.get_instance_details(instance_id)
            return d.get("actual_status") or "unknown"
        except Exception:
            return "unknown"
