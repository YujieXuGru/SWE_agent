from intake.pipeline import run_intake
from dotenv import load_dotenv
load_dotenv()



def main():
    repo = "YujieXuGru/Flask_Demo"
    # 1. Intake
    structured = run_intake(repo)
    for si in structured:
        print("Intake ->", si)
    # 2. Planner



if __name__ == "__main__":
    main()