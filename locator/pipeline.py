# locator/pipeline.py

import logging
from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from locator.schema import FileContent, LocatorResult, Location
from vm_executor.vm_manager import setup_workspace, clone_repository
from locator.file_scanner      import scan_py_files
from locator.llm_location_predictor import locate_with_llm
from intake.schema             import StructuredIssue

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LocatorState(TypedDict, total=False):
    """
    State schema for the locator pipeline.
    """
    issue: StructuredIssue      # input issue
    repo_url: str               # e.g. "https://github.com/foo/bar.git"
    context: Optional[dict]     # optional context for re-invocation
    workdir: str                # VM workspace path
    files: List[FileContent]    # all scanned FileContent
    locations: List[dict]       # intermediate raw locations (dataclass created later)
    explanation: str            # natural-language reasoning

def scan_py_files_node(state: LocatorState) -> dict:
    logger.info("🔍 scan_py_files input: workdir=%s", state["workdir"])
    out = scan_py_files(state["workdir"])
    logger.info("✅ scan_py_files output: %d files", len(out["files"]))
    return out

def locate_code_node(state: LocatorState) -> dict:
    summary   = state["issue"].summary
    files     = state["files"]
    context   = state.get("context")
    logger.info("[locate_code] summary=%r, context=%s, #files=%d",
                summary, context, len(files))

    result = locate_with_llm(summary=summary, files=files, context=context)
    # unpack LocatorResult into LangGraph state dict
    out = {
        "locations":   [loc.__dict__ for loc in result.locations],
        "explanation": result.explanation
    }
    logger.info("[locate_code] output: %s", out)
    return out

def build_locator_graph() -> StateGraph:
    """
    Construct the locator DAG:
      START → setup_workspace → clone_repository → scan_py_files
             → locate_code → END
    """
    g = StateGraph(LocatorState)

    g.add_node("setup_workspace",  setup_workspace)
    g.add_node("clone_repository", clone_repository)
    g.add_node("scan_py_files",    scan_py_files_node)
    g.add_node("locate_code",      locate_code_node)

    g.add_edge(START,              "setup_workspace")
    g.add_edge("setup_workspace",  "clone_repository")
    g.add_edge("clone_repository", "scan_py_files")
    g.add_edge("scan_py_files",    "locate_code")
    g.add_edge("locate_code",      END)

    return g

def run_locator(issue: StructuredIssue,
                repo_url: str,
                context: Optional[dict] = None) -> LocatorResult:
    """
    Execute the locator pipeline end-to-end.
    Returns a LocatorResult containing:
      - locations: List[Location]
      - explanation: str
      - context: same dict you passed in
    """
    logger.info("🚀 Running locator for issue #%s", issue.id)
    graph = build_locator_graph().compile()

    # Prepare initial state
    init = {
        "issue":    issue,
        "repo_url": repo_url,
    }
    if context:
        init["context"] = context

    # Invoke the graph
    final_state = graph.invoke(init)
    logger.info("✅ Locator final state: %s", {
        "locations": final_state["locations"],
        "explanation": final_state["explanation"]
    })

    # Build LocatorResult
    # return LocatorResult(
    #     locations=[  # convert raw dicts into Location
    #         FileContent(**{"path": loc["file"], "content": ""})  # placeholder
    #         for loc in final_state["locations"]
    #     ],
    #     explanation=final_state["explanation"],
    #     context=context
    # )

    locs = [
        Location(
            file=loc_dict["file"],
            function=loc_dict.get("function"),
            line=loc_dict.get("line")
        )
        for loc_dict in final_state["locations"]
    ]

    # 2. 返回 LocatorResult
    return LocatorResult(
        locations=locs,
        explanation=final_state["explanation"],
        context=context
    )
