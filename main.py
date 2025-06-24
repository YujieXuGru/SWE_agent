# main.py

from dotenv import load_dotenv
load_dotenv()

from intake.pipeline   import run_intake
from locator.pipeline  import run_planner

def main():
    # 1. 指定 GitHub 仓库（owner/repo）
    owner = "YujieXuGru"
    repo  = "Flask_Demo"
    repo_spec = f"{owner}/{repo}"
    repo_url  = f"https://github.com/{repo_spec}.git"

    # 2. Intake 阶段：把原始 Issue 转成 StructuredIssue
    structured_issues = run_intake(repo_spec)
    for si in structured_issues:
        print("🔍 Intake ->", si)

        # 3. Planner 阶段：为这个 Issue 生成 TaskDescriptor 列表
        tasks = run_planner(si, repo_url)
        print("🗺  Planner ->")
        for t in tasks:
            print("   ", t)

        # （后续你可以在这里把 tasks 发给 Executor 去实际执行）
        print()

if __name__ == "__main__":
    main()
