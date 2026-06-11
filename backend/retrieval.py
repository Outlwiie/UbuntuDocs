# ChromaDB queries
import os
import logging 
from ingestion import _collection, _embedder

logger = logging.getLogger(__name__)

TOP_K = int(os.getenv("TOP_K", 5))


def retrieve(query: str) -> list[dict]:
    """
    Embed the query and find the most similar chunks in ChromaDB.
 
    Returns a list of dicts:
        [{ "text": str, "filename": str }, ...]
    """
    count = _collection.count()
    if count == 0:
        logger.warning("Retrieval attempted but ChromaDB collection is empty.")
        return []
    
    k = min(TOP_K, count)
    logger.info(f"Retrieving top {k} chunks for query: '{query[:60]}...'")

    query_embedding = _embedder.encode(query).tolist()

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

    logger.info(f"Retrieved {len(chunks)} chunks.")
    return chunks
    