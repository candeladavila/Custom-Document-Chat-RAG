import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("chunks/chunks.jsonl")
OUTPUT_DIR = Path("embeddings")
EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npy"
METADATA_FILE = OUTPUT_DIR / "chunks_metadata.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = [json.loads(line) for line in CHUNKS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    texts = [row["text"] for row in rows]

    if not texts:
        raise RuntimeError("No hay chunks. Ejecuta antes 02_langchain_chunking.py")

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,  # facilita usar similitud por producto escalar/coseno
    )

    np.save(EMBEDDINGS_FILE, embeddings)
    METADATA_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Embeddings: {embeddings.shape}")
    print(f"Guardado en: {EMBEDDINGS_FILE}")
    print(f"Metadatos: {METADATA_FILE}")


if __name__ == "__main__":
    main()
