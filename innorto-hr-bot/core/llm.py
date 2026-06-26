import os
import logging
from groq import Groq

log = logging.getLogger(__name__)

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def ask(system_prompt: str, user_message: str) -> str:
    try:
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error("Groq error: %s", e)
        raise
