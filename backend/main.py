# FastAPI app
import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ingestion import ingest_pdf, delete_document, list_documents
from retrieval import retrieve
from llm import ask

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="UbuntuDocs",
    description="Upload PDFs. Ask questions. Get answers grounded in your documents.",
    version="0.1.0",
)

# Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# ── Request / Response models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Serve the frontend."""
    return FileResponse("../frontend/index.html")


@app.get("/health")
def health():
    """Quick check that the server is up."""
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Accept a PDF upload, ingest it, and return a summary.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save the upload to a temp file so ingestion can read it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_pdf(tmp_path, file.filename)
    finally:
        os.remove(tmp_path)  # clean up temp file

    return result


@app.post("/query", response_model=QueryResponse)
def query(body: QueryRequest):
    """
    Retrieve relevant chunks and generate an answer.
    """
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    chunks  = retrieve(body.question)
    answer  = ask(body.question, chunks)
    sources = list({c["filename"] for c in chunks})  # deduplicated source list

    return QueryResponse(answer=answer, sources=sources)


@app.get("/documents")
def documents():
    """List all ingested documents."""
    return list_documents()


@app.delete("/documents/{document_id}")
def delete(document_id: str):
    """Delete a document and all its vectors."""
    deleted = delete_document(document_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted_chunks": deleted}