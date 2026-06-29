# Demo RAG gratis con LiteParse + LangChain + embeddings locales

Estructura:

```
rag_liteparse_demo/
  documentos/                 # PDFs de entrada
  documentos-pareados/         # TXT generados por LiteParse
  chunks/                      # JSONL con chunks de LangChain
  embeddings/                  # embeddings numpy + metadatos
  01_liteparse_pdf_a_txt.py
  02_langchain_chunking.py
  03_embeddings_locales.py
  04_busqueda_semantica.py
  requirements.txt
```

## Instalacion

Activa tu entorno virtual y ejecuta:

```bash
python -m pip install -r requirements.txt
```

## Flujo

```bash
python 01_liteparse_pdf_a_txt.py
python 02_langchain_chunking.py
python 03_embeddings_locales.py
python 04_busqueda_semantica.py "quien fue Bertha Benz"
```

Nota: la primera ejecucion de `sentence-transformers/all-MiniLM-L6-v2` descarga el modelo. Despues funciona localmente.
