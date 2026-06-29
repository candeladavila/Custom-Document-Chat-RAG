import json
import sys
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDINGS_FILE = Path("embeddings/embeddings.npy")
METADATA_FILE = Path("embeddings/chunks_metadata.json")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def buscar(query: str, top_k: int = 4) -> None:
    embeddings = np.load(EMBEDDINGS_FILE)
    rows = json.loads(METADATA_FILE.read_text(encoding="utf-8"))

    model = SentenceTransformer(MODEL_NAME)
    q_emb = model.encode([query], normalize_embeddings=True)[0]

    # Como normalizamos embeddings, producto escalar equivale a similitud coseno.
    scores = embeddings @ q_emb
    best_idx = np.argsort(scores)[::-1][:top_k]

    for rank, idx in enumerate(best_idx, start=1):
        row = rows[int(idx)]
        print("=" * 80)
        print(f"#{rank} score={scores[idx]:.4f} id={row['id']} source={row['metadata'].get('source')}")
        print(row["text"][:1200])
        print()


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "que paso en 1926 con Mercedes"
    buscar(query)
