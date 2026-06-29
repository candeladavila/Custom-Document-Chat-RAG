"""
Sube chunks a Qdrant con dos mejoras importantes:
1) Antes de reindexar, borra únicamente los chunks de los documentos incluidos en chunks.jsonl.
2) Si la colección ya existe, valida que su dimensión vectorial coincida con el modelo actual.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from backend.config import (
    CHUNKS_FILE,
    EMBED_BATCH_SIZE,
    EMBEDDING_MODEL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
    UPSERT_BATCH_SIZE,
)


def read_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de chunks: {path}")

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"El archivo de chunks está vacío: {path}")

    if path.suffix.lower() == ".jsonl":
        chunks: list[dict[str, Any]] = []
        for line_number, line in enumerate(raw.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en línea {line_number} de {path}: {exc}") from exc
        return chunks

    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("chunks"), list):
        return data["chunks"]

    raise ValueError("Formato no reconocido. Usa JSONL, lista JSON, u objeto JSON con clave 'chunks'.")


def get_chunk_text(chunk: dict[str, Any]) -> str:
    text = chunk.get("text") or chunk.get("page_content") or chunk.get("content") or chunk.get("chunk") or ""
    return str(text).strip()


def deterministic_qdrant_id(chunk: dict[str, Any], text: str, index: int) -> str:
    base = str(chunk.get("id") or chunk.get("chunk_id") or "")
    if not base:
        base = hashlib.sha1(f"{index}:{text[:500]}".encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, base))


def batched(items: list[Any], batch_size: int) -> Iterable[list[Any]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def get_existing_vector_size(client: QdrantClient, collection_name: str) -> int | None:
    info = client.get_collection(collection_name=collection_name)
    vectors = info.config.params.vectors

    # Colección con vector único.
    if hasattr(vectors, "size"):
        return int(vectors.size)

    # Colección con named vectors, por si alguna vez se usa.
    if isinstance(vectors, dict) and vectors:
        first_vector = next(iter(vectors.values()))
        if hasattr(first_vector, "size"):
            return int(first_vector.size)

    return None


def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if client.collection_exists(collection_name=collection_name):
        existing_size = get_existing_vector_size(client, collection_name)

        if existing_size is not None and existing_size != vector_size:
            raise RuntimeError(
                f"La colección '{collection_name}' ya existe con dimensión {existing_size}, "
                f"pero el modelo actual genera dimensión {vector_size}. "
                "Solución: usa otra QDRANT_COLLECTION o limpia/recrea la colección."
            )

        print(f"Colección existente válida: {collection_name} | dimensión={existing_size}")
        return

    print(f"Creando colección: {collection_name} | dimensión vectorial: {vector_size}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def recreate_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if client.collection_exists(collection_name=collection_name):
        print(f"Eliminando colección completa: {collection_name}")
        client.delete_collection(collection_name=collection_name)

    print(f"Creando colección limpia: {collection_name} | dimensión vectorial: {vector_size}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def build_payload(chunk: dict[str, Any], text: str, index: int, model_name: str) -> dict[str, Any]:
    metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}

    payload: dict[str, Any] = {
        "text": text,
        "chunk_id": chunk.get("id") or chunk.get("chunk_id") or f"chunk_{index}",
        "embedding_model": model_name,
        "metadata": metadata,
    }

    # Campos principales duplicados en top-level para poder filtrar fácil en Qdrant.
    for key in [
        "source",
        "filename",
        "document_id",
        "source_type",
        "page",
        "page_label",
        "language",
        "chunk_index",
        "chunk_index_in_page",
    ]:
        value = metadata.get(key, chunk.get(key))
        if value is not None:
            payload[key] = value

    if "chunk_index" not in payload:
        payload["chunk_index"] = index

    return payload


def values_from_chunks(chunks: list[dict[str, Any]], metadata_key: str) -> set[str]:
    values: set[str] = set()
    for chunk in chunks:
        metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
        value = metadata.get(metadata_key) or chunk.get(metadata_key)
        if value is not None:
            values.add(str(value))
    return values


def delete_existing_by_field(
    client: QdrantClient,
    collection_name: str,
    field_name: str,
    values: set[str],
) -> None:
    if not values:
        return

    for value in sorted(values):
        print(f"Borrando chunks antiguos: {field_name}={value}")
        client.delete(
            collection_name=collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=field_name,
                            match=models.MatchValue(value=value),
                        )
                    ]
                )
            ),
            wait=True,
        )


def delete_existing_sources(client: QdrantClient, collection_name: str, chunks: list[dict[str, Any]]) -> None:
    """
    Opción 2 del punto 7: borra solo los chunks de los documentos que estás reindexando.
    Priorizamos document_id. Si no existe, usamos source.
    """
    document_ids = values_from_chunks(chunks, "document_id")
    if document_ids:
        delete_existing_by_field(client, collection_name, "document_id", document_ids)
        return

    sources = values_from_chunks(chunks, "source")
    delete_existing_by_field(client, collection_name, "source", sources)


def upload_chunks_to_qdrant(
    chunks_path: Path,
    collection_name: str,
    model_name: str,
    delete_old_sources: bool,
    recreate: bool,
) -> None:
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("Faltan QDRANT_URL y/o QDRANT_API_KEY en tu .env")

    print(f"Leyendo chunks desde: {chunks_path}")
    raw_chunks = read_chunks(chunks_path)

    clean_chunks: list[dict[str, Any]] = []
    texts: list[str] = []
    for idx, chunk in enumerate(raw_chunks):
        text = get_chunk_text(chunk)
        if not text:
            print(f"Aviso: chunk vacío ignorado en índice {idx}")
            continue
        clean_chunks.append(chunk)
        texts.append(text)

    if not clean_chunks:
        raise ValueError("No hay chunks con texto para subir a Qdrant.")

    print(f"Chunks con texto: {len(clean_chunks)}")
    print(f"Cargando modelo de embeddings: {model_name}")
    model = SentenceTransformer(model_name)

    print("Generando embeddings...")
    embeddings = model.encode(
        texts,
        batch_size=EMBED_BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    vector_size = int(embeddings.shape[1])
    print(f"Dimensión de embeddings: {vector_size}")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)
    print("Conectado a Qdrant Cloud.")

    if recreate:
        recreate_collection(client, collection_name, vector_size)
    else:
        ensure_collection(client, collection_name, vector_size)

    if delete_old_sources and not recreate:
        delete_existing_sources(client, collection_name, clean_chunks)

    total_uploaded = 0
    indexed_items = list(enumerate(zip(clean_chunks, texts, embeddings)))

    for batch in batched(indexed_items, UPSERT_BATCH_SIZE):
        points: list[models.PointStruct] = []

        for original_index, (chunk, text, vector) in batch:
            point_id = deterministic_qdrant_id(chunk, text, original_index)
            payload = build_payload(chunk, text, original_index, model_name)

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload=payload,
                )
            )

        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        total_uploaded += len(points)
        print(f"Subidos {total_uploaded}/{len(clean_chunks)} points")

    count = client.count(collection_name=collection_name, exact=True).count
    print("\nSubida completada.")
    print(f"Colección: {collection_name}")
    print(f"Points en la colección: {count}")


def test_query(collection_name: str, model_name: str, query: str, top_k: int) -> None:
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("Faltan QDRANT_URL y/o QDRANT_API_KEY en tu .env")

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)
    model = SentenceTransformer(model_name)

    query_vector = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0].tolist()

    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    print(f"\nResultados para: {query!r}")
    for i, point in enumerate(response.points, start=1):
        payload = point.payload or {}
        text = str(payload.get("text", ""))
        source = payload.get("source", "unknown")
        page = payload.get("page", "?")
        chunk_index = payload.get("chunk_index", "?")
        preview = text.replace("\n", " ")[:500]

        print("\n" + "=" * 80)
        print(f"#{i} | score={point.score:.4f} | source={source} | page={page} | chunk_index={chunk_index}")
        print(preview)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sube chunks JSONL a Qdrant Cloud con embeddings locales.")
    parser.add_argument("--chunks-path", default=str(CHUNKS_FILE), help="Ruta al archivo chunks.jsonl")
    parser.add_argument("--collection", default=QDRANT_COLLECTION, help="Nombre de colección en Qdrant")
    parser.add_argument("--model", default=EMBEDDING_MODEL, help="Modelo sentence-transformers")
    parser.add_argument("--query", default=None, help="Pregunta de prueba después de subir los points")
    parser.add_argument("--top-k", type=int, default=5, help="Número de resultados para la pregunta de prueba")
    parser.add_argument(
        "--no-delete-existing-sources",
        action="store_true",
        help="No borrar chunks antiguos del mismo document_id/source antes de subir.",
    )
    parser.add_argument(
        "--recreate-collection",
        action="store_true",
        help="Elimina la colección completa, la recrea y después sube los chunks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        upload_chunks_to_qdrant(
            chunks_path=Path(args.chunks_path),
            collection_name=args.collection,
            model_name=args.model,
            delete_old_sources=not args.no_delete_existing_sources,
            recreate=args.recreate_collection,
        )

        if args.query:
            test_query(
                collection_name=args.collection,
                model_name=args.model,
                query=args.query,
                top_k=args.top_k,
            )

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
