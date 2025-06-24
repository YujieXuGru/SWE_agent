# planner/pipeline.py

from typing import List, TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END

from planner.schema        import TaskDescriptor
from planner.vm_manager    import setup_workspace, clone_repository
from planner.file_scanner  import scan_py_files
from planner.code_locator  import locate_with_llm
from intake.schema         import StructuredIssue

class PlannerState(TypedDict, total=False):
    issue: StructuredIssue
    repo_url: str
    workdir: str
    files: List[Dict[str, str]]
    locations: List[Dict[str, Any]]
    explanation: str
    tasks: List[TaskDescriptor]

def scan_py_files_node(state):
    # Read all Python files and their contents into state["files"]
    return scan_py_files(state["workdir"])

def locate_code_node(state):
    summary = state["issue"].summary
    files   = state["files"]
    entities = state["issue"].entities or []

    # If intake extracted a specific file, prioritize it; otherwise take the first 5 files
    if any(e.file for e in entities):
        candidates = []
        for e in entities:
            for f in files:
                if f["path"].endswith(e.file):
                    candidates.append(f)
        # Fill up to 5 candidates
        for f in files:
            if len(candidates) >= 5:
                break
            if f not in candidates:
                candidates.append(f)
    else:
        candidates = files[:5]

    # Call the LLM to recommend insertion points
    result = locate_with_llm(summary, candidates)
    return {
        "locations":   result.get("locations", []),
        "explanation": result.get("explanation", "")
    }

def compose_tasks_node(state):
    import json
    payload_obj = {
        "locations":    state["locations"],
        "explanation":  state["explanation"]
    }
    payload = json.dumps(payload_obj, indent=2)
    return {"tasks": [
        TaskDescriptor(
            name="locate",
            type="llm",
            payload=payload,
            depends_on=[]
        )
    ]}

def build_planner_graph() -> StateGraph:
    graph = StateGraph(PlannerState)
    graph.add_node("setup_workspace",   setup_workspace)
    graph.add_node("clone_repository",  clone_repository)
    graph.add_node("scan_py_files",     scan_py_files_node)
    graph.add_node("locate_code",       locate_code_node)
    graph.add_node("compose_tasks",     compose_tasks_node)

    graph.add_edge(START,               "setup_workspace")
    graph.add_edge("setup_workspace",   "clone_repository")
    graph.add_edge("clone_repository",  "scan_py_files")
    graph.add_edge("scan_py_files",     "locate_code")
    graph.add_edge("locate_code",       "compose_tasks")
    graph.add_edge("compose_tasks",     END)
    return graph

def run_planner(issue: StructuredIssue, repo_url: str) -> List[TaskDescriptor]:
    graph = build_planner_graph().compile()
    state = graph.invoke({
        "issue":    issue,
        "repo_url": repo_url
    })
    return state["tasks"]
