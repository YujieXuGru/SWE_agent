# locator/llm_location_predictor.py

import os
import json
import openai
from typing import List, Optional

from locator.schema import FileContent, Location, LocatorResult

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set the OPENAI_API_KEY environment variable")

def locate_with_llm(
    summary: str,
    files: List[FileContent],
    context: Optional[dict] = None
) -> LocatorResult:
    """
    Given a bug summary, optional context, and a list of FileContent,
    ask the LLM to recommend where to insert validation or fix code.

    Prints the full prompt and raw model response for debugging.

    Returns:
        LocatorResult:
          - locations: List[Location]
          - explanation: str
          - context: passed-through context
    """
    # 1. Build a composite code section
    sections: List[str] = []
    for f in files:
        sections.append(
            f"--- FILE: {f.path}\n```python\n{f.content}\n```"
        )
    all_code = "\n\n".join(sections)

    # 2. Construct the prompt
    prompt_parts: List[str] = [
        "You are a code detective. The bug summary is:",
        summary,
        ""
    ]
    if context:
        prompt_parts += [
            "Additional context (e.g. previous test logs or failures):",
            json.dumps(context, indent=2),
            ""
        ]
    prompt_parts += [
        "Below are the candidate Python files (with path and content):",
        all_code,
        "",
        "Based on the summary and context, please recommend where to insert validation or fix code.",
        "Respond with a JSON object with two keys:",
        "  \"locations\": an array of {\"file\":<path>,\"function\":<name|null>,\"line\":<number|null>},",
        "  \"explanation\": a brief English sentence explaining why.",
        "",
        "Example:",
        "{",
        "  \"locations\": [",
        "    {\"file\": \"swe_agent/app.py\", \"function\": \"post_detail\", \"line\": 42}",
        "  ],",
        "  \"explanation\": \"In post_detail, before creating a Comment, we must check that both ",
        "author and body fields are non-empty to avoid database errors.\"",
        "}"
    ]
    prompt = "\n".join(prompt_parts)

    # 3. Print prompt for traceability
    print("\n🗣️ Prompt to LLM:\n", prompt)

    # 4. Call the LLM using the new openai-python v1.x interface
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You recommend code insertion points based on a bug summary and optional context."
            },
            { "role": "user", "content": prompt },
        ],
    )
    text = response.choices[0].message.content.strip()

    # 5. Print raw response
    print("\n🤖 LLM raw response:\n", text)

    # 6. Parse JSON into dataclasses
    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        return LocatorResult(locations=[], explanation="", context=context)

    locs: List[Location] = []
    for loc in body.get("locations", []):
        locs.append(Location(
            file=loc.get("file", ""),
            function=loc.get("function"),
            line=loc.get("line")
        ))

    return LocatorResult(
        locations=locs,
        explanation=body.get("explanation", ""),
        context=context
    )
