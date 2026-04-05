import httpx

from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def chat(prompt: str) -> str:
    if not settings.groq_api_key or settings.groq_api_key.strip().lower() == "changeme":
        raise ValueError("Groq API key is not configured. Set GROQ_API_KEY in .env.")

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": settings.groq_max_output_tokens,
    }

    response = httpx.post(GROQ_URL, json=payload, headers=headers, timeout=300.0)
    if not response.is_success:
        raise RuntimeError(f"Groq chat error: {response.status_code} - {response.text}")

    data = response.json()
    choices = data.get("choices", [])
    if choices and len(choices) > 0:
        return choices[0].get("message", {}).get("content", "")

    return ""
