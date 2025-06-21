# intake/classifier.py

import os
import openai

# Load OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def classify_intent(cleaned_text: str) -> str:
    """
    Use an LLM to classify the intent of an issue.
    Returns one of: BUG_FIX, FEATURE_REQUEST, PERFORMANCE, or DOCS.
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an issue classifier. "
                    "Only respond with one of: BUG_FIX, FEATURE_REQUEST, PERFORMANCE, or DOCS."
                )
            },
            {
                "role": "user",
                "content": cleaned_text
            }
        ],
    )
    return response.choices[0].message.content.strip()

def detect_crash(cleaned_text: str) -> bool:
    """
    Determine whether the described issue causes a program crash.
    Returns True if the issue indicates a crash, otherwise False.
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a crash detector. "
                    "Only respond with 'yes' if the issue describes a crash or unhandled exception, "
                    "otherwise respond with 'no'."
                )
            },
            {
                "role": "user",
                "content": cleaned_text
            }
        ],
    )
    answer = response.choices[0].message.content.strip().lower()
    return answer.startswith("y")
