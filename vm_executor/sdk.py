# executor/sdk.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

class SimpleGboxVM:
    """
    A simple Gbox VM manager that supports:
      - Creating a Linux VM
      - Executing shell commands on the VM
      - Cleaning up (terminating) the VM
    """
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GBOX_API_KEY")
        if not self.api_key:
            raise RuntimeError("Please set the GBOX_API_KEY environment variable")
        self.base_url = "https://gbox.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.box_id: str | None = None

    def create_vm(self) -> dict:
        """
        Create a Linux VM and wait for it to be ready.
        Returns the VM info as a dict.
        """
        print("🚀 Creating Linux VM...")
        url = f"{self.base_url}/boxes/linux"
        payload = {
            "wait": True,
            "config": {
                "expiresIn": "30m"  # auto-expire after 30 minutes
            }
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        info = resp.json()
        self.box_id = info["id"]

        print("✅ Linux VM created successfully!")
        print(f"📦 VM ID: {self.box_id}")
        print(f"🖥️  OS version: {info['config']['os']['version']}")
        print(f"⏰  Expiration time: {info['expiresAt']}")
        return info

    def run_command(self, command: str) -> dict:
        """
        Execute a shell command on the VM.
        Returns a dict containing 'exitCode', 'stdout', and 'stderr'.
        """
        if not self.box_id:
            raise RuntimeError("VM not created. Call create_vm() first.")

        print(f"\n💻 Executing on VM: {command}")
        url = f"{self.base_url}/boxes/{self.box_id}/commands"
        payload = {
            "commands": command,
            "timeout": "30s"
        }
        resp = requests.post(url, json=payload, headers=self.headers)
        resp.raise_for_status()
        result = resp.json()

        print(f"📋 Exit code: {result.get('exitCode')}")
        if result.get("stdout"):
            print("📤 stdout:")
            print(result["stdout"])
        if result.get("stderr"):
            print("❌ stderr:")
            print(result["stderr"])

        return result

    def cleanup(self) -> None:
        """
        Terminate the VM and clean up resources.
        """
        if not self.box_id:
            return

        print(f"\n🧹 Cleaning up VM {self.box_id}...")
        url = f"{self.base_url}/boxes/{self.box_id}/terminate"
        payload = {"wait": True}
        try:
            resp = requests.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()
            print("✅ VM terminated successfully")
        except Exception as e:
            print(f"⚠️ Error while cleaning up VM: {e}")
