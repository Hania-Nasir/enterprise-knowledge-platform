import { useState } from "react";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const askQuestion = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setError("Please enter a question before searching.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      if (!response.ok) {
        if (response.status === 422) {
          throw new Error(
            "The question could not be processed. Please check your input and try again."
          );
        }

        if (response.status >= 500) {
          throw new Error(
            "The knowledge service encountered a problem while processing your question. Please try again."
          );
        }

        throw new Error(
          "The request could not be completed. Please try again."
        );
      }

      const data = await response.json();

      if (!data.answer) {
        throw new Error(
          "The knowledge service returned an unexpected response."
        );
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (error) {
      if (error.name === "TypeError") {
        setError(
          "The knowledge service is currently unavailable. Please make sure the backend is running and try again."
        );
      } else {
        setError(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Enterprise Knowledge Platform</h1>
        <p>
          Ask questions and get answers from your enterprise documentation.
        </p>
      </header>

      <main className="container">
        <div className="question-box">
          <textarea
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setError("");
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
              }
            }}
            placeholder="Ask a question about the documentation..."
            rows="4"
          />

          <button onClick={askQuestion} disabled={loading}>
            {loading ? "Searching documentation..." : "Ask Question"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {answer && (
          <section className="answer-section">
            <h2>Answer</h2>

            <div className="answer">
              {answer}
            </div>
          </section>
        )}

        {sources.length > 0 && (
          <section className="sources-section">
            <h2>Sources</h2>

            <div className="sources">
              {sources.map((source, index) => (
                <div className="source-card" key={index}>
                  <p>
                    <strong>Page</strong>
                    <br />
                    {source.page}
                  </p>

                  <p>
                    <strong>Chunk</strong>
                    <br />
                    {source.chunk_id}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;