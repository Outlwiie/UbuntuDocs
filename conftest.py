import sys
import os

# Add backend folder to path so tests can import retrieval, ingestion, llm directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))