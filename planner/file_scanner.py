# planner/file_scanner.py

import logging
from typing import Dict, List
from planner.vm_manager import get_vm

logger = logging.getLogger(__name__)

def scan_py_files(workdir: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Scan the given workspace for all .py files and read their contents.
    Returns a dict with key 'files'; each item is {'path': ..., 'content': ...}.
    """
    vm = get_vm()
    # List all .py file paths
    result = vm.run_command(f"find {workdir} -type f -name '*.py'")
    paths = result["stdout"].splitlines()

    files = []
    for path in paths:
        cat = vm.run_command(f"cat {path}")
        content = cat["stdout"]
        files.append({"path": path, "content": content})

    logger.info("Scanned and read %d Python files", len(files))
    return {"files": files}
