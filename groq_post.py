"""
Groq AI-powered viral post content generator.

User sends news text → Groq generates:
  1. caption     : short styled text with [yellow]/[brown] markup (rendered on image)
  2. description : a ready-to-post social media paragraph (sent as text alongside the image)
"""

import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"


def _strip_emojis(text: str) -> str:
    """Remove all emoji / symbol characters from a string."""
    import unicodedata
    return "".join(
        ch for ch in text
        if not (unicodedata.category(ch) in ("So", "Sm") or ord(ch) > 0x2500)
    ).strip()


def generate_viral_content(news_text: str) -> dict:
    """
    Call Groq once and get back both the image caption and the post description.

    Returns:
        {
            "caption":     str  - short viral text with [yellow]/[brown] markup (for image)
            "description": str  - ready-to-post social media paragraph (sent as text)
        }
    """
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set!\n"
            "Add it to your .env file.\n"
            "Get a free key at: https://console.groq.com"
        )

    system_prompt = (
        "You are a viral social media content creator. Given a news/fact, produce TWO things:\n\n"
        "1. IMAGE CAPTION - A very short (1-2 line) punchy caption for the post image.\n"
        "   CRITICAL RULES for the caption:\n"
        "   - Extract the SINGLE most important/shocking key point from the user's text. Do NOT invent a new angle.\n"
        "   - Keep the same core meaning and facts as the user provided. Just condense and punch it up.\n"
        "   - Use markup: [brown]word[/brown] for names/places/things/titles, [yellow]word[/yellow] for shocking facts/numbers/dates.\n"
        "   - NO emojis. NO punctuation at the very end.\n"
        "   - Good example: user sends 'On 9 March 2014 flight MH370 disappeared'\n"
        "     Caption: On [yellow]9 March 2014[/yellow], flight [brown]MH370[/brown] mysteriously disappeared\n"
        "   - Bad example: inventing 'Search for MH370 ends without finding 239 people' when user never said that\n\n"
        "2. POST DESCRIPTION - A ready-to-post social media caption (3-5 sentences).\n"
        "   - Expand on the news, add context, make it engaging and shareable.\n"
        "   - Write in a conversational, informative tone like a journalist explaining to a friend.\n"
        "   - NO emojis. No hashtags.\n"
        "   - This should be something someone can paste directly as their post caption.\n\n"
        "Return ONLY valid JSON (no markdown fences), exactly this structure:\n"
        '{"caption": "<image headline with markup>", "description": "<ready-to-post paragraph>"}'
    )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"News/fact:\n{news_text}"}
        ],
        "temperature": 0.75,
        "max_tokens":  500,
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }

    resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()

    raw = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip markdown code fences if the model wraps with ```json
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    data = json.loads(raw)

    caption     = _strip_emojis(data.get("caption",     "").strip().strip('"'))
    description = _strip_emojis(data.get("description", "").strip().strip('"'))

    return {"caption": caption, "description": description}
