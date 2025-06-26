# executor/git_manager.py

from vm_executor.vm_manager import get_vm

def checkout_branch(workdir: str, branch: str) -> None:
    """
    Idempotent branch checkout:
      - if the branch exists locally, just switch to it
      - otherwise create a new one based on the current HEAD
    """
    vm = get_vm()
    # 判断分支是否存在
    check_cmd = (
        f"cd {workdir} && "
        f"git rev-parse --verify {branch}"
    )
    res = vm.run_command(check_cmd)
    if res["exitCode"] == 0:
        # 分支已存在，直接切换
        vm.run_command(f"cd {workdir} && git checkout {branch}")
    else:
        # 分支不存在，创建并切换
        vm.run_command(f"cd {workdir} && git checkout -b {branch}")

def write_diff_file(diff: str) -> None:
    vm = get_vm()
    here_doc = f"""cat << 'EOF' > /tmp/patch.diff
{diff}
EOF"""
    vm.run_command(here_doc)

def apply_diff(workdir: str) -> dict:
    vm = get_vm()
    result = vm.run_command(f"cd {workdir} && git apply -p2 /tmp/patch.diff")
    return {
        "applied_ok": result.get("exitCode", 1) == 0,
        "stdout":     result.get("stdout", ""),
        "stderr":     result.get("stderr", "")
    }
