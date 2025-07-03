from vm_executor.vm_manager import get_vm

def checkout_branch(workdir: str, branch: str) -> None:
    """
    Idempotent branch checkout:
      - if the branch exists locally, just switch to it
      - otherwise create a new one based on the current HEAD
    """
    vm = get_vm()
    check_cmd = (
        f"cd {workdir} && "
        f"git rev-parse --verify {branch}"
    )
    res = vm.run_command(check_cmd)
    if res["exitCode"] == 0:
        # Branch exists, checkout
        vm.run_command(f"cd {workdir} && git checkout {branch}")
    else:
        # Branch does not exist, create and checkout
        vm.run_command(f"cd {workdir} && git checkout -b {branch}")

