import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

INPUT_DIR = Path("documentos-parseados")
OUTPUT_DIR = Path("chunks")
OUTPUT_FILE = OUTPUT_DIR / "chunks.jsonl"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    total = 0
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for txt_path in sorted(INPUT_DIR.glob("*.txt")):
            text = txt_path.read_text(encoding="utf-8")
            docs = splitter.create_documents(
                [text],
                metadatas=[{"source": txt_path.name}],
            )
            for i, doc in enumerate(docs):
                row = {
                    "id": f"{txt_path.stem}_{i:04d}",
                    "text": doc.page_content,
                    "metadata": {**doc.metadata, "chunk_index": i},
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                total += 1

    print(f"Chunks generados: {total}")
    print(f"Archivo: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
