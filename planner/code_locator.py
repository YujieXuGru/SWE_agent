# planner/code_locator.py

import os
import json
import openai
from typing import List, Dict, Any

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("Please set the OPENAI_API_KEY environment variable")

def locate_with_llm(summary: str, files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Given a list of candidate files (path + content) and a bug summary,
    ask the LLM to recommend where to insert validation or fix code.
    Prints the prompt and the raw model response, then returns a dict:
      { "locations": [...], "explanation": "..." }.
    """
    # Construct the prompt by concatenating each file section
    sections = []
    for f in files:
        sections.append(
            f"--- FILE: {f['path']}\n```python\n{f['content']}\n```"
        )
    all_code = "\n\n".join(sections)

    prompt = (
        "You are a code detective. The bug summary is:\n"
        f"{summary}\n\n"
        "Below are the candidate Python files (with path and content):\n\n"
        f"{all_code}\n\n"
        "Based on the summary, please recommend where (file path, function name "
        "if known, and line number if known) you would insert validation or fix "
        "code. Respond with a JSON object containing two keys:\n"
        "  \"locations\": an array of {\"file\":<path>,\"function\":<name|null>,\"line\":<number|null>},\n"
        "  \"explanation\": a brief English sentence explaining why.\n"
        "Example:\n"
        "{\n"
        "  \"locations\": [\n"
        "    {\"file\": \"app.py\", \"function\": \"post_detail\", \"line\": 27}\n"
        "  ],\n"
        "  \"explanation\": \"In post_detail, before creating a Comment, "
        "we should verify both author and body are non-empty.\"\n"
        "}\n"
    )

    # Print the prompt sent to the model
    print("\n🗣️ Prompt to LLM:\n", prompt)

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You recommend code insertion points based on a bug summary."},
            {"role": "user",   "content": prompt},
        ],
    )

    text = response.choices[0].message.content.strip()

    # Print the raw model response
    print("\n🤖 LLM raw response:\n", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"locations": [], "explanation": ""}
