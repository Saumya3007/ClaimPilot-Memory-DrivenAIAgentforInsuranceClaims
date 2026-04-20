# ClaimPilot: Memory-Driven AI Agent for Insurance Claims Settlement

**ClaimPilot** is a state-of-the-art, memory-driven AI Copilot designed for insurance claims adjusters. It streamlines the lifecycle of a claim—from First Notice of Loss (FNOL) to final recommendation—by combining Large Language Models (LLMs), specialized Transformer models (RoBERTa, BART), Long-term Memory (LangMem), and Retrieval-Augmented Generation (RAG).

---

## 🏗️ System Design & Microservices Architecture

ClaimPilot is built using a **Modular Microservices Architecture** to ensure high availability, observability, and scalability. The system is containerized via Docker and orchestrated through Docker Compose.

### 1. High-Level Pipeline Flow
1.  **FNOL Intake:** The Adjuster enters incident data (Date, Location, Loss Type, Description) into the **Streamlit Workbench**.
2.  **Specialized NLP Analysis:** The **FastAPI Backend** intercepts the data and runs two specialized inferences:
    
![Architecture Visualization](docs/images/architecture.png)

    *   **Sentiment Engine (RoBERTa):** Detects claimant distress labels (Negative, Neutral, Positive).
    *   **Classification Engine (BART):** Performs zero-shot categorization into industry-standard claim types.
3.  **Knowledge Retrieval (RAG):** The system queries a **ChromaDB Vector Store** containing policy documents and insurance regulations found in `knowledge_base/`.
4.  **Memory Synthesis (LangMem):** The system searches the **LangGraph InMemoryStore** for historical outcomes related to that specific Customer or Company.
5.  **LLM Reasoning:** A **Groq-powered Llama-3 Agent** synthesizes the Analysis + RAG + Memory + Tool outputs into a structured coverage recommendation.
6.  **Human-in-the-Loop:** The Adjuster reviews, edits, and approves the draft. 
7.  **Evaluation & Learning:** On approval, the **Evaluation Service** calculates the **Human Fidelity Score** and persists the final outcome back into the Long-term Memory store.

### 2. Microservices Components
*   **FastAPI Backend (Port 8000):** The orchestration hub and API provider.
*   **Streamlit UI (Port 8501):** The interactive adjuster workbench.
*   **Prometheus (Port 9090):** The metrics collection engine.
*   **Grafana (Port 3000):** The visualization dashboard for performance and fidelity.

![Adjuster Dashboard Workbench](docs/images/dashboard.png)

---

## 🚦 Quick Start: Verification & Service Health

### 1. How to Verify Health & Services
Immediately after deployment (locally or on EC2), you can verify the status of the entire microservices stack:
*   **FastAPI Health (GET):** `http://<IP>:8000/health`
    *   *Role:* Returns `{"status":"ok"}`. This is used by the CI/CD pipeline to ensure the container is ready.
*   **Swagger API Documentation (GET):** `http://<IP>:8000/docs`
    *   *Role:* Provides interactive OpenAPI documentation. You can test every GET, POST, and PATCH request here directly.
*   **Prometheus Console (GET):** `http://<IP>:9090`
    *   *Role:* The monitoring engine. Click on `Status -> Targets` to ensure the API is "Up" and being scraped.
*   **Grafana Dashboard (GET):** `http://<IP>:3000`
    *   *Role:* The visualization layer. Open the "Insurance Adjuster Performance" dashboard to see Human Fidelity trends.
*   **Streamlit UI (GET):** `http://<IP>:8501`
    *   *Role:* The Adjuster Workbench where real insurance operations take place.

### 2. Detailed Postman Testing Examples

Execute these in order to simulate a full claim lifecycle and see the metrics in Grafana:

#### A. Create a Ticket (POST)
**Endpoint:** `POST http://localhost:8000/api/tickets`
```json
{
    "customer_email": "real_driver@example.com",
    "customer_name": "John Real",
    "subject": "Serious Collision in Parking Lot",
    "description": "I crashed my car while reversing. I AM FURIOUS because I called and no one helped. Totaled my car.",
    "priority": "high",
    "auto_generate": true
}
```
*   *Observation:* Triggers RoBERTa (Sentiment) and BART (Categorization).

#### B. Fetch AI Draft (GET)
**Endpoint:** `GET http://localhost:8000/api/drafts/{id}`
*   *Observation:* Returns the AI-generated coverage recommendation with sentiment metadata.

#### C. Human Approval Loop (PATCH)
**Endpoint:** `PATCH http://localhost:8000/api/drafts/{id}`
```json
{
    "content": "Final adjuster decision: Approved per policy section 4B.",
    "status": "accepted"
}
```
*   *Observation:* Triggers the Jaccard Similarity calculation for the **Human Fidelity Score**.

#### D. Fetch Fidelity Summary (GET)
**Endpoint:** `GET http://localhost:8000/api/evaluation/summary`

### 3. How to Verify the Human Fidelity Score (Step-by-Step)
The **Human Fidelity Score** is the key indicator of AI accuracy. Here is how to trace it:
1.  **Generate a Draft:** Submit a claim and let the AI generate a text recommendation.
2.  **Adjuster Intervention:** Open the `PATCH /api/drafts/{id}` endpoint in Swagger or Postman.
3.  **Perform an Edit:** Change the content of the draft (e.g., add or remove words) and set `status: "accepted"`.
4.  **Automatic Calculation:** The system instantly runs the **Jaccard Similarity** algorithm in the background.
5.  **View the Result (API):** Call `GET http://<IP>:8000/api/evaluation/summary`. You will see the `average_fidelity` value updated.
6.  **Visualize (Grafana):** Navigate to `http://<IP>:3000`. The "Human Fidelity Trend" line chart will plot the new score, proving the AI is learning from your edits.

---

## 🧠 AI Intelligence Layer (The "Nitty-Gritty")

We avoid the "Black Box" LLM approach by using a multi-model pipeline:

### 1. Sentiment-Based Urgency Engine (RoBERTa)
*   **Model ID:** `cardiffnlp/twitter-roberta-base-sentiment`
*   **Logical Role:** Insurance claims are often emotional. By using RoBERTa, the system identifies if a claimant is "Furious" or "Distressed" in their FNOL description. 
*   **Outcome:** High negative sentiment automatically scales the internal `urgency_score`, pushing the ticket to the top of the adjuster's queue.

### 2. Zero-Shot Classification Engine (BART)
*   **Model ID:** `facebook/bart-large-mnli`
*   **Logical Role:** Claim categorization is critical for triage. We use BART to perform zero-shot classification, meaning it can sort claims into categories (Collision, Theft, Vandalism, Medical) without needing a single row of labeled training data.

### 3. Agentic Reasoning (LangChain + Groq)
*   **Model:** Llama-3-70b/8b via Groq Cloud.
*   **Tools:**
    *   `lookup_customer_plan`: Checks if the customer has a "Premium" or "Basic" SLA.
    *   `lookup_open_ticket_load`: Checks current team bandwidth to manage adjuster expectations.

### 4. Long-Term Semantic Memory (LangMem)
*   **Implementation:** Leveraging LangGraph's `InMemoryStore`.
*   **Strategy:** We store "Resolutions" across two scopes:
    *   **User Scope:** Memories specific to the individual claimant.
    *   **Company Scope:** Memories shared across an entire organization (e.g., if a trucking company has a pattern of similar accidents).

---

## 📂 Detailed Folder Structure
```text
ClaimPilot/
├── app.py                      # Streamlit Adjuster Workbench (The Frontend)
├── main.py                     # FastAPI Entry Point (The Bootstrapper)
├── Dockerfile                  # Multi-service build (Optimized for CPU-Torch)
├── docker-compose.yml          # Full stack orchestration (API, UI, Mon, Grafana)
├── pyproject.toml              # Unified dependency management (uv-based)
├── customer_support_agent/     # THE CORE APPLICATION
│   ├── api/                    # API LAYER
│   │   ├── app_factory.py      # FastAPI config, Middleware, and Instrumentation
│   │   └── routers/            # ENDPOINTS
│   │       ├── tickets.py      # FNOL Registration logic
│   │       ├── drafts.py       # AI recommendation lifecycle
│   │       ├── evaluation.py   # Metrics and Fidelity reporting
│   │       ├── knowledge.py    # RAG ingestion endpoints
│   │       └── memory.py       # Direct memory probe endpoints
│   ├── services/               # LOGIC LAYER
│   │   ├── copilot_service.py  # Orchestrates RAG + Memory + LLM + Tools
│   │   ├── model_service.py    # RoBERTa and BART initialization and inference
│   │   ├── draft_service.py    # Persists and manages recommendation states
│   │   └── evaluation_service.py # The Jaccard Similarity engine
│   ├── integrations/           # EXTERNAL CONNECTORS
│   │   ├── memory/             # LangMem / LangGraph interface
│   │   ├── rag/                # ChromaDB Vector Store wrapper
│   │   └── tools/              # Postman/SLA lookup tools
│   └── repositories/           # PERSISTENCE
│       └── sqlite/             # Relational data (Tickets, Customers, Drafts)
├── data/                       # PERSISTENT STORAGE
│   ├── support.db              # The SQLite Relational Database
│   ├── real_world_claims.csv   # Dataset (1,000 anonymized records)
│   ├── evaluation_metrics.json # Live Performance log
│   └── hf_cache/               # Docker Volume for AI Model Weights (Optimized)
├── prometheus/                 # PROMETHEUS CONFIGURATION
│   └── prometheus.yml          # Scrape targets and intervals
├── grafana/                    # GRAFANA CONFIGURATION
│   └── provisioning/           # Automated datasource and dashboard setup
├── .github/workflows/          # CI/CD (GitHub Actions)
│   └── deploy-ec2.yml          # Strategic AWS Deployment pipeline
└── docs/                       # PROJECT DOCUMENTATION
    └── images/                 # Architecture and UI Screenshots
```

---

## 🧪 Evaluation Metrics & Real-World Data

### 1. Human Fidelity Score
A unique metric we developed to measure AI effectiveness. It is calculated using the **Jaccard Similarity Index** (word-level Intersection over Union) between the **AI's First Draft** $(D_{ai})$ and the **Adjuster's Final Approved Content** $(D_{human})$.
$$F = \frac{|W_{ai} \cap W_{human}|}{|W_{ai} \cup W_{human}|}$$
*   **Why Jaccard?** It rewards the AI for using correct domain terminology while penalizing unnecessary fluff or errors that the human had to delete.

### 2. Real-World Data Integration
We integrated a **Real-World Automobile Insurance Dataset** (1,000 records). 
*   **Origin:** Adapted from public insurance datasets (Kaggle).
*   **Content:** Contains realistic data spanning `incident_severity`, `total_claim_amount`, `property_damage`, and `fraud_reported`.
*   **Purpose:** This allows us to test the system against high-entropy, realistic claim scenarios where the AI must detect patterns like "Fraud Probability" based on historical severity levels.

---

## 🚀 Deployment Strategy (GitHub Actions -> EC2)

Deployment is automated using a robust **CD Pipeline** optimized for 30GB Free Tier AWS EC2 instances.

### Step-by-Step GitHub Actions Pipeline:
1.  **Checkout:** Scans the repository code into the GitHub Runner.
2.  **Environment Setup:** Installs Python 3.11 and the `uv` package manager.
3.  **Local Testing:** Runs `uv run pytest` to ensure no logic is broken.
4.  **Packaging:** Compresses the whole project into a `release.tar.gz`.
5.  **SSH Connect:** Connects to the **EC2 Public IP** using the `EC2_SSH_KEY` secret.
6.  **Upload:** Transfers the code via **SCP**.
7.  **EC2 Remote Execution (The "Nitty-Gritty"):**
    *   **Swap File Creation:** On a 4GB RAM instance, loading AI models is risky. The script automatically creates a **4GB Swap file** on the SSD to act as virtual RAM.
    *   **Docker Cleanup:** Runs `docker system prune -af` to delete old build layers and dangling images, ensuring we stay well under the 30GB disk limit.
    *   **Orchestration:** Executes `docker compose up -d --build --force-recreate` to launch the new version.
8.  **Health Check:** Pings `http://<EC2_IP>:8000/health`. Only if it returns a `200 OK` is the deployment marked "Success".

---

## 📊 Monitoring & Observability

ClaimPilot is fully instrumented for deep production monitoring:

*   **Swagger UI (`8000/docs`):** The primary testing interface. Developers can test every POST/GET endpoint directly from the browser.
*   **Prometheus (`9090`):** Automatically "scrapes" metrics from the FastAPI backend every 15 seconds. It tracks `api_requests_total`, `api_request_duration_seconds`, and custom AI inference times.
*   **Grafana (`3000`):** Visualizes performance. 
    *   **Key Dashboard:** "Human Fidelity Trends". It allows supervisors to see if the AI is becoming more or less accurate over time as more memories are added to the system.

---

## 📡 API Testing (Postman Examples)

### 1. Register FNOL & Analyze (POST)
**Endpoint:** `POST /api/tickets`
```json
{
    "customer_email": "real_driver@example.com",
    "customer_name": "John Real",
    "subject": "Serious Accident on Highway 5",
    "description": "I crashed my car and I AM FURIOUS! Nobody is answering!",
    "priority": "high",
    "auto_generate": true
}
```
*   **Internal Effect:** FastAPI calls RoBERTa (detects "Negative") and BART (detects "Auto Accident"). The Groq LLM then retrieves policy data from ChromaDB to create the first draft.

### 2. Approved Resolution & Memory (PATCH)
**Endpoint:** `PATCH /api/drafts/{id}`
```json
{
    "content": "Official coverage decision: Approved based on Policy Clause 4B.",
    "status": "accepted"
}
```
*   **Internal Effect:** This triggers the **Human Fidelity calculation** and permanently saves the "Resolution" into the customer's **LangMem store**.

---

## 🛠️ Setup & Local Usage
1.  **Environment:** Create a `.env` file with your `GROQ_API_KEY`.
2.  **Docker:** Run `docker compose up --build`.
3.  **Ingest KB:** Open the Streamlit sidebar (`localhost:8501`) and click "Ingest Policy & Regulation KB".
4.  **Register Claim:** Start entering data from the `real_world_claims.csv` to see the AI in action!
