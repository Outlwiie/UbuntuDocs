# FastAPI app
import os
import logging
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

# ── Logging setup ──────────────────────────────────────────────────────────────
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
 
MAX_FILE_SIZE_MB = 20
MAX_QUESTION_LEN = 500

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
app.mount("/static", StaticFiles(directory="frontend"), name="static")

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
    return FileResponse("frontend/index.html")


@app.get("/health")
def health():
    """Quick check that the server is up."""
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
 
    # Validate file size
    contents = await file.read()
    size_mb  = len(contents) / (1024 * 1024)
 
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
        )
 
    logger.info(f"Upload received: '{file.filename}' ({size_mb:.1f}MB)")
 
    # Write to temp file for ingestion
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
 
    try:
        result = ingest_pdf(tmp_path, file.filename)
    except ValueError as e:
        # Duplicate file or no extractable text
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed for '{file.filename}': {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed. Check server logs.")
    finally:
        os.remove(tmp_path)
 
    return result

@app.post("/query", response_model=QueryResponse)
def query(body: QueryRequest):
    question = body.question.strip()
 
    # Validate question
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
 
    if len(question) > MAX_QUESTION_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Question too long. Maximum is {MAX_QUESTION_LEN} characters."
        )
 
    logger.info(f"Query received: '{question[:60]}'")
 
    try:
        chunks = retrieve(question)
        answer = ask(question, chunks)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed. Check server logs.")
 
    sources = list({c["filename"] for c in chunks})
    return QueryResponse(answer=answer, sources=sources)
 
 
@app.get("/documents")
def documents():
    return list_documents()

@app.delete("/documents/{document_id}")
def delete(document_id: str):
    """Delete a document and all its vectors."""
    deleted = delete_document(document_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted_chunks": deleted}