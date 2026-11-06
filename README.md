# Enterprise Knowledge Platform

A production-style Retrieval-Augmented Generation (RAG) application for querying enterprise documentation using hybrid retrieval, reranking, and a grounded local LLM.

The current implementation uses the **Pexip Infinity Product User Guide** as its knowledge source.

## Overview

Enterprise documentation can be large and difficult to search through manually. This project provides a question-answering interface that retrieves relevant information from documentation and generates answers grounded in the retrieved content.

The system combines:

* Semantic vector search
* BM25 keyword search
* Reciprocal Rank Fusion (RRF)
* Cross-encoder reranking
* Grounded LLM generation
* FastAPI backend
* React frontend
* Source/page/chunk references

The goal of the project was to build a practical RAG application rather than a simple chatbot or tutorial implementation.

## Architecture

```text
                    PDF Documentation
                           │
                           ▼
                    PDF Document Loader
                           │
                           ▼
                       Chunking
                           │
                           ▼
                      Embeddings
                           │
                           ▼
                    Qdrant Vector Store
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
        Semantic Search              BM25 Search
              │                         │
              └────────────┬────────────┘
                           ▼
                    RRF Hybrid Retrieval
                           │
                           ▼
                  Cross-Encoder Reranking
                           │
                           ▼
                       Top 5 Chunks
                           │
                           ▼
                    Grounded Prompt
                           │
                           ▼
                     Qwen2.5:7b
                           │
                           ▼
                     FastAPI API
                           │
                           ▼
                    React Frontend
```

## RAG Pipeline

### 1. Document Loading

The Pexip Infinity Product User Guide is loaded using `PyPDFLoader`.

### 2. Chunking

The document is split using `RecursiveCharacterTextSplitter` with:

* Chunk size: `800`
* Chunk overlap: `100`

Each chunk is assigned metadata including its source, page number, and chunk ID.

### 3. Semantic Retrieval

The project uses:

`sentence-transformers/all-MiniLM-L6-v2`

to generate embeddings and retrieve semantically relevant chunks.

### 4. BM25 Retrieval

BM25 provides keyword-based retrieval, which helps when questions contain specific technical terms, names, or phrases that semantic search may not rank highly enough.

### 5. Hybrid Retrieval

Semantic and BM25 results are combined using **Reciprocal Rank Fusion (RRF)**.

The retrieval stage initially produces a larger candidate pool before reranking.

### 6. Cross-Encoder Reranking

The retrieved candidates are reranked using:

`cross-encoder/ms-marco-MiniLM-L-6-v2`

The highest-ranked five chunks are passed to the generation step.

### 7. Grounded Generation

The final answer is generated using the local:

`Qwen2.5:7b`

model through Ollama.

The prompt instructs the model to:

* Use only the provided documentation
* Avoid unsupported claims
* Say that the information is not available when the documentation does not provide an answer
* Include supporting source information

## Features

* Enterprise-document question answering
* Hybrid semantic + keyword retrieval
* Reciprocal Rank Fusion
* Cross-encoder reranking
* Grounded responses
* Out-of-document fallback behavior
* Source and page references
* REST API using FastAPI
* React-based web interface
* Local LLM inference with Ollama

## Tech Stack

| Component         | Technology                         |
| ----------------- | ---------------------------------- |
| Language          | Python                             |
| RAG Framework     | LangChain                          |
| Document Loading  | PyPDFLoader                        |
| Embeddings        | Hugging Face Sentence Transformers |
| Vector Store      | Qdrant                             |
| Keyword Retrieval | BM25                               |
| Hybrid Retrieval  | Reciprocal Rank Fusion             |
| Reranker          | Cross-Encoder                      |
| LLM               | Qwen2.5:7b                         |
| LLM Runtime       | Ollama                             |
| Backend           | FastAPI                            |
| Frontend          | React                              |
| Frontend Tooling  | Vite                               |

## Project Structure

```text
enterprise-knowledge-platform/
│
├── backend/
│   ├── __init__.py
│   └── main.py
│
├── rag/
│   ├── __init__.py
│   ├── pipeline.py
│   └── pipeline.ipynb
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── index.html
│
├── data/
│   └── Product_User_Guide.pdf
│
├── README.md
└── .gitignore
```

## Running Locally

### Prerequisites

Make sure the following are installed:

* Python 3.10+
* Node.js
* Ollama
* Qwen2.5:7b model

Pull the model with:

```bash
ollama pull qwen2.5:7b
```

### Start the Backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite development URL shown in the terminal, normally:

```text
http://localhost:5173
```

## Example Questions

The application can answer questions such as:

* What is a Management Node in Pexip Infinity?
* What is the purpose of a Conferencing Node?
* What authentication methods are supported by Pexip Infinity?
* What happens when a Conferencing Node is taken out of service?
* How can conference diagnostics be accessed or used?
* What functions can administrators perform from the Management Node?
* What are the four possible risk response options described in the documentation?

The system also includes a grounded fallback for questions that cannot be answered from the provided documentation.

For example:

```text
What is the population of Pakistan?
```

The system should respond that the information is not available in the provided documentation rather than generating an unsupported answer.

## Retrieval Evaluation

The retrieval pipeline was evaluated using a question-answer evaluation dataset containing expected evidence.

Current retrieval measurements include:

| Metric    | Result |
| --------- | -----: |
| Recall@5  |  0.178 |
| MRR@5     |  0.350 |
| Recall@10 |  0.303 |
| MRR@10    |  0.379 |

These measurements were used to evaluate retrieval quality during development and guide improvements to the retrieval pipeline.

## Design Decisions

### Why Hybrid Retrieval?

Enterprise documentation often contains both conceptual language and exact technical terminology.

Semantic retrieval helps identify conceptually relevant information, while BM25 helps retrieve documents containing exact terms.

Combining both approaches provides a stronger retrieval baseline than relying on either method alone.

### Why Reranking?

Initial retrieval can return several relevant but imperfectly ordered chunks.

A cross-encoder reranker evaluates the relationship between the question and retrieved passages more directly and selects the most relevant evidence for generation.

### Why a Local LLM?

The project uses Ollama with Qwen2.5:7b to keep inference local during development and avoid requiring an external LLM API.

## Current Scope

The current version focuses on a single enterprise documentation source: the Pexip Infinity Product User Guide.

The project intentionally focuses on building and demonstrating a complete RAG workflow rather than implementing a large document-management platform.

## Future Improvements

Potential future improvements could include:

* Multi-document ingestion
* Persistent vector storage
* Authentication and user management
* Conversation history
* Cloud deployment
* Streaming responses
* More extensive automated evaluation
* Document management through the UI

These are outside the scope of the current implementation.

## License

This project is intended as a portfolio and learning project.

**That's the version I'd push.** It describes what you actually built, highlights the engineering decisions, and doesn't oversell the project as a full enterprise platform when it's currently a single-document RAG application.
