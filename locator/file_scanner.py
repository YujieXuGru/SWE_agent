# locator/file_scanner.py

import logging
from typing import Dict, List
from vm_executor.vm_manager import get_vm, read_file_numbered
from locator.schema     import FileContent

logger = logging.getLogger(__name__)

def scan_py_files(workdir: str) -> Dict[str, List[FileContent]]:
    """
    Scan the VM workspace for all .py files and read their contents with line numbers.

    Returns:
        {
          'files': [
             FileContent(path='swe_agent/app.py', content=' 1 from flask import ...'),
             ...
          ]
        }
    """
    vm = get_vm()
    # List all .py file paths
    result = vm.run_command(f"find {workdir} -type f -name '*.py'")
    paths = result["stdout"].splitlines()

    files: List[FileContent] = []
    for p in paths:
        numbered = read_file_numbered(p)
        files.append(FileContent(path=p, content=numbered))

    logger.info("Scanned and read %d Python files", len(files))
    return {"files": files}
