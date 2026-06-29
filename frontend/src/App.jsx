import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      text: "Hola. Soy tu chat personalizado sobre documentos. Selecciona las fuentes y hazme una pregunta.",
      sources: [],
    },
  ]);

  const [question, setQuestion] = useState("");
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  const [isLoadingAnswer, setIsLoadingAnswer] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents`);

      if (!response.ok) {
        throw new Error("No se pudieron cargar los documentos.");
      }

      const data = await response.json();
      const loadedDocuments = data.documents || [];

      setDocuments(loadedDocuments);
      setSelectedDocumentIds(loadedDocuments.map((document) => document.document_id));
    } catch (error) {
      setUploadMessage(`Error cargando documentos: ${error.message}`);
    }
  }

  function toggleDocument(documentId) {
    setSelectedDocumentIds((previousSelected) => {
      if (previousSelected.includes(documentId)) {
        return previousSelected.filter((id) => id !== documentId);
      }

      return [...previousSelected, documentId];
    });
  }

  function selectAllDocuments() {
    setSelectedDocumentIds(documents.map((document) => document.document_id));
  }

  function clearDocumentSelection() {
    setSelectedDocumentIds([]);
  }

  async function uploadPdf() {
    if (!selectedFile || isUploadingFile) {
      return;
    }

    if (selectedFile.type !== "application/pdf") {
      setUploadMessage("Solo puedes subir archivos PDF.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    const uploadMessageId =
      crypto.randomUUID?.() || `upload-${Date.now().toString()}`;

    setIsUploadingFile(true);
    setUploadMessage("Subiendo PDF...");

    setMessages((previousMessages) => [
      ...previousMessages,
      {
        id: uploadMessageId,
        role: "assistant",
        text: `Preparando subida de "${selectedFile.name}"...`,
        sources: [],
        isProgress: true,
      },
    ]);

    function updateUploadBubble(text) {
      setMessages((previousMessages) =>
        previousMessages.map((message) =>
          message.id === uploadMessageId
            ? {
                ...message,
                text,
              }
            : message
        )
      );
    }

    try {
      const response = await fetch(`${API_URL}/upload-stream`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || "Error subiendo el archivo.";
        throw new Error(errorMessage);
      }

      if (!response.body) {
        throw new Error("El backend no devolvió un stream de progreso.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      let progressLines = [];

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }

          const event = JSON.parse(line);

          if (event.status === "progress") {
            progressLines.push(`• ${event.message}`);
            updateUploadBubble(progressLines.join("\n"));
            setUploadMessage(event.message);
          }

          if (event.status === "done") {
            progressLines.push(`✓ ${event.message}`);
            updateUploadBubble(progressLines.join("\n"));
            setUploadMessage(event.message);
            setSelectedFile(null);
            await loadDocuments();
          }

          if (event.status === "error") {
            progressLines.push(`✕ ${event.message}`);
            updateUploadBubble(progressLines.join("\n"));
            setUploadMessage(event.message);
            throw new Error(event.message);
          }
        }
      }
    } catch (error) {
      setUploadMessage(`Error: ${error.message}`);

      setMessages((previousMessages) =>
        previousMessages.map((message) =>
          message.id === uploadMessageId
            ? {
                ...message,
                text: `Error procesando el PDF:\n${error.message}`,
                isProgress: false,
              }
            : message
        )
      );
    } finally {
      setIsUploadingFile(false);
    }
  }

  async function sendQuestion() {
    const cleanQuestion = question.trim();

    if (!cleanQuestion || isLoadingAnswer) {
      return;
    }

    if (selectedDocumentIds.length === 0) {
      setMessages((previousMessages) => [
        ...previousMessages,
        {
          id: crypto.randomUUID?.() || `error-${Date.now().toString()}`,
          role: "assistant",
          text: "Selecciona al menos un documento como fuente antes de preguntar.",
          sources: [],
        },
      ]);
      return;
    }

    const userMessage = {
      id: crypto.randomUUID?.() || `user-${Date.now().toString()}`,
      role: "user",
      text: cleanQuestion,
      sources: [],
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setQuestion("");
    setIsLoadingAnswer(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: cleanQuestion,
          top_k: 3,
          document_ids: selectedDocumentIds,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage =
          errorData?.detail || "Ha ocurrido un error llamando al backend.";

        throw new Error(errorMessage);
      }

      const data = await response.json();

      const assistantMessage = {
        id: crypto.randomUUID?.() || `assistant-${Date.now().toString()}`,
        role: "assistant",
        text: data.answer,
        sources: data.sources || [],
      };

      setMessages((previousMessages) => [
        ...previousMessages,
        assistantMessage,
      ]);
    } catch (error) {
      const errorMessage = {
        id: crypto.randomUUID?.() || `error-${Date.now().toString()}`,
        role: "assistant",
        text: `Error: ${error.message}`,
        sources: [],
      };

      setMessages((previousMessages) => [...previousMessages, errorMessage]);
    } finally {
      setIsLoadingAnswer(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendQuestion();
    }
  }

  return (
    <div className="app">
      <div className="chat-card">
        <header className="chat-header">
          <div>
            <h1>Chat personalizado sobre documentos</h1>
            <p>Sube PDFs, selecciona fuentes y pregunta sobre su contenido</p>
          </div>

          <div className="status-pill">
            <span className="status-dot"></span>
            Local
          </div>
        </header>

        <main className="messages">
          {messages.map((message, index) => (
            <div
              key={message.id || index}
              className={`message-row ${
                message.role === "user" ? "user-row" : "assistant-row"
              }`}
            >
              <div
                className={`bubble ${
                  message.role === "user" ? "user-bubble" : "assistant-bubble"
                }`}
              >
                <p className={message.isProgress ? "progress-text" : ""}>
                  {message.text}
                </p>

                {message.sources.length > 0 && (
                  <div className="sources">
                    <strong>Fuentes</strong>

                    {message.sources.map((source, sourceIndex) => (
                      <div key={sourceIndex} className="source-item">
                        {source.filename}, página {source.page}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoadingAnswer && (
            <div className="message-row assistant-row">
              <div className="bubble assistant-bubble typing-bubble">
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            </div>
          )}
        </main>

        <footer className="composer">
          <div className="sources-panel">
            <div className="sources-header">
              <div>
                <strong>Fuentes disponibles</strong>
                <span>{selectedDocumentIds.length} seleccionadas</span>
              </div>

              <div className="sources-actions">
                <button type="button" onClick={selectAllDocuments}>
                  Todas
                </button>
                <button type="button" onClick={clearDocumentSelection}>
                  Ninguna
                </button>
              </div>
            </div>

            <div className="document-checkboxes">
              {documents.length === 0 ? (
                <span className="empty-documents">
                  Todavía no hay PDFs subidos.
                </span>
              ) : (
                documents.map((document) => (
                  <label key={document.document_id} className="document-option">
                    <input
                      type="checkbox"
                      checked={selectedDocumentIds.includes(document.document_id)}
                      onChange={() => toggleDocument(document.document_id)}
                    />
                    <span>{document.filename}</span>
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="input-row">
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu pregunta..."
              rows="3"
            />

            <div className="input-buttons">
              <label className="upload-inline-button">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => {
                    const file = event.target.files?.[0] || null;
                    setSelectedFile(file);
                    setUploadMessage(file ? file.name : "");
                  }}
                />
                PDF
              </label>

              <button
                className="upload-action-button"
                onClick={uploadPdf}
                disabled={!selectedFile || isUploadingFile}
              >
                {isUploadingFile ? "Subiendo..." : "Subir"}
              </button>

              <button
                className="send-button"
                onClick={sendQuestion}
                disabled={isLoadingAnswer || !question.trim()}
              >
                {isLoadingAnswer ? "Enviando..." : "Enviar"}
              </button>
            </div>
          </div>

          {uploadMessage && (
            <div className="upload-message">{uploadMessage}</div>
          )}
        </footer>
      </div>
    </div>
  );
}

export default App;