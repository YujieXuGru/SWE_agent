# planner/vm_manager.py

from vm_executor.sdk import SimpleGboxVM

_vm_client: SimpleGboxVM | None = None

def get_vm() -> SimpleGboxVM:
    global _vm_client
    if _vm_client is None:
        _vm_client = SimpleGboxVM()
        _vm_client.create_vm()
    return _vm_client

def setup_workspace(state) -> dict:
    vm = get_vm()
    workdir = "swe_agent"
    vm.run_command(f"mkdir -p {workdir}")
    return {"workdir": workdir}

def clone_repository(state) -> dict:
    repo_url = state["repo_url"]
    workdir  = state["workdir"]
    vm = get_vm()
    vm.run_command(f"git clone {repo_url} {workdir}")
    return {}

def read_file_numbered(path: str) -> str:
    """
    Read a file on the VM, returning every line prefixed with its line number.
    Uses `nl -ba` so blank lines are numbered too.
    """
    vm = get_vm()
    res = vm.run_command(f"nl -ba {path}")
    # res["stdout"] already contains numbered lines
    return res["stdout"]
