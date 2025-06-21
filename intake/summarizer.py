# intake/summarizer.py

import os
import openai

# Load the OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_issue(cleaned_text: str) -> dict:
    """
    Use an LLM to generate a concise one-sentence summary of the issue.
    Returns a dict with the 'summary' key.
    """
    prompt = (
        "Please provide a single clear sentence summarizing the core problem and how to fix it, or how to enhance it "
        "described below:\n\n"
        f"{cleaned_text}"
    )
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a software engineering assistant. "
                    "Summarize the core issue in one clear sentence."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )
    summary_text = response.choices[0].message.content.strip()
    return {"summary": summary_text}
