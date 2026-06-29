import { useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hola. Soy tu asistente RAG. Hazme una pregunta sobre los documentos cargados.",
      sources: [],
    },
  ]);

  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function sendQuestion() {
    const cleanQuestion = question.trim();

    if (!cleanQuestion || isLoading) {
      return;
    }

    const userMessage = {
      role: "user",
      text: cleanQuestion,
      sources: [],
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: cleanQuestion,
          top_k: 5,
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
      setIsLoading(false);
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
            <p>Pregunta sobre tus documentos indexados en Qdrant</p>
          </div>

          <div className="status-pill">
            <span className="status-dot"></span>
            Local
          </div>
        </header>

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
                <p>{message.text}</p>

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

          {isLoading && (
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

          <button onClick={sendQuestion} disabled={isLoading || !question.trim()}>
            {isLoading ? "Enviando..." : "Enviar"}
          </button>
        </footer>
      </div>
    </div>
  );
}

export default App;