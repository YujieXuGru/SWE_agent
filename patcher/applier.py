from vm_executor.vm_manager import get_vm

def apply_patch(diff: str, workdir: str) -> dict:
    """
    Apply the unified diff to the given workdir on the VM using the 'patch' command.
    Returns applied_ok, stdout, stderr.
    """
    vm = get_vm()


    patch_file_path = "/tmp/agent.patch"
    here_doc = f"""cat << 'EOF' > {patch_file_path}
{diff}
EOF"""
    vm.run_command(here_doc)

    cmd = f"cd {workdir} && patch -p2 -u --forward < {patch_file_path}"
    result = vm.run_command(cmd)

    # Clean up the temporary patch file
    vm.run_command(f"rm {patch_file_path}")

    return {
        "applied_ok": result.get("exitCode", 1) == 0,
        "stdout":     result.get("stdout", ""),
        "stderr":     result.get("stderr", "")
    }