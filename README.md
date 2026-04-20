# ClaimPilot: Memory-Driven AI Agent for Insurance Claims

**ClaimPilot** is an advanced AI-powered insurance claims copilot designed to assist adjusters in processing First Notice of Loss (FNOL) claims. It leverages large language models (LLMs) via Groq, long-term memory through LangMem, and a Retrieval-Augmented Generation (RAG) system grounded in insurance policy documentation.

---

## 🏗️ Folder Structure & Microservices

The project is structured as a modular microservices-ready architecture:

```text
ClaimPilot/
├── app.py                      # Streamlit Frontend (Adjuster Workbench)
├── main.py                     # FastAPI Entry Point
├── Dockerfile                  # Multi-service build configuration
├── docker-compose.yml          # Orchestration: API, Dashboard, Prometheus, Grafana
├── customer_support_agent/
│   ├── api/                    # API Layer (Routers & Factories)
│   │   └── routers/            # Tickets, Drafts, Evaluation, Knowledge endpoints
│   ├── services/               # Logic Layer
│   │   ├── model_service.py    # RoBERTa & BART model implementations
│   │   ├── copilot_service.py  # LLM Orchestration & RAG retrieval
│   │   └── evaluation_service.py # Jaccard Similarity / Fidelity logic
│   ├── integrations/           # Third-party adapters
│   │   ├── memory/             # LangMem / LangGraph Store
│   │   ├── rag/                # ChromaDB vector store
│   │   └── tools/              # Claim lookup & SLA tools
│   └── repositories/           # Database Persistence
├── data/                       # Local DB, Real-world CSV, & Metrics
├── docs/                       # Project Documentation & Images
└── tests/                      # Pytest Suite
```

---

## 🖼️ Architecture & Interface

### Technical Architecture
![Architecture](docs/images/architecture.png)

### Adjuster Workbench (Streamlit)
![Dashboard](docs/images/dashboard.png)

---

## 🚀 Core Enhancements

### 1. Real-World Data Integration
We transitioned from synthetic placeholders to a **real-world automobile insurance dataset**.
*   **Source:** Inspired by public insurance datasets (Kaggle), adapted and expanded.
*   **Utility:** 1,000+ anonymized records including `incident_severity`, `total_claim_amount`, and `fraud_reported`.
*   **Location:** `data/real_world_claims.csv`

### 2. Specialized NLP Models (RoBERTa & BART)
*   **RoBERTa (Sentiment Analysis):** Detects claimant frustration/urgency to influence priority.
*   **BART (Zero-Shot Classification):** Automatically categorizes claims (e.g., *Auto Accident, Theft*) without training.
*   **Implementation:** Found in `customer_support_agent/services/model_service.py`.

### 3. Human Fidelity Evaluation
Measures AI reliability by comparing AI drafts with adjuster-approved final versions.
*   **Formula:** Jaccard Similarity index (Intersection over Union).
*   **Purpose:** Quantifies "human-in-the-loop" alignment.

---

## 📡 Postman API Examples

### 1. Create Ticket (POST)
**URL:** `http://localhost:8000/api/tickets`
**Body:**
```json
{
    "customer_email": "john.doe@example.com",
    "subject": "Accident in Parking Lot",
    "description": "I hit a pole while reversing. I am very frustrated!",
    "auto_generate": true
}
```

### 2. Get AI Analysis (GET)
**URL:** `http://localhost:8000/api/drafts/{ticket_id}`
**Response:**
```json
{
    "content": "Proposed coverage recommendation...",
    "ai_analysis": {
        "sentiment": "negative",
        "category": "auto accident"
    }
}
```

### 3. Approve/Edit Draft (PATCH)
**URL:** `http://localhost:8000/api/drafts/{draft_id}`
**Body:**
```json
{
    "content": "Final adjuster-edited content here...",
    "status": "accepted"
}
```

### 4. Fetch Fidelity Stats (GET)
**URL:** `http://localhost:8000/api/evaluation/summary`

---

## 📋 Installation & Setup
```bash
docker compose up --build
```
*   **API:** `8000` | **Dashboard:** `8001` | **Grafana:** `3000`
