# patcher/applier.py

from vm_executor.vm_manager import get_vm

def apply_patch(diff: str, workdir: str) -> dict:
    """
    Apply the unified diff to the given workdir on the VM.
    Returns applied_ok, stdout, stderr.
    """
    vm = get_vm()

    # Write diff to /tmp/patch.diff
    here_doc = f"""cat << 'EOF' > /tmp/patch.diff
{diff}
EOF"""
    vm.run_command(here_doc)

    # Apply patch on current branch
    cmd = f"cd {workdir} && git apply /tmp/patch.diff"
    result = vm.run_command(cmd)

    return {
        "applied_ok": result.get("exitCode", 1) == 0,
        "stdout":     result.get("stdout", ""),
        "stderr":     result.get("stderr", "")
    }
