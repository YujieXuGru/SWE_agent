# intake/pipeline.py

import logging
from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END

from .fetcher      import fetch_issues
from .cleaner      import clean_text
from .classifier   import classify_intent, detect_crash
from .extractor    import extract_entities
from .schema       import RawIssue, Entity, StructuredIssue
from .summarizer   import summarize_issue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 1. Define the state schema for LangGraph
class IntakeState(TypedDict, total=False):
    input_issue: RawIssue
    cleaned_text: str
    intent: str
    is_crash: bool
    entities: List[Entity]
    summary: str
    structured_issue: StructuredIssue


# 2. Node implementations with logging

def clean_text_node(state):
    logger.info("[clean_text] input: %s", state["input_issue"].body)
    out = {"cleaned_text": clean_text(state["input_issue"].body)}
    logger.info("[clean_text] output: %s", out)
    return out

def classify_intent_node(state):
    logger.info("[classify_intent] input: %s", state["cleaned_text"])
    out = {"intent": classify_intent(state["cleaned_text"])}
    logger.info("[classify_intent] output: %s", out)
    return out

def detect_crash_node(state):
    logger.info("[detect_crash] input: %s", state["cleaned_text"])
    out = {"is_crash": detect_crash(state["cleaned_text"])}
    logger.info("[detect_crash] output: %s", out)
    return out

def extract_entities_node(state):
    logger.info("[extract_entities] input: %s", state["cleaned_text"])
    out = {"entities": extract_entities(state["cleaned_text"])}
    logger.info("[extract_entities] output: %s", out)
    return out

def summarize_issue_node(state):
    logger.info("[summarize_issue] input: %s", state["cleaned_text"])
    out = summarize_issue(state["cleaned_text"])
    logger.info("[summarize_issue] output: %s", out)
    return out

def compose_structured_node(state):
    # Include summary in the StructuredIssue
    structured = StructuredIssue(
        id=state["input_issue"].id,
        intent=state["intent"],
        is_crash=state["is_crash"],
        entities=state["entities"],
        summary=state["summary"],
    )
    out = {"structured_issue": structured}
    logger.info("[compose_structured] output: %s", out)
    return out


# 3. Node specification: name -> (handler function, dependencies)
NODE_SPECS = {
    "clean_text":        (clean_text_node,        ["input_issue"]),
    "classify_intent":   (classify_intent_node,   ["cleaned_text"]),
    "detect_crash":      (detect_crash_node,      ["cleaned_text"]),
    "extract_entities":  (extract_entities_node,  ["cleaned_text"]),
    "summarize_issue":   (summarize_issue_node,   ["cleaned_text"]),
    "compose_structured":(
        compose_structured_node,
        ["classify_intent", "detect_crash", "extract_entities", "summarize_issue"]
    ),
}


# 4. Build the StateGraph
def build_intake_graph() -> StateGraph:
    graph = StateGraph(IntakeState)

    # Register all nodes
    for name, (handler, _) in NODE_SPECS.items():
        graph.add_node(name, handler)

    # Define edges: first step is cleaning
    graph.add_edge(START, "clean_text")

    # Parallel steps after cleaning
    graph.add_edge("clean_text", "classify_intent")
    graph.add_edge("clean_text", "detect_crash")
    graph.add_edge("clean_text", "extract_entities")
    graph.add_edge("clean_text", "summarize_issue")

    # Join into compose_structured
    graph.add_edge("classify_intent", "compose_structured")
    graph.add_edge("detect_crash",    "compose_structured")
    graph.add_edge("extract_entities","compose_structured")
    graph.add_edge("summarize_issue", "compose_structured")

    # Final node leads to END
    graph.add_edge("compose_structured", END)

    return graph


# 5. Main execution function: fetch issues -> run pipeline -> return results
def run_intake(repo: str) -> List[StructuredIssue]:
    raw_list = fetch_issues(repo)
    compiled = build_intake_graph().compile()

    results: List[StructuredIssue] = []
    for raw in raw_list:
        logger.info("🔍 Processing issue #%s", raw.id)
        state = compiled.invoke({"input_issue": raw})
        logger.info("✅ Final state: %s", state)
        results.append(state["structured_issue"])

    return results
