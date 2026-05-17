import os
import uuid
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

#Config

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
CHROMA_PATH   = os.getenv("CHROMA_PATH", "./chroma_db")

#Singletons 

_embedder   = SentenceTransformer("all-MiniLM-L6-v2")
_client     = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection("ubuntudocs")

#Helpers

def _extract_text(file_path: str) -> str:
    """Pull all text out of a PDF as one big string."""
    doc  = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def _chunk_text(text: str) -> list[str]:
    """
    Split text into fixed-size chunks with overlap.
    No external library needed — just string slicing.
    """
    words  = text.split()
    chunks = []
    start  = 0

    while start < len(words):
        end   = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP  # step back by overlap amount

    return chunks

#Public API 

def ingest_pdf(file_path: str, filename: str) -> dict:
    """Extract -> chunk -> embed -> store. Returns a summary dict."""
    document_id = str(uuid.uuid4())

    text   = _extract_text(file_path)
    chunks = _chunk_text(text)

    embeddings = _embedder.encode(chunks, show_progress_bar=False).tolist()

    _collection.upsert(
        ids        = [f"{document_id}_{i}" for i in range(len(chunks))],
        documents  = chunks,
        embeddings = embeddings,
        metadatas  = [{"document_id": document_id, "filename": filename} for _ in chunks],
    )

    return {
        "document_id": document_id,
        "filename":    filename,
        "chunks":      len(chunks),
    }


def delete_document(document_id: str) -> int:
    """Delete all chunks for a document. Returns how many were removed."""
    results = _collection.get(where={"document_id": {"$eq": document_id}})
    ids     = results["ids"]
    if ids:
        _collection.delete(ids=ids)
    return len(ids)


def list_documents() -> list[dict]:
    """Return one entry per document (deduplicated from chunk metadata)."""
    results = _collection.get(include=["metadatas"])
    seen    = {}
    for meta in results["metadatas"]:
        doc_id = meta["document_id"]
        if doc_id not in seen:
            seen[doc_id] = {"document_id": doc_id, "filename": meta["filename"], "chunks": 0}
        seen[doc_id]["chunks"] += 1
    return list(seen.values())