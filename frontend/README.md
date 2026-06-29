# Chat personalizado sobre documentos

Aplicación RAG local que permite subir documentos PDF, indexarlos en Qdrant y hacer preguntas sobre ellos desde un chat web personalizado.

El proyecto usa:

```text
React + Vite
FastAPI
LangChain
sentence-transformers
Qdrant Cloud
Gemini API
```

El usuario puede:

```text
1. Subir PDFs desde la interfaz web
2. Ver los documentos disponibles como checkboxes
3. Seleccionar qué documentos usar como fuente
4. Escribir una pregunta en el chat
5. Recibir una respuesta generada con Gemini usando solo los documentos seleccionados
6. Ver las fuentes utilizadas en la respuesta
```

---

## Índice

```text
1. Requisitos previos
2. Cuentas necesarias
3. Archivos y carpetas que hay que crear
4. Configuración paso a paso
5. Cómo ejecutar el proyecto
6. Uso de la aplicación
7. Pipeline completo explicado paso a paso
8. Endpoints del backend
9. Scripts del backend
10. Qdrant
11. Gemini
12. Estructura del proyecto
13. Troubleshooting
14. Mejoras futuras
15. Autor
```

---

# 1. Requisitos previos

Antes de empezar necesitas tener instalado:

```text
Python 3.10+
Node.js 18+
npm
Git
```

Comprueba las versiones:

```bash
python3 --version
node --version
npm --version
git --version
```

---

# 2. Cuentas necesarias

## 2.1. Qdrant Cloud

Necesitas una cuenta en Qdrant Cloud para guardar los embeddings de tus documentos.

Pasos:

```text
1. Crear cuenta en Qdrant Cloud
2. Crear un cluster gratuito
3. Copiar la URL del cluster
4. Crear/copiar una API key
5. Guardar esos valores en backend/.env
```

Variables que necesitarás:

```env
QDRANT_URL=https://TU_CLUSTER.qdrant.io
QDRANT_API_KEY=TU_API_KEY_QDRANT
QDRANT_COLLECTION=documentos_rag
```

Para este proyecto se usa una colección de Qdrant llamada:

```text
documentos_rag
```

Puedes cambiar el nombre si quieres, pero debe coincidir con `QDRANT_COLLECTION`.

---

## 2.2. Google AI Studio / Gemini API

Necesitas una API key de Gemini para generar las respuestas finales.

Pasos:

```text
1. Entrar en Google AI Studio
2. Ir a API keys
3. Crear una API key
4. Usar un proyecto en Free Tier si quieres evitar costes
5. No activar billing si quieres que al agotarse la cuota simplemente falle
6. Copiar la API key en backend/.env
```

Variables necesarias:

```env
GEMINI_API_KEY=TU_API_KEY_GEMINI
GEMINI_MODEL=gemini-2.5-flash-lite
```

Si un modelo llega al límite diario, puedes cambiar el modelo desde Google AI Studio y actualizar `GEMINI_MODEL`.

---

# 3. Archivos y carpetas que hay que crear

El proyecto tiene dos partes principales:

```text
backend/
frontend/
```

## 3.1. Carpetas del backend

Dentro de `backend/` deben existir estas carpetas:

```text
backend/documentos/
backend/documentos-parseados/
backend/chunks/
backend/embeddings/
```

Se pueden crear con:

```bash
mkdir -p backend/documentos
mkdir -p backend/documentos-parseados
mkdir -p backend/chunks
mkdir -p backend/embeddings
```

Uso de cada carpeta:

```text
backend/documentos/
Guarda los PDFs subidos por el usuario.

backend/documentos-parseados/
Guarda el texto extraído de los PDFs y los JSONL página a página.

backend/chunks/
Guarda chunks/chunks.jsonl con todos los fragmentos generados.

backend/embeddings/
Guarda embeddings locales si se ejecuta el script de embeddings local.
```

---

## 3.2. Archivos del backend

Dentro de `backend/` deben existir:

```text
backend/main.py
backend/config.py
backend/01_liteparse_pdf_a_txt.py
backend/02_langchain_chunking.py
backend/03_embeddings_locales.py
backend/04_busqueda_semantica.py
backend/05_subir_chunks_a_qdrant.py
backend/06_ask_rag.py
backend/requirements.txt
backend/.env
```

Descripción rápida:

```text
main.py
API con FastAPI. Gestiona /ask, /documents y /upload-stream.

config.py
Centraliza rutas, variables de entorno, modelo de embeddings, Qdrant y Gemini.

01_liteparse_pdf_a_txt.py
Extrae texto de PDFs y genera archivos .txt y .pages.jsonl.

02_langchain_chunking.py
Crea chunks con metadata a partir de los archivos .pages.jsonl.

03_embeddings_locales.py
Genera embeddings locales para pruebas.

04_busqueda_semantica.py
Permite probar búsqueda semántica local.

05_subir_chunks_a_qdrant.py
Genera embeddings y sube los chunks a Qdrant.

06_ask_rag.py
Busca en Qdrant, construye el contexto y llama a Gemini.

requirements.txt
Dependencias de Python.

.env
Variables privadas de configuración.
```

---

## 3.3. Archivos del frontend

Dentro de `frontend/` deben existir:

```text
frontend/src/App.jsx
frontend/src/App.css
frontend/src/index.css
frontend/src/main.jsx
frontend/index.html
frontend/.env.local
frontend/package.json
```

Descripción rápida:

```text
App.jsx
Interfaz del chat, subida de PDFs, checkboxes de documentos y llamadas al backend.

App.css
Estilos visuales de la aplicación.

index.css
Estilos globales.

main.jsx
Entrada principal de React.

index.html
HTML base y título de la página.

.env.local
URL local del backend.
```

---

# 4. Configuración paso a paso

## 4.1. Clonar el repositorio

```bash
git clone https://github.com/candeladavila/Proyecto-Prueba-RAG.git
cd Proyecto-Prueba-RAG
```

---

## 4.2. Crear entorno virtual de Python

Desde la raíz del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows:

```bash
.venv\Scripts\activate
```

---

## 4.3. Instalar dependencias del backend

```bash
cd backend
pip install -r requirements.txt
```

Si falta alguna dependencia:

```bash
pip install fastapi "uvicorn[standard]" python-multipart python-dotenv qdrant-client langchain-text-splitters langchain-huggingface sentence-transformers google-genai pypdf numpy
```

`backend/requirements.txt` debería contener:

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

## 4.4. Crear `backend/.env`

En `backend/.env`:

```env
QDRANT_URL=https://TU_CLUSTER.qdrant.io
QDRANT_API_KEY=TU_API_KEY_QDRANT
QDRANT_COLLECTION=documentos_rag

GEMINI_API_KEY=TU_API_KEY_GEMINI
GEMINI_MODEL=gemini-2.5-flash-lite

RAG_TOP_K=3
RAG_MAX_CONTEXT_CHARS=5000

EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Importante:

```text
No subas backend/.env a GitHub.
No pongas API keys en React.
No actives billing en Gemini si quieres evitar costes.
```

---

## 4.5. Crear el frontend

Si todavía no existe:

```bash
cd ..
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

---

## 4.6. Crear `frontend/.env.local`

En `frontend/.env.local`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

---

## 4.7. Cambiar título de la página

En `frontend/index.html`:

```html
<title>Chat personalizado sobre documentos</title>
```

---

# 5. Cómo ejecutar el proyecto

Necesitas dos terminales.

---

## 5.1. Terminal 1: backend

Desde la raíz del proyecto:

```bash
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend disponible en:

```text
http://127.0.0.1:8000
```

Comprobar que funciona:

```bash
curl http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

---

## 5.2. Terminal 2: frontend

Desde la raíz del proyecto:

```bash
cd frontend
npm run dev
```

Frontend disponible en:

```text
http://localhost:5173
```

---

# 6. Uso de la aplicación

## 6.1. Subir un PDF

En la interfaz:

```text
1. Pulsar el botón PDF
2. Elegir un archivo .pdf
3. Pulsar Subir
4. Esperar el progreso en el chat
```

El chat mostrará pasos como:

```text
• Guardando PDF
• Extrayendo texto del PDF
• Creando chunks con metadata
• Subiendo chunks a Qdrant
✓ PDF procesado e indexado correctamente
```

El PDF se guarda en:

```text
backend/documentos/
```

---

## 6.2. Seleccionar fuentes

En la parte inferior del chat aparece un listado de documentos disponibles.

Cada documento aparece como checkbox.

Por defecto, todos los documentos están marcados.

Puedes:

```text
- Usar todos los documentos
- Desmarcar documentos concretos
- Pulsar “Todas”
- Pulsar “Ninguna”
```

La pregunta solo usará como contexto los documentos seleccionados.

---

## 6.3. Preguntar al chat

Escribe una pregunta en el área de texto y pulsa:

```text
Enviar
```

Ejemplo:

```text
¿Cuándo se fundó BMW?
```

El sistema buscará chunks relevantes solo en los documentos seleccionados, enviará el contexto a Gemini y devolverá una respuesta con fuentes.

---

# 7. Pipeline completo explicado paso a paso

## Paso 1: El usuario sube un PDF

El usuario selecciona un archivo PDF desde el frontend.

React envía el archivo al backend mediante:

```text
POST /upload-stream
```

El archivo viaja como `FormData`.

---

## Paso 2: FastAPI recibe el PDF

El endpoint `POST /upload-stream` está en:

```text
backend/main.py
```

Este endpoint:

```text
1. Comprueba que el archivo sea PDF
2. Limpia el nombre del archivo
3. Guarda el archivo en backend/documentos/
4. Devuelve eventos de progreso al frontend
```

Ejemplo de evento:

```json
{"status":"progress","step":"save","message":"Guardando PDF: documento.pdf"}
```

---

## Paso 3: El PDF se guarda en `/documentos`

El archivo queda almacenado aquí:

```text
backend/documentos/nombre_del_documento.pdf
```

Esta carpeta es la fuente principal de documentos del sistema.

El endpoint:

```text
GET /documents
```

lee esta carpeta y devuelve todos los PDFs disponibles al frontend.

---

## Paso 4: Extracción de texto

Después de guardar el PDF, el backend ejecuta:

```bash
python 01_liteparse_pdf_a_txt.py
```

Este script lee:

```text
backend/documentos/*.pdf
```

y genera:

```text
backend/documentos-parseados/*.txt
backend/documentos-parseados/*.pages.jsonl
```

El archivo `.txt` contiene el texto completo.

El archivo `.pages.jsonl` conserva la información por página.

Ejemplo:

```json
{
  "document_id": "bmw_informacion_rag",
  "filename": "bmw_informacion_rag.pdf",
  "source": "bmw_informacion_rag.pdf",
  "source_type": "pdf",
  "page": 1,
  "page_label": "1",
  "text": "Texto extraído de la página..."
}
```

---

## Paso 5: Creación de chunks

Después se ejecuta:

```bash
python 02_langchain_chunking.py
```

Este script lee:

```text
backend/documentos-parseados/*.pages.jsonl
```

y genera:

```text
backend/chunks/chunks.jsonl
```

Cada chunk contiene:

```text
- id
- text
- metadata
```

Ejemplo:

```json
{
  "id": "bmw_informacion_rag_p001_c000",
  "text": "Texto del chunk...",
  "metadata": {
    "source": "bmw_informacion_rag.pdf",
    "filename": "bmw_informacion_rag.pdf",
    "document_id": "bmw_informacion_rag",
    "source_type": "pdf",
    "page": 1,
    "page_label": "1",
    "language": "es",
    "chunk_index": 0,
    "chunk_index_in_page": 0,
    "chunk_size": 921
  }
}
```

El campo más importante para filtrar por documento es:

```text
document_id
```

---

## Paso 6: Generación de embeddings

Después se ejecuta:

```bash
python 05_subir_chunks_a_qdrant.py
```

Este script carga el modelo definido en `.env`:

```env
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Cada chunk se convierte en un vector de embeddings.

Ese modelo genera vectores de dimensión:

```text
384
```

---

## Paso 7: Validación de colección en Qdrant

El script comprueba si la colección existe.

Si no existe, la crea:

```text
QDRANT_COLLECTION=documentos_rag
```

Si existe, comprueba que la dimensión vectorial sea correcta.

Esto evita errores cuando cambias de modelo de embeddings.

---

## Paso 8: Creación del índice `document_id`

Para poder filtrar por documentos seleccionados, Qdrant necesita un índice de payload sobre:

```text
document_id
```

El script crea:

```text
document_id → keyword
```

Esto permite:

```text
- borrar chunks antiguos de un documento concreto
- buscar solo dentro de documentos seleccionados
```

---

## Paso 9: Limpieza parcial de Qdrant

Antes de subir chunks nuevos, el script borra los chunks antiguos del mismo documento usando:

```text
document_id
```

Ejemplo:

```text
document_id=bmw_informacion_rag
```

Esto evita duplicados al volver a subir el mismo PDF.

No borra toda la colección.

---

## Paso 10: Subida de chunks a Qdrant

Cada point en Qdrant contiene:

```text
id
vector
payload
```

El payload contiene:

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

---

## Paso 11: El frontend actualiza los documentos

Cuando termina la subida, React llama a:

```text
GET /documents
```

y actualiza la lista de checkboxes.

Los documentos nuevos aparecen marcados por defecto.

---

## Paso 12: El usuario hace una pregunta

React envía:

```text
POST /ask
```

con este body:

```json
{
  "question": "¿Cuándo se fundó BMW?",
  "top_k": 3,
  "document_ids": ["bmw_informacion_rag"]
}
```

---

## Paso 13: Qdrant recupera chunks relevantes

El backend convierte la pregunta en embedding usando el mismo modelo usado para los documentos.

Después busca en Qdrant usando filtro:

```text
document_id IN documentos seleccionados
```

Qdrant devuelve los chunks más parecidos semánticamente.

---

## Paso 14: Construcción del prompt

`06_ask_rag.py` construye un prompt con:

```text
- instrucciones
- contexto recuperado
- pregunta del usuario
```

El prompt obliga al modelo a:

```text
- responder en español
- usar solo el contexto proporcionado
- no inventar información
- incluir fuentes
```

---

## Paso 15: Respuesta con Gemini

El backend llama a Gemini con:

```text
GEMINI_MODEL
```

Gemini genera la respuesta final usando el contexto recibido.

---

## Paso 16: El frontend muestra respuesta y fuentes

React muestra la respuesta en forma de bocadillo de chat.

Si hay fuentes, aparecen como:

```text
bmw_informacion_rag.pdf, página 2
```

---

# 8. Endpoints del backend

## `GET /health`

Comprueba si la API está viva.

```bash
curl http://127.0.0.1:8000/health
```

Respuesta:

```json
{"status":"ok"}
```

---

## `GET /documents`

Devuelve los PDFs disponibles.

```bash
curl http://127.0.0.1:8000/documents
```

Respuesta:

```json
{
  "documents": [
    {
      "document_id": "bmw_informacion_rag",
      "filename": "bmw_informacion_rag.pdf"
    }
  ]
}
```

---

## `POST /upload-stream`

Sube un PDF y devuelve progreso en streaming.

```bash
curl -N -X POST "http://127.0.0.1:8000/upload-stream" \
  -F "file=@/ruta/a/tu/documento.pdf"
```

Respuesta tipo NDJSON:

```json
{"status":"progress","step":"save","message":"Guardando PDF: documento.pdf"}
{"status":"progress","step":"parse","message":"Extrayendo texto del PDF..."}
{"status":"progress","step":"chunks","message":"Creando chunks con metadata..."}
{"status":"progress","step":"qdrant","message":"Subiendo chunks a Qdrant..."}
{"status":"done","step":"done","message":"PDF \"documento.pdf\" procesado e indexado correctamente."}
```

---

## `POST /ask`

Pregunta al RAG.

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuándo se fundó BMW?",
    "top_k": 3,
    "document_ids": ["bmw_informacion_rag"]
  }'
```

Respuesta:

```json
{
  "answer": "Respuesta generada por Gemini...",
  "sources": [
    {
      "filename": "bmw_informacion_rag.pdf",
      "page": "1",
      "chunk_index": "0",
      "score": 0.82
    }
  ]
}
```

---

# 9. Scripts del backend

## `01_liteparse_pdf_a_txt.py`

Extrae texto de PDFs.

Entrada:

```text
backend/documentos/*.pdf
```

Salida:

```text
backend/documentos-parseados/*.txt
backend/documentos-parseados/*.pages.jsonl
```

Ejecutar manualmente:

```bash
cd backend
source ../.venv/bin/activate
python 01_liteparse_pdf_a_txt.py
```

---

## `02_langchain_chunking.py`

Crea chunks con LangChain.

Entrada:

```text
backend/documentos-parseados/*.pages.jsonl
```

Salida:

```text
backend/chunks/chunks.jsonl
```

Ejecutar:

```bash
python 02_langchain_chunking.py
```

---

## `03_embeddings_locales.py`

Genera embeddings locales para pruebas.

```bash
python 03_embeddings_locales.py
```

---

## `04_busqueda_semantica.py`

Permite hacer búsqueda semántica local sin Qdrant.

```bash
python 04_busqueda_semantica.py
```

---

## `05_subir_chunks_a_qdrant.py`

Sube chunks a Qdrant.

Hace:

```text
1. Lee chunks/chunks.jsonl
2. Genera embeddings
3. Crea o valida la colección
4. Crea índice document_id
5. Borra chunks antiguos de documentos reindexados
6. Sube chunks nuevos
```

Ejecutar:

```bash
python 05_subir_chunks_a_qdrant.py
```

Recrear colección completa:

```bash
python 05_subir_chunks_a_qdrant.py --recreate-collection
```

Recrear y probar búsqueda:

```bash
python 05_subir_chunks_a_qdrant.py --recreate-collection \
  --query "¿Cuándo se fundó BMW?" \
  --top-k 5
```

---

## `06_ask_rag.py`

Script para hacer preguntas sin frontend.

```bash
python 06_ask_rag.py "¿Cuándo se fundó BMW?" --show-sources
```

Filtrar por documento:

```bash
python 06_ask_rag.py "¿Cuándo se fundó BMW?" \
  --document-id bmw_informacion_rag \
  --show-sources
```

---

# 10. Qdrant

Qdrant se usa como base de datos vectorial.

Guarda:

```text
embedding del chunk
texto del chunk
metadata del chunk
```

Cada registro se llama point.

Ejemplo conceptual:

```json
{
  "id": "uuid",
  "vector": [0.12, -0.05, 0.88],
  "payload": {
    "text": "Texto del chunk...",
    "filename": "bmw_informacion_rag.pdf",
    "document_id": "bmw_informacion_rag",
    "page": 1
  }
}
```

---

## Rehacer colección de Qdrant

Desde `backend/`:

```bash
source ../.venv/bin/activate
python 05_subir_chunks_a_qdrant.py --recreate-collection
```

Usar cuando:

```text
- Cambias el modelo de embeddings
- Cambias la dimensión vectorial
- Quieres limpiar pruebas antiguas
- Qdrant quedó inconsistente
- Quieres preparar una demo desde cero
```

---

## Limpieza parcial

El flujo normal no borra toda la colección.

Solo borra chunks antiguos del mismo:

```text
document_id
```

Esto permite actualizar un PDF sin eliminar los demás.

---

# 11. Gemini

Gemini se usa únicamente para generar la respuesta final.

No se usa para embeddings.

El flujo es:

```text
Pregunta del usuario
↓
Qdrant recupera chunks relevantes
↓
Gemini recibe pregunta + chunks
↓
Gemini redacta la respuesta final
```

Configuración recomendada:

```env
GEMINI_MODEL=gemini-2.5-flash-lite
RAG_TOP_K=3
RAG_MAX_CONTEXT_CHARS=5000
```

Si Gemini devuelve:

```text
429 RESOURCE_EXHAUSTED
```

significa que se ha alcanzado un límite de cuota.

Si devuelve:

```text
503 UNAVAILABLE
```

significa que el modelo puede estar saturado temporalmente.

Soluciones:

```text
- Esperar unos segundos/minutos
- Cambiar de modelo
- Reducir RAG_TOP_K
- Reducir RAG_MAX_CONTEXT_CHARS
- Añadir un proveedor alternativo como Groq
```

---

# 12. Estructura del proyecto

```text
Proyecto-Prueba-RAG/
├── .venv/
├── backend/
│   ├── documentos/
│   │   └── *.pdf
│   ├── documentos-parseados/
│   │   ├── *.txt
│   │   └── *.pages.jsonl
│   ├── chunks/
│   │   └── chunks.jsonl
│   ├── embeddings/
│   │   └── embeddings.npy
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
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── .env.local
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```

---

# 13. Troubleshooting

## `python: command not found`

Usar:

```bash
python3
```

o activar la venv:

```bash
source ../.venv/bin/activate
```

Comprobar:

```bash
which python
```

Debe apuntar a:

```text
.venv/bin/python
```

---

## `ModuleNotFoundError: No module named 'dotenv'`

Instalar:

```bash
pip install python-dotenv
```

---

## `ModuleNotFoundError: No module named 'langchain_huggingface'`

Instalar:

```bash
pip install langchain-huggingface
```

---

## `No module named backend`

Si ejecutas scripts desde dentro de `backend/`, los imports deben ser:

```python
from config import ...
```

no:

```python
from backend.config import ...
```

---

## Error de Qdrant: `Index required but not found for document_id`

Solución: asegurarse de que `05_subir_chunks_a_qdrant.py` crea el índice:

```python
client.create_payload_index(
    collection_name=collection_name,
    field_name="document_id",
    field_schema=models.PayloadSchemaType.KEYWORD,
    wait=True,
)
```

---

## El PDF se sube pero no aparece en las respuestas

Comprobar que el upload ejecuta:

```text
01_liteparse_pdf_a_txt.py
02_langchain_chunking.py
05_subir_chunks_a_qdrant.py
```

También comprobar:

```bash
curl http://127.0.0.1:8000/documents
```

---

## El frontend no conecta con el backend

Revisar `frontend/.env.local`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Reiniciar frontend:

```bash
npm run dev
```

---

# 14. Mejoras futuras

## Mejoras funcionales

* [ ] Añadir botón para borrar documentos desde la interfaz.
* [ ] Mostrar fecha de subida de cada PDF.
* [ ] Mostrar número de páginas de cada documento.
* [ ] Mostrar número de chunks generados por documento.
* [ ] Añadir vista de fuentes más detallada.
* [ ] Permitir descargar el texto parseado.
* [ ] Permitir subir varios PDFs a la vez.
* [ ] Añadir soporte para `.txt`, `.docx` y `.md`.
* [ ] Añadir autenticación de usuarios.
* [ ] Añadir historial de conversaciones.

## Mejoras RAG

* [ ] Añadir reranking de chunks.
* [ ] Añadir búsqueda híbrida: vectorial + keyword search.
* [ ] Añadir filtros por metadata: fecha, marca, categoría, idioma.
* [ ] Añadir resúmenes automáticos por documento.
* [ ] Añadir citas más precisas por página y sección.
* [ ] Añadir deduplicación de chunks similares.
* [ ] Añadir evaluación automática de respuestas.
* [ ] Añadir fallback a Groq si Gemini falla.
* [ ] Añadir streaming de respuesta del LLM.
* [ ] Añadir memoria conversacional con control de contexto.

## Mejoras técnicas

* [ ] Convertir scripts en funciones importables en vez de ejecutarlos con `subprocess`.
* [ ] Separar backend en módulos: `routes/`, `services/`, `rag/`, `storage/`.
* [ ] Añadir tests unitarios.
* [ ] Añadir tests de integración.
* [ ] Añadir Dockerfile para backend.
* [ ] Añadir Docker Compose para frontend + backend.
* [ ] Añadir logging estructurado.
* [ ] Añadir control de errores más detallado.
* [ ] Añadir barra de progreso real por documento.
* [ ] Añadir despliegue en cloud.

## Mejoras de interfaz

* [ ] Mejorar diseño responsive móvil.
* [ ] Añadir modo oscuro.
* [ ] Añadir drag & drop para subir PDFs.
* [ ] Añadir estado de conexión con Qdrant y Gemini.
* [ ] Añadir contador de documentos seleccionados.
* [ ] Añadir botón para limpiar chat.
* [ ] Añadir animación de procesamiento de PDF.
* [ ] Añadir vista lateral de documentos.

---

# 15. Seguridad

No subir a GitHub:

```text
.env
.venv/
__pycache__/
*.pyc
.DS_Store
__MACOSX/
frontend/node_modules/
frontend/.env.local
backend/.env
backend/embeddings/
backend/chunks/
backend/documentos-parseados/
```

Si no quieres subir PDFs:

```text
backend/documentos/
```

Ejemplo de `.gitignore`:

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

Si una API key se subió por error:

```text
1. Revocar la key
2. Crear una nueva
3. Actualizar backend/.env
4. Hacer commit eliminando la key del repo
```

---

# 16. Comandos útiles

## Activar entorno virtual desde backend

```bash
source ../.venv/bin/activate
```

---

## Comprobar configuración

```bash
python -c "from config import GEMINI_MODEL, RAG_TOP_K, RAG_MAX_CONTEXT_CHARS; print(GEMINI_MODEL, RAG_TOP_K, RAG_MAX_CONTEXT_CHARS)"
```

---

## Arrancar backend

```bash
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## Arrancar frontend

```bash
cd frontend
npm run dev
```

---

## Probar documentos

```bash
curl http://127.0.0.1:8000/documents
```

---

## Probar subida de PDF

```bash
curl -N -X POST "http://127.0.0.1:8000/upload-stream" \
  -F "file=@/ruta/a/tu/documento.pdf"
```

---

## Probar pregunta

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuándo se fundó BMW?",
    "top_k": 3,
    "document_ids": ["bmw_informacion_rag"]
  }'
```

---

## Rehacer colección Qdrant

```bash
cd backend
source ../.venv/bin/activate
python 05_subir_chunks_a_qdrant.py --recreate-collection
```

---

# 17. Autor

Desarrollado por **Candela Dávila Moreno**.

GitHub:

```text
@candeladavila
```

Repositorio:

```text
https://github.com/candeladavila/Proyecto-Prueba-RAG
```

---

# 18. Resumen final

Este proyecto implementa un sistema RAG completo en local:

```text
PDF
↓
Texto
↓
Chunks
↓
Embeddings
↓
Qdrant
↓
Recuperación semántica
↓
Gemini
↓
Respuesta con fuentes
```

La interfaz permite subir PDFs, seleccionar fuentes mediante checkboxes y hacer preguntas personalizadas sobre los documentos cargados.
