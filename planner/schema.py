# planner/schema.py

from dataclasses import dataclass
from typing import Literal, List

@dataclass
class TaskDescriptor:
    name: str
    type: Literal["shell", "llm"]
    payload: str
    depends_on: List[str]
