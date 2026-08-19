# UbuntuDocs

> *"I am because of what I've read."*

UbuntuDocs lets you upload PDF documents and have a conversation with them. Ask a question in plain English, and it finds the most relevant parts of your documents and gives you a grounded answer — telling you exactly which file it came from.

No cloud storage. No third-party indexing. Everything runs on your machine.

---

## What it does

You upload a PDF. UbuntuDocs breaks it into chunks, converts each chunk into a vector (a mathematical representation of its meaning), and stores everything locally. When you ask a question, it finds the chunks that are most semantically similar to your question and passes them to an LLM to generate a real answer — not just a keyword match.

This pattern is called RAG (Retrieval-Augmented Generation). It's how most production document AI systems work.

---

## Built with

- **FastAPI** — the backend API
- **ChromaDB** — stores and searches the document vectors locally
- **sentence-transformers** (`all-MiniLM-L6-v2`) — turns text into vectors, runs fully offline
- **PyMuPDF** — extracts text from PDFs
- **Ollama** (llama3.2) — the local LLM that generates answers, no API key needed
- **HTML / CSS / Vanilla JS** — the frontend, no framework
- **Docker** — so anyone can run it with one command
- **pytest** — 20 tests covering ingestion, retrieval, and the LLM layer

---

## Getting started

### Option 1 — Docker (recommended)

Make sure Docker Desktop and Ollama are running, then:

```bash
git clone https://github.com/yourname/ubuntudocs.git
cd ubuntudocs
docker-compose up --build
```

Open `http://localhost:8000` and you're good to go.

### Option 2 — Run locally

```bash
git clone https://github.com/yourname/ubuntudocs.git
cd ubuntudocs

cp .env.example .env       # fill in your values

cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://localhost:8000`.

### Prerequisites

- Python 3.11+
- Docker Desktop (for Option 1)
- [Ollama](https://ollama.com) with `llama3.2` pulled — run `ollama pull llama3.2`

---

## Project structure

```
ubuntudocs/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── ingestion.py     # PDF parsing, chunking, embedding
│   ├── retrieval.py     # Vector similarity search
│   ├── llm.py           # Prompt building and LLM calls
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_llm.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## How it works

**When you upload a PDF:**

1. PyMuPDF extracts all the text
2. The text is split into 500-word chunks with a 50-word overlap between them
3. Each chunk is converted into a 384-dimensional vector using a local embedding model
4. The vectors and metadata are saved to ChromaDB on disk

**When you ask a question:**

1. Your question gets converted into a vector using the same model
2. ChromaDB finds the 5 most similar chunks
3. Those chunks get passed to llama3.2 as context
4. The LLM generates an answer grounded in that context
5. You get the answer plus a citation showing which file it came from

---

## Running the tests

```bash
pytest tests/ -v
```

20 tests across three files. ChromaDB and the LLM are mocked so tests run fast without any external dependencies.

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed. Never commit `.env` — it's in `.gitignore`.

| Variable | Default | What it does |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Where Ollama is running |
| `CHUNK_SIZE` | `500` | Max words per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K` | `5` | How many chunks to retrieve per question |
| `CHROMA_PATH` | `./chroma_db` | Where ChromaDB saves its data |

---

## API

| Method | Endpoint | What it does |
|---|---|---|
| `POST` | `/upload` | Upload a PDF |
| `POST` | `/query` | Ask a question |
| `GET` | `/documents` | List ingested documents |
| `DELETE` | `/documents/{id}` | Remove a document |
| `GET` | `/health` | Check the server is up |

---

## Licence

MIT
