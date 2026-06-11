import requests
import logging 

logger = logging.getLogger(__name__)

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"


def ask(question: str, chunks: list[dict]) -> str:
    """
    Build a prompt from retrieved chunks and send to Ollama.
 
    Returns the LLM's answer as a string.
    Raises ConnectionError if Ollama is not running.
    Raises RuntimeError if the response is malformed.
    """
    if not chunks:
        logger.warning("No chunks provided to LLM — returning fallback message.")
        return "I couldn't find any relevant information in your documents. Try uploading a PDF first."

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

    logger.info(f"Sending prompt to Ollama (model: {OLLAMA_MODEL})...")
 
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,  # 2 minute timeout
        )
        response.raise_for_status()
 
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Ollama.")
        raise ConnectionError(
            "Ollama is not running. Start it by running 'ollama serve' in a terminal."
        )
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out.")
        raise TimeoutError("The request to Ollama timed out. Try a shorter question or a smaller model.")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Ollama returned an HTTP error: {e}")
        raise RuntimeError(f"Ollama error: {e}")
 
    data = response.json()
 
    if "response" not in data:
        logger.error(f"Unexpected Ollama response format: {data}")
        raise RuntimeError("Unexpected response format from Ollama.")
 
    logger.info("Received response from Ollama.")
    return data["response"]