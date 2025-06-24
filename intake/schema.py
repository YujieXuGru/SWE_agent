# intake/schema.py
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class RawIssue:
    id: int
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    created_at: str
    updated_at: str

@dataclass
class Entity:
    file: Optional[str]
    function: Optional[str]
    line: Optional[int]
    repro_cmd: Optional[str]

@dataclass
class StructuredIssue:
    id: int
    intent: str            # e.g. "BUG_FIX"
    is_crash: bool
    entities: List[Entity]
    summary: str
