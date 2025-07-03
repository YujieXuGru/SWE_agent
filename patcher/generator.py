import os
import json
import openai
from typing import List, Optional
from collections import OrderedDict

from locator.schema import Location
from vm_executor.vm_manager import get_vm, read_file_numbered

# Load your OpenAI API key (ensure OPENAI_API_KEY is set)
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set the OPENAI_API_KEY environment variable")


def generate_patch(
        summary: str,
        locations: List[Location],
        explanation: str,
        context: Optional[dict] = None
) -> str:
    """
    Generate a clean, raw unified diff patch via the LLM.
    """
    # (The first part of the function remains the same)
    unique_files = OrderedDict((loc.file, None) for loc in locations)
    vm = get_vm()
    code_sections = []
    for path in unique_files:
        numbered_code = read_file_numbered(path)
        code_sections.append(
            f"--- FULL FILE: {path} ---\n"
            f"```python\n{numbered_code}```"
        )
    all_code = "\n\n".join(code_sections)

    loc_lines = [
        f"- File `{loc.file}`, function `{loc.function}`, around line {loc.line}"
        for loc in locations
    ]
    loc_block = "\n".join(loc_lines)

    prompt = f"""
You are a software patch generator.

Issue summary:
{summary}

Locator explanation:
{explanation}

Identified fix locations:
{loc_block}

Below are the full source files (with line numbers) for those locations:
Attention: the line numbers are for reference only and should not be included in the patch.
The path should be a/swe_agent/filepath and b/swe_agent/filepath.

{all_code}
"""
    if context:
        prompt += f"""

Additional context (e.g. previous test failures):
{json.dumps(context, indent=2)}
"""
    prompt += """
Generate a unified diff patch that implements the necessary validation or fixes
at the above locations. **Only output the raw unified diff**, without any
``` fences or Markdown formatting, and with file paths relative to the
repository root. The before/after file paths in the diff header should be identical.
"""
    print("\n🗣️ Patch Generation Prompt:\n")
    print(prompt)
    print("\n—— End of prompt ——\n")

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate raw unified diff patches."},
            {"role": "user", "content": prompt},
        ],
    )
    raw_diff = response.choices[0].message.content
    print("\n🤖 DDEBUG: Raw LLM Response:\n", raw_diff)

    lines = raw_diff.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]

    first_line_index = -1
    for i, line in enumerate(lines):
        if line.startswith("diff --git") or line.startswith("---"):
            first_line_index = i
            break

    if first_line_index != -1:
        lines = lines[first_line_index:]
    else:
        lines = []  # If no valid start found, result is an empty patch

    cleaned_diff = "\n".join(lines).rstrip() + "\n"

    print("\n🤖 Cleaned diff to apply:\n")
    print(cleaned_diff)
    print("\n—— End of cleaned diff ——\n")

    return cleaned_diff