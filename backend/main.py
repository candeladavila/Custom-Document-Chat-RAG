import importlib.util
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


RAG_SCRIPT_PATH = Path(__file__).with_name("06_ask_rag.py")


def load_rag_module():
    """
    Carga 06_ask_rag.py aunque el nombre empiece por número.
    Así reutilizamos las funciones que ya funcionan:
    - validate_config
    - search_qdrant
    - format_context
    - build_prompt
    - ask_gemini
    """
    spec = importlib.util.spec_from_file_location("ask_rag_module", RAG_SCRIPT_PATH)

    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar 06_ask_rag.py")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


rag = load_rag_module()

app = FastAPI(
    title="Proyecto Prueba RAG API",
    description="API local para preguntar al RAG usando Qdrant + Gemini",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class Source(BaseModel):
    filename: str
    page: str
    chunk_index: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "Backend RAG funcionando",
        "endpoint": "POST /ask",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    try:
        rag.validate_config()

        chunks: list[dict[str, Any]] = rag.search_qdrant(
            question=question,
            top_k=request.top_k,
        )

        if not chunks:
            return AskResponse(
                answer="No he encontrado información relevante en los documentos.",
                sources=[],
            )

        context = rag.format_context(
            chunks=chunks,
            max_chars=rag.RAG_MAX_CONTEXT_CHARS,
        )

        prompt = rag.build_prompt(
            question=question,
            context=context,
        )

        answer = rag.ask_gemini(prompt)

        sources = []

        for chunk in chunks:
            sources.append(
                Source(
                    filename=str(chunk.get("filename", "desconocido")),
                    page=str(chunk.get("page_label", chunk.get("page", "desconocida"))),
                    chunk_index=str(chunk.get("chunk_index", "desconocido")),
                    score=float(chunk.get("score", 0.0)),
                )
            )

        return AskResponse(
            answer=answer or "Gemini no devolvió respuesta.",
            sources=sources,
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la pregunta: {str(error)}",
        )