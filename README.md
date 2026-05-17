# README.md
UbuntuDocs

"I am because of what I've read."

A Retrieval-Augmented Generation (RAG) system that lets you upload PDF documents and query them using natural language. Ask a question, UbuntuDocs finds the most relevant passages across your documents and uses an LLM to generate a grounded answer — with source citations.

Tech Stack
ComponentChoicePDF parsingPyMuPDF (fitz)ChunkingLangChain RecursiveCharacterTextSplitterEmbedding modelall-MiniLM-L6-v2 (sentence-transformers, runs locally)Vector databaseChromaDB (persistent, no external setup)LLMClaude API or Ollama (llama3 / mistral)BackendFastAPI + UvicornFrontendHTML / CSS / Vanilla JSTestingpytest + unittest.mockContainerisationDocker + docker-compose

Project Structure
ubuntudocs/
├── backend/
│   ├── main.py             # FastAPI app — routes and app config
│   ├── ingestion.py        # PDF parsing, chunking, embedding
│   ├── retrieval.py        # ChromaDB queries and similarity search
│   ├── llm.py              # Prompt building and LLM API calls
│   └── requirements.txt
├── frontend/
│   ├── index.html          # Upload form + chat interface
│   ├── style.css
│   └── app.js              # Fetch calls to FastAPI
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py   # Chunk size, overlap, metadata correctness
│   ├── test_retrieval.py   # Top-k retrieval, empty collection handling
│   └── test_llm.py         # Prompt construction, response parsing
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

Getting Started
Prerequisites

Python 3.11+
Docker and docker-compose
An Anthropic API key — or Ollama installed locally for a free option

1. Clone and configure
bashgit clone https://github.com/yourname/ubuntudocs.git
cd ubuntudocs
cp .env.example .env
Open .env and fill in your values:
envANTHROPIC_API_KEY=your_key_here
LLM_PROVIDER=anthropic         # or ollama
OLLAMA_MODEL=llama3            # only needed if using ollama
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=5
CHROMA_PATH=./chroma_db
2. Run with Docker
bashdocker-compose up --build
App runs at http://localhost:8000
3. Run locally (without Docker)
bashcd backend
pip install -r requirements.txt
uvicorn main:app --reload

How It Works
Ingestion pipeline
When you upload a PDF, UbuntuDocs:

Extracts raw text page by page using PyMuPDF
Splits the text into overlapping chunks (500 tokens, 50 token overlap)
Embeds each chunk into a 384-dimensional vector using all-MiniLM-L6-v2
Stores the vectors and metadata (filename, page number) in ChromaDB

Query pipeline
When you ask a question:

The question is embedded using the same model
ChromaDB returns the top 5 most semantically similar chunks
Those chunks are inserted into a prompt as context
The LLM generates an answer grounded in that context
The answer is returned with source citations (filename + page number)


API Endpoints
MethodEndpointDescriptionPOST/uploadUpload a PDF. Returns document ID and chunk count.POST/queryAsk a question. Returns answer and source citations.GET/documentsList all ingested documents.DELETE/documents/{id}Remove a document and its vectors.GET/healthHealth check.

Running Tests
bashpytest tests/ -v
FileWhat it coverstest_ingestion.pyChunks respect size limit, overlap is applied, metadata is attached to every chunktest_retrieval.pyTop-k returns correct count, empty collection handled gracefully (ChromaDB mocked)test_llm.pyContext appears in prompt, question appears in prompt, API errors handled (LLM client mocked)

Configuration
All config lives in .env. Never commit this file — only commit .env.example.
VariableDefaultDescriptionANTHROPIC_API_KEY—Your Anthropic API keyLLM_PROVIDERanthropicanthropic or ollamaOLLAMA_MODELllama3Model name if using OllamaCHUNK_SIZE500Max tokens per chunkCHUNK_OVERLAP50Token overlap between chunksTOP_K5Chunks retrieved per queryCHROMA_PATH./chroma_dbChromaDB persistence path
