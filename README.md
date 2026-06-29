# Custom Document Chat — RAG System with PDF Uploads

A local RAG project built with:

```text
React + Vite
FastAPI
LangChain
Local embeddings with sentence-transformers
Qdrant Cloud
Gemini API
```

The application allows users to:

```text
1. Upload PDF documents from the frontend
2. Save them in backend/documentos/
3. Extract text from the PDF
4. Extract text page by page
5. Create chunks with metadata
6. Upload the chunks to Qdrant
7. Ask questions through a web chat
8. Get answers generated with Gemini using the retrieved chunks
```

---

## Project Structure

```text
Proyecto-Prueba-RAG/
├── .venv/
├── backend/
│   ├── documentos/
│   ├── documentos-parseados/
│   ├── chunks/
│   ├── embeddings/
│   ├── 01_liteparse_pdf_a_txt.py
│   ├── 02_langchain_chunking.py
│   ├── 03_embeddings_locales.py
│   ├── 04_busqueda_semantica.py
│   ├── 05_subir_chunks_a_qdrant.py
│   ├── 06_ask_rag.py
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   ├── index.css
    │   └── main.jsx
    ├── .env.local
    ├── package.json
    └── vite.config.js
```

---

## Complete RAG Flow

```text
User uploads PDF
↓
React frontend calls POST /upload-stream
↓
Backend saves the PDF in backend/documentos/
↓
01_liteparse_pdf_a_txt.py extracts text and pages
↓
02_langchain_chunking.py creates chunks with metadata
↓
05_subir_chunks_a_qdrant.py creates embeddings and uploads chunks to Qdrant
↓
User asks a question in the chat
↓
Frontend calls POST /ask
↓
Backend creates an embedding of the question
↓
Qdrant returns relevant chunks
↓
Gemini generates the final answer using those chunks
↓
Frontend displays the answer and sources
```

---

## 1. Create a Virtual Environment

From the project root:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

---

## 2. Install Backend Dependencies

From the project root:

```bash
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
```

If any dependency is missing, install:

```bash
pip install fastapi "uvicorn[standard]" python-multipart python-dotenv qdrant-client langchain-text-splitters langchain-huggingface sentence-transformers google-genai pypdf numpy
```

The `backend/requirements.txt` file should include:

```txt
liteparse
langchain-text-splitters
langchain-huggingface
sentence-transformers
numpy
qdrant-client
python-dotenv
pypdf
google-genai
fastapi
uvicorn[standard]
python-multipart
```

---

## 3. Configure Backend Environment Variables

Create the file:

```text
backend/.env
```

Recommended content:

```env
QDRANT_URL=https://YOUR_CLUSTER.qdrant.io
QDRANT_API_KEY=YOUR_QDRANT_API_KEY
QDRANT_COLLECTION=documentos_rag

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash-lite

RAG_TOP_K=3
RAG_MAX_CONTEXT_CHARS=5000

EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Important:

```text
Do not upload .env to GitHub.
Do not put private keys in the frontend.
```

---

## 4. Configure the Frontend

From the project root:

```bash
cd frontend
npm install
```

Create the file:

```text
frontend/.env.local
```

Content:

```env
VITE_API_URL=http://127.0.0.1:8000
```

---

## 5. Start the Backend

From the project root:

```bash
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend available at:

```text
http://127.0.0.1:8000
```

Check backend health:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

---

## 6. Start the Frontend

In another terminal, from the project root:

```bash
cd frontend
npm run dev
```

The frontend is usually available at:

```text
http://localhost:5173
```

---

## 7. Backend Endpoints

### `GET /health`

Checks whether the backend is running.

```bash
curl http://127.0.0.1:8000/health
```

---

### `POST /upload-stream`

Uploads a PDF, saves it in `backend/documentos/`, processes it and uploads it to Qdrant.

This endpoint returns step-by-step progress in NDJSON format.

Internal flow:

```text
Save PDF
↓
Extract text
↓
Create chunks
↓
Upload chunks to Qdrant
↓
Finish
```

Test with `curl`:

```bash
curl -N -X POST "http://127.0.0.1:8000/upload-stream" \
  -F "file=@/path/to/your/document.pdf"
```

Example response:

```json
{"status":"progress","step":"save","message":"Saving PDF: document.pdf"}
{"status":"progress","step":"parse","message":"Extracting text from the PDF..."}
{"status":"progress","step":"chunks","message":"Creating chunks with metadata..."}
{"status":"progress","step":"qdrant","message":"Uploading chunks to Qdrant..."}
{"status":"done","step":"done","message":"PDF \"document.pdf\" processed and indexed successfully."}
```

---

### `POST /ask`

Receives a question and returns an answer generated with Gemini using Qdrant as the document source.

Request:

```json
{
  "question": "when was Mercedes-Benz founded",
  "top_k": 3
}
```

Test with `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "when was Mercedes-Benz founded", "top_k": 3}'
```

Expected response:

```json
{
  "answer": "Answer generated by Gemini...",
  "sources": [
    {
      "filename": "document.pdf",
      "page": "1",
      "chunk_index": "0",
      "score": 0.78
    }
  ]
}
```

---

## 8. Upload PDFs from the Frontend

In the web interface:

```text
1. Click “Choose PDF”
2. Select a .pdf file
3. Click “Upload”
4. Wait for the chat to show:
   - Saving PDF
   - Extracting text
   - Creating chunks
   - Uploading chunks to Qdrant
   - PDF processed successfully
5. Ask questions about the document in the chat
```

PDFs are saved in:

```text
backend/documentos/
```

---

## 9. Backend Scripts

### `01_liteparse_pdf_a_txt.py`

Converts PDFs into text and generates page-by-page extraction.

Input:

```text
backend/documentos/*.pdf
```

Output:

```text
backend/documentos-parseados/*.txt
backend/documentos-parseados/*.pages.jsonl
```

Run manually:

```bash
cd backend
source ../.venv/bin/activate
python 01_liteparse_pdf_a_txt.py
```

---

### `02_langchain_chunking.py`

Reads `.pages.jsonl` files and generates chunks with metadata.

Input:

```text
backend/documentos-parseados/*.pages.jsonl
```

Output:

```text
backend/chunks/chunks.jsonl
```

Run manually:

```bash
python 02_langchain_chunking.py
```

---

### `03_embeddings_locales.py`

Generates local embeddings from the chunks.

Input:

```text
backend/chunks/chunks.jsonl
```

Output:

```text
backend/embeddings/embeddings.npy
```

Run manually:

```bash
python 03_embeddings_locales.py
```

---

### `04_busqueda_semantica.py`

Allows local semantic search testing without Qdrant.

Run:

```bash
python 04_busqueda_semantica.py
```

---

### `05_subir_chunks_a_qdrant.py`

Reads `chunks/chunks.jsonl`, generates embeddings and uploads the chunks to Qdrant.

It also:

```text
- Checks whether the collection exists
- Validates the vector dimension
- Creates the document_id payload index if needed
- Deletes old chunks with the same document_id
- Uploads the new chunks
```

Run:

```bash
python 05_subir_chunks_a_qdrant.py
```

Test search after uploading:

```bash
python 05_subir_chunks_a_qdrant.py --query "when was Mercedes-Benz founded" --top-k 5
```

---

### `06_ask_rag.py`

Runs the full RAG flow in script mode:

```text
Question
↓
Local embedding of the question
↓
Search in Qdrant
↓
Context construction
↓
Answer with Gemini
```

Run:

```bash
python 06_ask_rag.py "when was Mercedes-Benz founded" --show-sources
```

---

## 10. Completely Recreate the Qdrant Collection

If you want to delete the entire collection and recreate it from scratch:

```bash
cd backend
source ../.venv/bin/activate
python 05_subir_chunks_a_qdrant.py --recreate-collection
```

You can also recreate it and run a test search:

```bash
python 05_subir_chunks_a_qdrant.py --recreate-collection --query "when was Mercedes-Benz founded" --top-k 5
```

Use this command when:

```text
- You change the embedding model
- You change the vector dimension
- The collection became inconsistent
- You want to delete old data
- You want to prepare a demo from scratch
```

---

## 11. Partial Cleanup in Qdrant

The normal flow does not delete the whole collection.

When you upload a document with the same `document_id`, the script:

```text
1. Finds old chunks with that document_id
2. Deletes them
3. Uploads the new chunks
```

For this to work in Qdrant Cloud, the script creates a payload index:

```text
document_id → keyword
```

This prevents errors such as:

```text
Index required but not found for "document_id" of type keyword
```

---

## 12. Chunk Metadata

Each chunk is stored with useful metadata for traceability.

Example:

```json
{
  "id": "bmw_informacion_rag_p001_c000",
  "text": "Chunk text...",
  "metadata": {
    "source": "bmw_informacion_rag.pdf",
    "filename": "bmw_informacion_rag.pdf",
    "document_id": "bmw_informacion_rag",
    "source_type": "pdf",
    "page": 1,
    "page_label": "1",
    "language": "en",
    "chunk_index": 0,
    "chunk_index_in_page": 0,
    "chunk_size": 921
  }
}
```

In Qdrant, the payload contains fields such as:

```text
text
source
filename
document_id
source_type
page
page_label
language
chunk_index
chunk_index_in_page
chunk_size
```

This makes it possible to display sources in the answer:

```text
bmw_informacion_rag.pdf, page 3
```

---

## 13. Recommended Gemini Configuration

In `backend/.env`:

```env
GEMINI_MODEL=gemini-2.5-flash-lite
RAG_TOP_K=3
RAG_MAX_CONTEXT_CHARS=5000
```

If Gemini returns a 503 error:

```text
503 UNAVAILABLE
This model is currently experiencing high demand
```

It does not mean the project is wrong. It means Gemini is temporarily overloaded.

Solutions:

```text
- Wait a few seconds and retry
- Reduce RAG_TOP_K
- Reduce RAG_MAX_CONTEXT_CHARS
- Use gemini-2.5-flash-lite
- Add a fallback to another provider such as Groq
```

---

## 14. Git and Security

Do not upload these files or folders to the repository:

```text
.env
.venv/
__pycache__/
*.pyc
.DS_Store
__MACOSX/
backend/embeddings/
backend/chunks/
backend/documentos-parseados/
```

Optionally, if you do not want to upload PDFs to the repository:

```text
backend/documentos/
```

Example `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.DS_Store
__MACOSX/

backend/.env
backend/embeddings/
backend/chunks/
backend/documentos-parseados/

frontend/node_modules/
frontend/.env.local
```

If an API key was accidentally uploaded to GitHub:

```text
1. Revoke the key
2. Create a new one
3. Update your local .env file
```

---

## 15. Useful Commands

### Activate the Virtual Environment from Backend

```bash
source ../.venv/bin/activate
```

### Check That You Are Using the Correct Virtual Environment

```bash
which python
```

It should return something similar to:

```text
/Users/candeladavilamoreno/Documents/GitHub/Proyecto-Prueba-RAG/.venv/bin/python
```

### Check Loaded Configuration

```bash
python -c "from config import GEMINI_MODEL, RAG_TOP_K, RAG_MAX_CONTEXT_CHARS; print(GEMINI_MODEL, RAG_TOP_K, RAG_MAX_CONTEXT_CHARS)"
```

Expected output:

```text
gemini-2.5-flash-lite 3 5000
```

### Start Backend

```bash
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

### Test PDF Upload

```bash
curl -N -X POST "http://127.0.0.1:8000/upload-stream" \
  -F "file=@/path/to/your/document.pdf"
```

### Test a Question

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "when was Mercedes-Benz founded", "top_k": 3}'
```

### Recreate the Qdrant Collection

```bash
cd backend
source ../.venv/bin/activate
python 05_subir_chunks_a_qdrant.py --recreate-collection
```

---

## 16. Current Project Status

The project currently supports:

```text
- Creating a React chat frontend
- Uploading PDFs from the interface
- Showing document processing progress in the chat
- Saving PDFs in backend/documentos/
- Extracting text from PDFs
- Creating chunks with metadata
- Creating local embeddings
- Creating/verifying a Qdrant collection
- Creating a payload index for document_id
- Deleting old chunks by document_id
- Uploading new chunks to Qdrant
- Asking questions from the chat
- Retrieving relevant chunks
- Generating final answers with Gemini
- Showing the sources used by the retrieved chunks
```

---

## 17. Recommended Next Steps

```text
1. Improve the chat design
2. Add a button to delete documents
3. Add an indicator showing whether Qdrant is connected
4. Add a fallback to Groq if Gemini returns 503
5. Convert scripts into Python functions instead of running them with subprocess
6. Deploy the frontend and backend
```
