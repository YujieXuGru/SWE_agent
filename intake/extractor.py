# intake/extractor.py

import os
import json
import openai
import logging
from typing import List
from .schema import Entity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_entities(cleaned_text: str) -> List[Entity]:
    """
    Call OpenAI to convert issue text into a list of structured entities.
    Performs strict JSON extraction and error handling.
    """
    prompt = (
        "Please extract the following fields as a JSON array:\n"
        "- file: filename\n"
        "- function: function or method name\n"
        "- line: line number (optional)\n"
        "- repro_cmd: reproduction command (optional)\n"
        "If a field is missing, set its value to null.\n\n"
        f"```{cleaned_text}```"
    )

    # Call the new OpenAI API
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an entity extractor. Output only a strict JSON array, no extra text."
            },
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content.strip()
    logger.info("LLM raw response: %s", content)

    # Locate the outermost [ ... ] block
    start = content.find("[")
    end = content.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"Could not find JSON array in model response: {content!r}")

    json_str = content[start:end]

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        # Log the problematic JSON snippet for debugging
        logger.error("JSON parsing failed: %s\nSnippet: %r", e, json_str)
        raise ValueError(f"JSONDecodeError: {e.msg}") from e

    # Convert to Entity instances
    entities: List[Entity] = []
    for item in parsed:
        try:
            entities.append(Entity(**item))
        except TypeError as te:
            logger.error("Failed to construct Entity, mismatched fields: %r", item)
            raise

    return entities
