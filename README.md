# RAG Research Engine 🤖
> **Enterprise-Grade RAG Infrastructure for Autonomous Document Intelligence.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL%2015-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/orchestration-Docker-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**RAG Research Engine** is a high-performance **Retrieval-Augmented Generation (RAG)** platform engineered to operate as a **Senior AI Research Lead**. It orchestrates multi-source document ingestion, semantic vectorization, and deterministic synthesis to eliminate AI hallucinations while providing production-level scalability for technical research.

---

## 🚀 Key Engineering Highlights

* **🛡️ Deterministic Guardrails**: Implements a strict "Closed-Domain" policy. The system is architected to admit ignorance if the provided context lacks the answer, ensuring 100% factual grounding and preventing hallucinations.
* **⏳ Time-Weighted Semantic Scoring**: Beyond standard cosine similarity, the engine applies a custom heuristic to prioritize fresh data. Mathematical relevance is recalculated to favor recently uploaded documents over legacy records.
* **🌍 Cross-Lingual Research Intelligence**: Powered by **Cohere Multilingual**, the engine detects query intent in any language and performs real-time semantic retrieval across diverse document sets, responding in the user's native tongue.
* **⚡ Asynchronous Ingestion Daemon**: A dedicated background worker manages heavy vectorization and embedding tasks using a non-blocking polling architecture, ensuring the REST API and UI remain highly responsive.
* **📉 Rank-Based Truncation (Token Safety)**: Mitigates "Lost in the Middle" syndromes by enforcing a strict 4,000-token context margin, optimized for **Groq's Llama 3.3 70B**'s high-fidelity attention mechanism.
* **🖥️ Premium Desktop Client**: A hardware-accelerated **CustomTkinter** GUI featuring real-time status badges (`Pending`, `Processing`, `Ready`) and interactive context cards for full data traceability.

---

## 🛠️ Technology Stack

| Component | Technology | Implementation Detail |
| :--- | :--- | :--- |
| **Logic Layer** | **Python 3.11+** | Modular, type-hinted architecture. |
| **Backend API** | **FastAPI** | High-concurrency Uvicorn-based service. |
| **Data Store** | **PostgreSQL 15** | Relational 3NF schema for metadata and audit logs. |
| **ORM** | **SQLAlchemy 2.0** | Optimized query execution and session management. |
| **Vector AI** | **Cohere API** | `embed-multilingual-v3.0` for global semantics. |
| **Reasoning Engine** | **Groq API** | `llama-3.3-70b-versatile` for ultra-fast, grounded synthesis. |
| **UI/UX** | **CustomTkinter** | Modern dark-mode interface with async state polling. |

### 🚄 Why Groq?
The engine leverages **Groq's LPU (Language Processing Unit)** infrastructure for unprecedented inference speed:
* ⚡ **Sub-second response times**: Queries typically complete in 1-3 seconds
* 🆓 **100% Free Tier**: Generous limits (30 RPM, 14,400 RPD) - perfect for production workloads
* 🧠 **Llama 3.3 70B**: State-of-the-art reasoning capabilities with 70 billion parameters
* 🌐 **Cloud-native**: No local compute required, ideal for enterprise deployment

---

## 📁 System Blueprint

The RAG Research Engine operates under a decoupled methodology, separating the ingestion daemon from the query pipeline to ensure system resilience and scalability.

```mermaid
flowchart LR
	%% Modern, clean visual language with separated subgraphs.
	classDef source fill:#e8f5e9,stroke:#2e7d32,stroke-width:1.5px,color:#1b4332;
	classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:1.5px,color:#0d47a1;
	classDef store fill:#fff8e1,stroke:#ef6c00,stroke-width:1.5px,color:#6d4c41;
	classDef output fill:#f3e5f5,stroke:#6a1b9a,stroke-width:1.5px,color:#4a148c;

	subgraph ING[Ingestion Pipeline]
		direction LR
		U[Unstructured Data\nPDF / Web] --> S[Recursive Character\nText Splitting]
		S --> E[Vector Embeddings]
		E --> P[(PostgreSQL + pgvector\nEmbeddings Storage)]
	end

	subgraph RAG[RAG Query Loop]
		direction LR
		Q[User Query] --> M[Semantic Search\nSimilarity]
		M --> C[Context Injection]
		C --> G[Gemini 1.5 Flash\nReasoning]
		G --> A[Verified Answer\nwith Citations]
	end

	P -.-> M

	class U,Q source;
	class S,E,M,C,G process;
	class P store;
	class A output;
```

---

## 🧪 Mathematical Extraction Framework

The engine employs a multi-stage retrieval heuristic to ensure precision in research-heavy environments.

### 1. Vector Similarity
Queries are vectorized and cross-referenced against the PostgreSQL store using **Cosine Similarity**.

### 2. Heuristic Re-weighting
The final relevance score incorporates a time-decay factor to prioritize updated information:
```text
Final Score = (0.8 * Similarity) + (0.2 * Recency Factor)
```

### 3. Threshold & Truncation
* **Drop-off Threshold**: Any fragment with a score below `0.70` is discarded to eliminate noise.
* **Token Margin**: Context injection stops at `4,000 tokens` to maintain the LLM's focus and precision.

---

## ⚙️ Deployment & Setup

### 1. Prerequisites
* **Docker & Docker Compose**
* API Keys: **Groq** (free at https://console.groq.com/keys) and **Cohere** (free at https://cohere.com).

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/ragdb

GROQ_API_KEY=your_groq_key_here
COHERE_API_KEY=your_cohere_key_here

UPLOADS_DIR=uploads
```

**Obtaining API Keys:**
* **Groq**: Visit https://console.groq.com/keys → Create Account → Generate API Key (Free)
* **Cohere**: Visit https://dashboard.cohere.com/api-keys → Sign Up → Create API Key (Free)

### 3. Containerized Launch
```bash
docker compose up --build
```
* **API Listener**: `http://localhost:8000`
* **Interactive Docs**: `http://localhost:8000/docs`

### 4. Launching the GUI
```bash
python gui.py
```

---

## 📄 Credits & Academic Purpose

Developed as an elite implementation of industrial AI research architectures.
* **Developer**: Keylor Pineda (Systems Engineering Student, National University of Costa Rica - UNA)
* **Focus**: Scalable RAG, Asynchronous Python, and Document Intelligence.
