# intake/cleaner.py
import re

def clean_text(text: str) -> str:
    # remove fenced code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # collapse multiple blank lines
    text = re.sub(r"\n\s*\n", "\n", text).strip()
    return text
