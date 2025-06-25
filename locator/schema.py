# locator/schema.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class FileContent:
    """
    Represents the full text of a Python source file, with line numbers.
    """
    path: str         # path within the workspace, e.g. "swe_agent/app.py"
    content: str      # full file content, each line prefixed with its line number

@dataclass
class Location:
    """
    A single recommendation of where to insert a validation or fix.
    """
    file: str               # file path relative to workspace
    function: Optional[str] # name of the function/method, or None
    line: Optional[int]     # 1-based line number, or None

@dataclass
class LocatorResult:
    """
    The output of a locator pipeline run.

    - locations: list of recommended insertion points
    - explanation: natural language reasoning for these recommendations
    - context: optional arbitrary dict to carry e.g. test logs or previous state
    """
    locations: List[Location]
    explanation: str
    context: Optional[Dict[str, Any]] = None
