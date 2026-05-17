# ChromaDB queries
import os
from ingestion import _collection, _embedder

TOP_K = int(os.getenv("TOP_K", 5))


def retrieve(query: str) -> list[dict]:
    query_embedding = _embedder.encode(query).tolist()

    # never ask for more results than chunks that exist
    count = _collection.count()
    if count == 0:
        return []
    
    k = min(TOP_K, count)

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas"],
    )

    chunks = []
    for text, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "text":     text,
            "filename": meta["filename"],
        })

    return chunks
    