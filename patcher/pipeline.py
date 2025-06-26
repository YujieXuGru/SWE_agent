# patcher/pipeline.py

import logging
from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END

from intake.schema       import StructuredIssue
from locator.schema      import LocatorResult
from patcher.generator   import generate_patch

from vm_executor.git_manager import (
    checkout_branch,
    write_diff_file,
    apply_diff,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PatcherState(TypedDict, total=False):
    issue:       StructuredIssue
    locator_res: LocatorResult
    workdir:     str

    patch:       str
    branch:      str
    applied_ok:  bool
    stdout:      str
    stderr:      str

def generate_patch_node(state: PatcherState) -> dict:
    diff = generate_patch(
        summary=state["issue"].summary,
        locations=state["locator_res"].locations,
        explanation=state["locator_res"].explanation,
        context=state["locator_res"].context
    )
    logger.info("[generate_patch] diff length=%d", len(diff))
    return {"patch": diff}

def create_branch_node(state: PatcherState) -> dict:
    branch = f"fix/issue-{state['issue'].id}"
    checkout_branch(state["workdir"], branch)
    logger.info("[create_branch] branch ready=%s", branch)
    return {"branch": branch}

def apply_patch_node(state: PatcherState) -> dict:
    write_diff_file(state["patch"])
    res = apply_diff(state["workdir"])
    logger.info("[apply_patch] applied_ok=%s", res["applied_ok"])
    return {
        "applied_ok": res["applied_ok"],
        "stdout":     res["stdout"],
        "stderr":     res["stderr"]
    }

def build_patcher_graph() -> StateGraph:
    g = StateGraph(PatcherState)
    g.add_node("generate_patch", generate_patch_node)
    g.add_node("create_branch",  create_branch_node)
    g.add_node("apply_patch",    apply_patch_node)

    g.add_edge(START,            "generate_patch")
    g.add_edge("generate_patch", "create_branch")
    g.add_edge("create_branch",  "apply_patch")
    g.add_edge("apply_patch",    END)
    return g

def run_patcher(
    issue: StructuredIssue,
    locator_res: LocatorResult,
    workdir: str
) -> PatcherState:
    graph = build_patcher_graph().compile()
    init = {
        "issue":       issue,
        "locator_res": locator_res,
        "workdir":     workdir
    }
    final_state: PatcherState = graph.invoke(init)
    return final_state
