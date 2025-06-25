# locator/vm_manager.py

from vm_executor.sdk import SimpleGboxVM

_vm_client: SimpleGboxVM | None = None
from typing import Dict, Optional


def initialize_vm(api_key: Optional[str] = None) -> SimpleGboxVM:
    """
    Create (or reuse) a single Gbox VM. Call once at program startup.
    Returns the VM client.
    """
    global _vm_client
    if _vm_client is None:
        _vm_client = SimpleGboxVM(api_key)
        _vm_client.create_vm()
    return _vm_client

def get_vm() -> SimpleGboxVM:
    """
    Return the already-initialized VM.
    Raises if initialize_vm() was never called.
    """
    global _vm_client
    if _vm_client is None:
        raise RuntimeError("VM not initialized; call initialize_vm() first")
    return _vm_client

def cleanup_vm() -> None:
    """
    Terminate and clean up the VM. Call once at program shutdown.
    """
    global _vm_client
    if _vm_client:
        _vm_client.cleanup()
        _vm_client = None


# ─── LangGraph node implementations ───────────────────────────────────────────

def setup_workspace(state: Dict) -> Dict[str, str]:
    """
    LangGraph node: ensure the remote VM has a workspace directory.
    Returns {'workdir': 'swe_agent'}.
    """
    vm = get_vm()
    workdir = "swe_agent"
    vm.run_command(f"mkdir -p {workdir}")
    return {"workdir": workdir}

def clone_repository(state: Dict) -> Dict:
    """
    LangGraph node: clone the target GitHub repo into the workspace.
    Expects state['repo_url'] and state['workdir'].
    Returns {} (no new state keys).
    """
    vm = get_vm()
    repo_url = state["repo_url"]
    workdir  = state["workdir"]
    vm.run_command(f"git clone {repo_url} {workdir}")
    return {}

def read_file_numbered(path: str) -> str:
    """
    Helper: read a file on the VM with line numbers (including blank lines).
    Uses `nl -ba` so that blank lines are also numbered.
    Returns the raw stdout as a single string.
    """
    vm = get_vm()
    res = vm.run_command(f"nl -ba {path}")
    return res["stdout"]
