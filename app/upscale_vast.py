import os
import time
import json
import subprocess
import requests
from typing import Tuple, Dict

VAST_API_URL = "https://console.vast.ai/api/v0"

class VastManager:
    def __init__(self):
        self.api_key = os.getenv("VAST_API_KEY")
        if not self.api_key:
            raise RuntimeError("VAST_API_KEY is not set in environment")
        # Docker image for upscale server running on instance (overridden by runtime settings)
        self.cached_instance_id_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "upscale_instance.json")

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

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
        Ensure an L4 instance with our image is running. If cached instance exists, try to start it.
        Otherwise, use VAST_INSTANCE_ID from runtime settings if provided.
        If creation endpoint is unavailable, raise a friendly error.
        Returns instance details from Vast API.
        """
        from .upscale_config import get_upscale_settings
        settings = get_upscale_settings()

        # Try configured instance id first
        configured_id = settings.get("VAST_INSTANCE_ID") or None
        if configured_id:
            try:
                details = self.get_instance_details(configured_id)
                if details.get("actual_status") != "running":
                    self.start_instance(configured_id)
                    self.wait_for_instance(configured_id, target_state="running", timeout=600)
                self._save_cached_instance({"id": configured_id})
                return details
            except Exception:
                pass

        # Try cached
        cached = self._load_cached_instance()
        instance_id = cached.get("id")
        if instance_id:
            details = self.get_instance_details(instance_id)
            state = details.get("actual_status")
            if state != "running":
                self.start_instance(instance_id)
                self.wait_for_instance(instance_id, target_state="running", timeout=600)
            return details

        # Fallback: attempt to create new from config
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "upscale", "vastai_instance_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Override image and onstart from runtime settings
        image = settings.get("UPSCALE_IMAGE") or os.getenv("UPSCALE_IMAGE") or "your-dockerhub-username/video-upscale-app:latest"
        cfg["image"] = image
        cfg.setdefault("env", {})
        cfg["env"]["PORT"] = cfg["env"].get("PORT", "5000")
        cfg["onstart"] = "/start_server.sh"
        # Prefer direct SSH runtype so we can scp
        cfg["runtype"] = "ssh_direc"
        # Create
        try:
            # Attempt legacy create (per local docs)
            resp = requests.post(f"{VAST_API_URL}/asks/", headers=self._headers(), json=cfg)
            if resp.status_code == 404:
                # Fallback to orders/ flow: choose an L4 offer and create order
                return self._create_via_orders(cfg)
            resp.raise_for_status()
            data = resp.json()
            new_id = data.get("id")
            if not new_id:
                raise RuntimeError(f"Failed to create instance: {data}")
            self.wait_for_instance(new_id, target_state="running", timeout=900)
            details = self.get_instance_details(new_id)
            self._save_cached_instance({"id": new_id})
            return details
        except requests.HTTPError as he:
            # Try orders/ flow on 404
            if he.response is not None and he.response.status_code == 404:
                return self._create_via_orders(cfg)
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to create Vast instance: {e}")

    def get_instance_details(self, instance_id: str) -> Dict:
        r = requests.get(f"{VAST_API_URL}/instances/{instance_id}/", headers=self._headers())
        r.raise_for_status()
        return r.json()

    def start_instance(self, instance_id: str) -> Dict:
        r = requests.put(f"{VAST_API_URL}/instances/{instance_id}/", headers=self._headers(), json={"state": "running"})
        r.raise_for_status()
        return r.json()

    def stop_instance(self, instance_id: str) -> Dict:
        r = requests.put(f"{VAST_API_URL}/instances/{instance_id}/", headers=self._headers(), json={"state": "stopped"})
        r.raise_for_status()
        return r.json()

    def wait_for_instance(self, instance_id: str, target_state: str = "running", timeout: int = 600) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                d = self.get_instance_details(instance_id)
                if d.get("actual_status") == target_state:
                    return True
            except Exception:
                pass
            time.sleep(10)
        return False

    def _get_ssh_info(self, inst: Dict) -> Tuple[str, int, str]:
        """
        Return (ssh_host, ssh_port, user). Vast usually uses ssh_host ssh.vast.ai and a port.
        """
        ssh_host = inst.get("ssh_host") or inst.get("hostname") or "ssh.vast.ai"
        ssh_port = int(inst.get("ssh_port") or inst.get("ports", {}).get("ssh", 0) or 0)
        user = inst.get("ssh_user") or "root"
        return ssh_host, ssh_port, user

    def _get_http_ip(self, inst: Dict) -> str:
        return inst.get("public_ipaddr") or inst.get("ip_addr") or inst.get("ip") or ""

    def upload_and_plan_paths(self, inst: Dict, local_path: str) -> Tuple[str, str]:
        """
        Upload local file to instance inbox and plan output path.
        Returns (remote_input_path, remote_output_path)
        """
        ssh_host, ssh_port, user = self._get_ssh_info(inst)
        filename = os.path.basename(local_path)
        remote_in = f"/app/inbox/{filename}"
        remote_out = f"/app/outbox/{filename}"
        # Create dirs on remote and upload
        # We use ssh to create directories
        subprocess.run(["ssh", "-p", str(ssh_port), f"{user}@{ssh_host}", "mkdir -p /app/inbox /app/outbox"], check=False)
        # scp upload
        scp_cmd = ["scp", "-P", str(ssh_port), local_path, f"{user}@{ssh_host}:{remote_in}"]
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"scp upload failed: {result.stderr}")
        return remote_in, remote_out

    def submit_job(self, inst: Dict, remote_in: str, remote_out: str) -> str:
        ip = self._get_http_ip(inst)
        if not ip:
            raise RuntimeError("Instance public IP not found")
        url = f"http://{ip}:5000/upscale"
        r = requests.post(url, json={"input_path": remote_in, "output_path": remote_out}, timeout=30)
        if r.status_code not in (200, 202):
            raise RuntimeError(f"Failed to submit job: {r.text}")
        data = r.json()
        return str(data.get("job_id"))

    def job_status(self, inst: Dict, job_id: str) -> str:
        ip = self._get_http_ip(inst)
        r = requests.get(f"http://{ip}:5000/job/{job_id}", timeout=10)
        if r.status_code != 200:
            return "failed"
        data = r.json()
        return data.get("status", "failed")

    def download_result(self, inst: Dict, remote_out: str, local_dir: str) -> str:
        ssh_host, ssh_port, user = self._get_ssh_info(inst)
        os.makedirs(local_dir, exist_ok=True)
        filename = os.path.basename(remote_out)
        local_path = os.path.join(local_dir, filename)
        scp_cmd = ["scp", "-P", str(ssh_port), f"{user}@{ssh_host}:{remote_out}", local_path]
        result = subprocess.run(scp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"scp download failed: {result.stderr}")
        return os.path.abspath(local_path)

    def _find_l4_offer(self) -> Dict:
        # Find an L4 bundle offer
        r = requests.get(f"{VAST_API_URL}/bundles/?q=gpu_name:L4", headers=self._headers())
        r.raise_for_status()
        data = r.json()
        # Data structure may vary; select first available offer
        if isinstance(data, dict) and 'offers' in data:
            offers = data['offers']
        else:
            offers = data if isinstance(data, list) else []
        if not offers:
            raise RuntimeError("No L4 offers found via Vast API bundles endpoint")
        return offers[0]

    def _create_via_orders(self, cfg: Dict) -> Dict:
        """Create instance by creating an order for an L4 offer."""
        offer = self._find_l4_offer()
        ask_id = offer.get('id') or offer.get('ask_id')
        if not ask_id:
            raise RuntimeError("Selected L4 offer has no id/ask_id")
        order_payload = {
            "ask_id": ask_id,
            "image": cfg.get("image"),
            "disk": cfg.get("disk", 32.0),
            "onstart": cfg.get("onstart", "/start_server.sh"),
            "env": cfg.get("env", {}),
        }
        r = requests.post(f"{VAST_API_URL}/orders/", headers=self._headers(), json=order_payload)
        r.raise_for_status()
        od = r.json()
        # Try to extract instance id directly if provided
        inst_id = od.get('instance_id') or od.get('instance') or None
        if inst_id:
            self.wait_for_instance(inst_id, target_state="running", timeout=900)
            details = self.get_instance_details(inst_id)
            self._save_cached_instance({"id": inst_id})
            return details
        # Otherwise, poll instances to find a running one
        for _ in range(60):
            all_inst = requests.get(f"{VAST_API_URL}/instances/", headers=self._headers())
            all_inst.raise_for_status()
            arr = all_inst.json()
            if isinstance(arr, dict) and 'instances' in arr:
                arr = arr['instances']
            # Pick first running instance
            for it in arr or []:
                if (it.get('actual_status') == 'running'):
                    self._save_cached_instance({"id": it.get('id')})
                    return it
            time.sleep(10)
        raise RuntimeError("Order created but no running instance found after waiting")

    def stop_instance_if_idle(self):
        cached = self._load_cached_instance()
        instance_id = cached.get("id")
        if instance_id:
            # Best-effort stop to save money
            try:
                self.stop_instance(instance_id)
            except Exception:
                pass

    def get_status(self) -> str:
        """Return 'running', 'stopped', or 'unknown' based on cached instance."""
        cached = self._load_cached_instance()
        instance_id = cached.get("id")
        if not instance_id:
            return "stopped"
        try:
            d = self.get_instance_details(instance_id)
            return d.get("actual_status") or "unknown"
        except Exception:
            return "unknown"
