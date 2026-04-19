# ClaimPilot Project Deep Dive: Architecture & Services

This document explains the full codebase structure, the theory behind each layer, and how to verify them.

---

## 1. Project Folder Structure

```text
.
├── main.py                 # Entry point for the FastAPI Backend
├── app.py                  # Entry point for the Streamlit Frontend (Workbench)
├── Dockerfile              # Instructions for building the service image
├── docker-compose.yml      # Orchestrates Microservices (API, UI, Prometheus, Grafana)
├── pyproject.toml          # Dependency management (uv)
├── data/                   # Persistent storage (SQLite, CSVs, Vector DBs)
├── prometheus/             # Monitoring configuration
├── grafana/                # Dashboard visualizations
├── customer_support_agent/ # Core Package (The Source Code)
│   ├── api/                # FastAPI Routers & Dependencies
│   ├── services/           # The "Brains" (Business Logic)
│   ├── repositories/       # Data Access Layer (SQLite operations)
│   ├── integrations/       # Connectivity (LangMem, ChromaDB, Tools)
│   ├── schemas/            # Pydantic models (Data standards)
│   └── core/               # App configuration & settings
└── tests/                  # Verification & Quality Assurance
```

---

## 2. Service Layer: The "Brains" (`/services`)

| Service | Responsibility | Theory |
| :--- | :--- | :--- |
| **Copilot Service** | Orchestration | The **Main Orchestrator**. It gathers data from RAG, Memory, and Models to build the final response. |
| **Model Service** | Specialized NLP | Uses **RoBERTa** (Sentiment) and **BART** (Categorization). Smaller models are faster and more accurate for specific tasks than a generic LLM. |
| **Evaluation Service** | Feedback Loop | Measures **Human Fidelity**. It calculates Levenshtein distance between AI drafts and human edits. |
| **Knowledge Service** | RAG Management | Handles the ingestion of PDFs/Markdown into **ChromaDB**. |
| **Draft Service** | Lifecycle | Manages the creation, status, and storage of coverage recommendations. |

---

## 3. Infrastructure Theory: Memory & RAG

### A. Long-Term Memory (LangMem + SQLite)
Unlike standard chatbots, our agent has **Episodic Memory**.
1.  **Short-Term:** LangGraph Checkpoints (remembers the current conversation).
2.  **Long-Term:** LangMem (remembers previous successful resolutions for that specific customer).
3.  **Relational:** SQLite (stores the "hard data" like ticket IDs and policy numbers).

### B. Knowledge Retrieval (ChromaDB)
This is **RAG (Retrieval-Augmented Generation)**.
*   Instead of training the AI on company policies, we store policies in a **Vector Database**.
*   When a new claim comes in, the system "searches" for the relevant policy paragraph and feeds it to the AI as "Context."

---

## 4. Testing & Verification Guide

### A. Unit Testing (Backend Logic)
Run this to verify the Memory and Copilot logic:
```powershell
uv run pytest tests/test_langmem_detailed.py
```

### B. Monitoring Verification (The "N/A" Fix)
*   **FastAPI Metrics:** `http://localhost:8000/metrics`
*   **Prometheus Health:** `http://localhost:9090/targets`
*   **Fidelity Data:** `http://localhost:8000/api/evaluation/summary`

### C. Manual Integration Test (Postman)
To verify the **Model Service** (RoBERTa/BART) is working inside the API:
```json
// POST http://localhost:8000/api/tickets
{
    "customer_email": "test@viva.com",
    "customer_name": "Student",
    "subject": "Accident",
    "description": "I crashed my car and I am ANGRY!",
    "priority": "high",
    "auto_generate": true
}
```
Wait 10 seconds and check `GET /api/drafts/{id}`. You should see:
*   `ai_analysis.sentiment`: "negative"
*   `ai_analysis.category`: "auto accident"

---

## 5. Deployment Layer (AWS/Docker)
The code is designed for **Cloud Scalability**:
*   **Stateless logic:** The API can be restarted without losing data because everything is in the `data/` volume.
*   **Containerization:** The `Dockerfile` uses **`uv`** for light, fast Python environments, reducing EC2 memory usage.
