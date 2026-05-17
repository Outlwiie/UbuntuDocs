# LLM call + prompt building
import os
import requests
from dotenv import load_dotenv

load_dotenv()

#_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def ask(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I couldn't find any relevant information in your documents."

    context = "\n\n".join(
        f"[Source: {c['filename']}]\n{c['text']}"
        for c in chunks
    )

    prompt = f"""Answer the question using only the context provided below.
If the answer is not in the context, say "I don't have enough information to answer that."
Always mention which file the answer came from.

Context:
{context}

Question: {question}"""

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
    })

    return response.json()["response"]