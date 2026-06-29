import argparse
import sys
from typing import Any

import time
import random

from google import genai
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

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


def search_qdrant(question: str, top_k: int) -> list[dict[str, Any]]:
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(question)

    client = get_qdrant_client()

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
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
    client = genai.Client(api_key=GEMINI_API_KEY)

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )

            return response.text or ""

        except Exception as error:
            error_text = str(error)

            is_retryable_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if is_retryable_error and attempt < max_retries - 1:
                wait_seconds = (2 ** attempt) + random.uniform(0, 1)
                print(
                    f"Gemini saturado o con límite temporal. "
                    f"Reintentando en {wait_seconds:.1f}s..."
                )
                time.sleep(wait_seconds)
                continue

            if "503" in error_text or "UNAVAILABLE" in error_text:
                raise RuntimeError(
                    "Gemini está saturado temporalmente. "
                    "Espera unos segundos y vuelve a intentarlo. "
                    "También puedes usar GEMINI_MODEL=gemini-2.5-flash-lite."
                )

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                raise RuntimeError(
                    "Has alcanzado un límite temporal de Gemini API. "
                    "Espera un poco y vuelve a intentarlo."
                )

            raise


def print_sources(chunks: list[dict[str, Any]]) -> None:
    print("\n\nChunks recuperados desde Qdrant:")
    print("-" * 80)

    for i, chunk in enumerate(chunks, start=1):
        print(
            f"{i}. {chunk['filename']} | "
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
    chunks = search_qdrant(question, top_k=args.top_k)

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