import os
import time

from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY, GBOX_API_KEY, etc.)
load_dotenv()

from intake.pipeline import run_intake
from locator.pipeline import run_locator
from locator.schema import LocatorResult
from patcher.pipeline import run_patcher
from vm_executor.vm_manager import initialize_vm, cleanup_vm


def main():
    # --- Repository configuration ---
    owner = os.getenv("GITHUB_OWNER", "YujieXuGru")
    repo_name = os.getenv("GITHUB_REPO", "Flask_Demo")
    repo_spec = f"{owner}/{repo_name}"
    repo_url = f"https://github.com/{repo_spec}.git"

    initialize_vm()

    try:
        # --- 1. Intake stage ---
        print("Running intake...")
        structured_issues = run_intake(repo_spec)
        if not structured_issues:
            print("No issues found.")
            return

        # --- 2. Locator stage & 3. Patcher stage ---
        for issue in structured_issues:
            print("\n🔍 Intake →", issue)

            locator_res: LocatorResult = run_locator(
                issue=issue,
                repo_url=repo_url
            )
            print("🗺️ Locator →")
            for loc in locator_res.locations:
                print("   ", loc)
            print("   explanation:", locator_res.explanation)

            max_retries = 3
            retry_context = None
            final_patch_state = None

            for attempt in range(max_retries):
                print(f"\n🏗️ Patcher Attempt {attempt + 1}/{max_retries}...")

                workdir = "swe_agent"
                patch_state = run_patcher(
                    issue=issue,
                    locator_res=locator_res,
                    workdir=workdir,
                    context=retry_context  # Pass context from previous failure
                )

                if patch_state.get("applied_ok"):
                    print("✅ Patch applied successfully!")
                    final_patch_state = patch_state
                    break  # Exit the loop on success
                else:
                    print("❌ Patch application failed. Preparing for retry...")
                    # Build context for the next attempt
                    retry_context = {
                        "previous_attempt": {
                            "failed_patch": patch_state.get("patch", ""),
                            "stderr": patch_state.get("stderr", ""),
                            "stdout": patch_state.get("stdout", ""),
                        },
                        "hint": "The previous patch failed to apply. The error is provided in 'stderr'. Please analyze the error and the original patch to generate a new, corrected patch that fixes the underlying issue."
                    }
                    final_patch_state = patch_state  # Store the last failed state

            # After the loop, print the final status
            print("\n🏁 Patcher Final Status →")
            if final_patch_state and final_patch_state.get("applied_ok"):
                print("   branch     :", final_patch_state.get("branch"))
                print("   applied_ok :", True)
            else:
                print("   Failed to apply patch after all retries.")
                print("   applied_ok :", False)
                if final_patch_state:
                    print("   Last stderr:", final_patch_state.get("stderr"))

    finally:
        time.sleep(5000)
        cleanup_vm()


if __name__ == "__main__":
    main()