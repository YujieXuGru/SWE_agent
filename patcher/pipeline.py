import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from intake.schema import StructuredIssue
from locator.schema import LocatorResult
from patcher.generator import generate_patch
from patcher.applier import apply_patch
from vm_executor.git_manager import checkout_branch

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PatcherState(TypedDict, total=False):
    issue: StructuredIssue
    locator_res: LocatorResult
    workdir: str
    patch: str
    branch: str
    applied_ok: bool
    stdout: str
    stderr: str
    ## Add a context field to the state so it can be passed to the generator.
    context: Optional[dict]

def generate_patch_node(state: PatcherState) -> dict:
    """This node now passes retry context to the LLM if it exists."""
    diff = generate_patch(
        summary=state["issue"].summary,
        locations=state["locator_res"].locations,
        explanation=state["locator_res"].explanation,
        # Get context from the state and pass it to the generator.
        # On the first run, this will be None. On retries, it will contain error info.
        context=state.get("context")
    )
    logger.info("[generate_patch] diff length=%d", len(diff))
    return {"patch": diff}

def create_branch_node(state: PatcherState) -> dict:
    branch = f"fix/issue-{state['issue'].id}"
    checkout_branch(state["workdir"], branch)
    logger.info("[create_branch] branch ready=%s", branch)
    return {"branch": branch}

def apply_patch_node(state: PatcherState) -> dict:
    res = apply_patch(
        diff=state["patch"],
        workdir=state["workdir"]
    )
    logger.info("[apply_patch] applied_ok=%s", res["applied_ok"])
    if not res["applied_ok"]:
        logger.error("[apply_patch] stderr: %s", res["stderr"])
    return {
        "applied_ok": res["applied_ok"],
        "stdout": res["stdout"],
        "stderr": res["stderr"]
    }

def build_patcher_graph() -> StateGraph:
    # The graph structure itself does not need to change.
    g = StateGraph(PatcherState)
    g.add_node("generate_patch", generate_patch_node)
    g.add_node("create_branch", create_branch_node)
    g.add_node("apply_patch", apply_patch_node)

    g.add_edge(START, "generate_patch")
    g.add_edge("generate_patch", "create_branch")
    g.add_edge("create_branch", "apply_patch")
    g.add_edge("apply_patch", END)
    return g

# optional context dictionary.
def run_patcher(
    issue: StructuredIssue,
    locator_res: LocatorResult,
    workdir: str,
    context: Optional[dict] = None
) -> PatcherState:
    graph = build_patcher_graph().compile()
    # includes the context.
    init = {
        "issue": issue,
        "locator_res": locator_res,
        "workdir": workdir,
        "context": context
    }
    final_state: PatcherState = graph.invoke(init)
    return final_state