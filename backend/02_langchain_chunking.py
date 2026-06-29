from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHUNK_LANGUAGE,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKS_DIR,
    CHUNKS_FILE,
    PARSED_DIR,
    PAGES_SUFFIX,
)

HEADER_RE = re.compile(
    r"Mercedes-Benz\s*-\s*documento de prueba RAG\s*\|\s*P[aá]gina\s*\d+",
    flags=re.IGNORECASE,
)


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = HEADER_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido en {path}, línea {line_number}: {exc}") from exc
    return rows


def load_page_rows() -> list[dict[str, Any]]:
    """
    Prioriza los .pages.jsonl generados por 01_liteparse_pdf_a_txt.py.
    Si no existen, mantiene compatibilidad con los .txt antiguos.
    """
    page_files = sorted(PARSED_DIR.glob(f"*{PAGES_SUFFIX}"))
    if page_files:
        rows: list[dict[str, Any]] = []
        for pages_path in page_files:
            rows.extend(read_jsonl(pages_path))
        return rows

    txt_files = sorted(PARSED_DIR.glob("*.txt"))
    rows = []
    for txt_path in txt_files:
        rows.append(
            {
                "document_id": txt_path.stem,
                "filename": txt_path.name,
                "source": txt_path.name,
                "source_type": "txt",
                "page": None,
                "page_label": None,
                "text": txt_path.read_text(encoding="utf-8"),
            }
        )
    return rows


def safe_id_part(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9_-]+", "_", value)
    return value.strip("_") or "documento"


def main() -> None:
    CHUNKS_DIR.mkdir(exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    page_rows = load_page_rows()
    if not page_rows:
        print(f"No hay documentos parseados en {PARSED_DIR.resolve()}")
        return

    total = 0
    per_document_counter: dict[str, int] = {}

    with CHUNKS_FILE.open("w", encoding="utf-8") as f:
        for page_row in page_rows:
            text = clean_text(str(page_row.get("text", "")))
            if not text:
                continue

            document_id = str(page_row.get("document_id") or Path(str(page_row.get("filename", "documento"))).stem)
            filename = str(page_row.get("filename") or page_row.get("source") or f"{document_id}.txt")
            source = str(page_row.get("source") or filename)
            source_type = str(page_row.get("source_type") or Path(filename).suffix.lstrip(".") or "unknown")
            page = page_row.get("page")
            page_label = page_row.get("page_label")

            page_chunks = splitter.split_text(text)

            for chunk_index_in_page, chunk_text in enumerate(page_chunks):
                global_chunk_index = per_document_counter.get(document_id, 0)
                per_document_counter[document_id] = global_chunk_index + 1

                page_part = f"p{int(page):03d}" if isinstance(page, int) else "p000"
                chunk_id = f"{safe_id_part(document_id)}_{page_part}_c{chunk_index_in_page:03d}"

                metadata = {
                    "source": source,
                    "filename": filename,
                    "document_id": document_id,
                    "source_type": source_type,
                    "page": page,
                    "page_label": page_label,
                    "language": CHUNK_LANGUAGE,
                    "chunk_index": global_chunk_index,
                    "chunk_index_in_page": chunk_index_in_page,
                    "chunk_size": len(chunk_text),
                }

                row = {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": metadata,
                }

                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                total += 1

    print(f"Chunks generados: {total}")
    print(f"Archivo: {CHUNKS_FILE}")


if __name__ == "__main__":
    main()
