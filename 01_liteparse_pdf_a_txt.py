from pathlib import Path
from liteparse import LiteParse

# Respeto el nombre que pediste: documentos-pareados.
# Si prefieres "documentos-parseados", cambia esta constante.
INPUT_DIR = Path("documentos")
OUTPUT_DIR = Path("documentos-parseados")


def main() -> None:
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Para PDFs normales con capa de texto, ocr_enabled=False es mas rapido.
    # Si vas a meter PDFs escaneados/fotos, cambia a True.
    parser = LiteParse(
        output_format="text",
        ocr_enabled=False,
        quiet=True,
    )

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No hay PDFs en {INPUT_DIR.resolve()}")
        return

    for pdf_path in pdfs:
        print(f"Parseando: {pdf_path.name}")
        try:
            result = parser.parse(str(pdf_path))
            text = getattr(result, "text", str(result))
            out_path = OUTPUT_DIR / f"{pdf_path.stem}.txt"
            out_path.write_text(text, encoding="utf-8")
            print(f"OK -> {out_path}")
        except Exception as exc:
            print(f"ERROR con {pdf_path.name}: {exc}")


if __name__ == "__main__":
    main()
