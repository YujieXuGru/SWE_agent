# main.py

import os
from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY, GBOX_API_KEY, etc.)
load_dotenv()

# 1. Intake: fetch & structure GitHub Issues
from intake.pipeline import run_intake

# 2. Locator: scan the repo, invoke LLM to locate insertion points
from locator.pipeline import run_locator
from locator.schema   import LocatorResult

from vm_executor.vm_manager import initialize_vm, cleanup_vm

def main():
    # ——— Repository configuration ———
    owner     = os.getenv("GITHUB_OWNER", "YujieXuGru")
    repo_name = os.getenv("GITHUB_REPO",  "Flask_Demo")
    repo_spec = f"{owner}/{repo_name}"
    repo_url  = f"https://github.com/{repo_spec}.git"
    initialize_vm()

    # ——— 1. Intake stage ———
    print("Running intake...")
    structured_issues = run_intake(repo_spec)
    if not structured_issues:
        print("No issues found.")
        return

    # ——— 2. Locator stage ———
    for issue in structured_issues:
        print("\n🔍 Intake →", issue)

        locator_res: LocatorResult = run_locator(
            issue=issue,
            repo_url=repo_url,
            context=None  # optional, for future reruns with test logs
        )
        print("🗺 Locator →")
        for loc in locator_res.locations:
            print("   ", loc)
        print("   explanation:", locator_res.explanation)

        # (Next steps: pass locator_res into your task_planner, patcher, etc.)
        cleanup_vm()
if __name__ == "__main__":
    main()
