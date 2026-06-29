from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTOS_DIR = BASE_DIR / "documentos"
PARSED_DIR = BASE_DIR / "documentos-parseados"
CHUNKS_DIR = BASE_DIR / "chunks"
EMBEDDINGS_DIR = BASE_DIR / "embeddings"

CHUNKS_FILE = Path(os.getenv("CHUNKS_PATH", str(CHUNKS_DIR / "chunks.jsonl")))
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.npy"
METADATA_FILE = EMBEDDINGS_DIR / "chunks_metadata.json"

PAGES_SUFFIX = ".pages.jsonl"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
CHUNK_LANGUAGE = os.getenv("CHUNK_LANGUAGE", "es")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documentos_rag")

EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
UPSERT_BATCH_SIZE = int(os.getenv("UPSERT_BATCH_SIZE", "64"))
