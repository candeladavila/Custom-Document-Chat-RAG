import { useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hola. Soy tu asistente RAG. Sube un PDF o hazme una pregunta sobre los documentos ya indexados.",
      sources: [],
    },
  ]);

  const [question, setQuestion] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoadingAnswer, setIsLoadingAnswer] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

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

    const userMessage = {
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
            <h1>Mercedes RAG Chat</h1>
            <p>Sube PDFs y pregunta sobre tus documentos indexados</p>
          </div>

          <div className="status-pill">
            <span className="status-dot"></span>
            Local
          </div>
        </header>

        <section className="upload-panel">
          <div className="upload-info">
            <strong>Subir documento PDF</strong>
            <span>Se guardará en backend/documentos y se procesará automáticamente.</span>
          </div>

          <div className="upload-controls">
            <label className="file-label">
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) => {
                  const file = event.target.files?.[0] || null;
                  setSelectedFile(file);
                  setUploadMessage(file ? file.name : "");
                }}
              />
              Elegir PDF
            </label>

            <button
              className="upload-button"
              onClick={uploadPdf}
              disabled={!selectedFile || isUploadingFile}
            >
              {isUploadingFile ? "Procesando..." : "Subir"}
            </button>
          </div>

          {uploadMessage && (
            <div className="upload-message">{uploadMessage}</div>
          )}
        </section>

        <main className="messages">
          {messages.map((message, index) => (
            <div
              key={index}
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
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu pregunta..."
            rows="3"
          />

          <button
            onClick={sendQuestion}
            disabled={isLoadingAnswer || !question.trim()}
          >
            {isLoadingAnswer ? "Enviando..." : "Enviar"}
          </button>
        </footer>
      </div>
    </div>
  );
}

export default App;