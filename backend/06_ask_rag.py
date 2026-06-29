import argparse
import sys
from typing import Any

from google import genai
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models

from config import (
    EMBEDDING_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    RAG_TOP_K,
    RAG_MAX_CONTEXT_CHARS,
)


def validate_config() -> None:
    missing = []

    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not QDRANT_API_KEY:
        missing.append("QDRANT_API_KEY")
    if not QDRANT_COLLECTION:
        missing.append("QDRANT_COLLECTION")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if missing:
        raise RuntimeError("Faltan variables en .env: " + ", ".join(missing))


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


def build_document_filter(document_ids: list[str] | None):
    if not document_ids:
        return None

    should_conditions = []

    for document_id in document_ids:
        should_conditions.append(
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=document_id),
            )
        )

    return models.Filter(
        should=should_conditions,
    )


def search_qdrant(
    question: str,
    top_k: int,
    document_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(question)

    client = get_qdrant_client()

    query_filter = build_document_filter(document_ids)

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    )

    chunks = []

    for point in results.points:
        payload = point.payload or {}

        chunks.append(
            {
                "score": point.score,
                "text": payload.get("text", ""),
                "source": payload.get("source") or payload.get("filename", "desconocido"),
                "filename": payload.get("filename", "desconocido"),
                "document_id": payload.get("document_id", "desconocido"),
                "page": payload.get("page", "desconocida"),
                "page_label": payload.get("page_label", payload.get("page", "desconocida")),
                "chunk_index": payload.get("chunk_index", "desconocido"),
            }
        )

    return chunks


def format_context(chunks: list[dict[str, Any]], max_chars: int) -> str:
    context_parts = []
    current_length = 0

    for index, chunk in enumerate(chunks, start=1):
        text = chunk["text"].strip()

        if not text:
            continue

        block = f"""
[Fuente {index}]
Archivo: {chunk["filename"]}
Documento ID: {chunk["document_id"]}
Página: {chunk["page_label"]}
Chunk: {chunk["chunk_index"]}
Score: {chunk["score"]:.4f}

{text}
""".strip()

        if current_length + len(block) > max_chars:
            break

        context_parts.append(block)
        current_length += len(block)

    return "\n\n---\n\n".join(context_parts)


def build_prompt(question: str, context: str) -> str:
    return f"""
Eres un asistente RAG para responder preguntas usando documentación interna.

Instrucciones:
- Responde en español.
- Usa únicamente el CONTEXTO proporcionado.
- No inventes información.
- Si la respuesta no aparece en el contexto, di: "No tengo suficiente información en los documentos proporcionados."
- Sé claro y directo.
- Al final, incluye una sección "Fuentes" con archivo y página.
- Si varias fuentes dicen lo mismo, agrúpalas.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:
""".strip()


def ask_gemini(prompt: str) -> str:
    import time
    import random

    client = genai.Client(api_key=GEMINI_API_KEY)

    models_to_try = [
        GEMINI_MODEL,
    ]

    max_retries_per_model = 3
    last_error = None

    for model_name in models_to_try:
        for attempt in range(max_retries_per_model):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                return response.text or ""

            except Exception as error:
                last_error = error
                error_text = str(error)

                is_retryable_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                )

                if is_retryable_error and attempt < max_retries_per_model - 1:
                    wait_seconds = (2 ** attempt) + random.uniform(0, 1)
                    print(
                        f"Gemini no disponible temporalmente. "
                        f"Reintentando en {wait_seconds:.1f}s..."
                    )
                    time.sleep(wait_seconds)
                    continue

                break

    raise RuntimeError(
        "Gemini no está disponible ahora mismo o ha alcanzado un límite temporal. "
        f"Último error: {last_error}"
    )


def print_sources(chunks: list[dict[str, Any]]) -> None:
    print("\n\nChunks recuperados desde Qdrant:")
    print("-" * 80)

    for i, chunk in enumerate(chunks, start=1):
        print(
            f"{i}. {chunk['filename']} | "
            f"document_id {chunk['document_id']} | "
            f"página {chunk['page_label']} | "
            f"score {chunk['score']:.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pregunta al RAG usando Qdrant + Gemini."
    )

    parser.add_argument(
        "question",
        type=str,
        nargs="?",
        help="Pregunta que quieres hacer al RAG.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=RAG_TOP_K,
        help="Número de chunks a recuperar desde Qdrant.",
    )

    parser.add_argument(
        "--document-id",
        action="append",
        default=[],
        help="Document ID a usar como fuente. Puedes repetirlo varias veces.",
    )

    parser.add_argument(
        "--show-sources",
        action="store_true",
        help="Muestra los chunks recuperados desde Qdrant.",
    )

    args = parser.parse_args()

    question = args.question

    if not question:
        question = input("Pregunta: ").strip()

    if not question:
        print("No has escrito ninguna pregunta.")
        sys.exit(1)

    validate_config()

    print("Buscando chunks relevantes en Qdrant...")

    chunks = search_qdrant(
        question=question,
        top_k=args.top_k,
        document_ids=args.document_id,
    )

    if not chunks:
        print("No se han encontrado chunks relevantes en Qdrant.")
        sys.exit(0)

    context = format_context(chunks, max_chars=RAG_MAX_CONTEXT_CHARS)
    prompt = build_prompt(question, context)

    print("Generando respuesta con Gemini...\n")
    answer = ask_gemini(prompt)

    print(answer)

    if args.show_sources:
        print_sources(chunks)


if __name__ == "__main__":
    main()