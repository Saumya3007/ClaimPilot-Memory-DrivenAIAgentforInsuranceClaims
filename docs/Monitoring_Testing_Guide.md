# Comprehensive Monitoring & Testing Guide: FastAPI, Postman, Prometheus, and Grafana

This document serves as the master guide explaining **where** our services live, the **theoretical purpose** of each tool, and deeply integrated **API testing examples** covering all REST operations (GET, POST, PUT/PATCH, and AI Generation) and how they manifest in your observability dashboards.

---

## Part 1: Where Are Services Located?

When you run `docker compose up -d`, these are the designated ports and URLs on your local machine (or the EC2 Public IP):

- **FastAPI Backend:** `http://localhost:8000` (The core server)
- **FastAPI Swagger API Docs:** `http://localhost:8000/docs`
- **Prometheus (Metrics Scraper):** `http://localhost:9090`
- **Grafana (Visualization Dashboard):** `http://localhost:3000`
- **Streamlit UI:** `http://localhost:8501`

---

## Part 2: The Theoretical Framework

To understand how testing works, you must understand the role of each tool in the chain.

### 1. FastAPI Theory
FastAPI is a modern, high-performance web framework for building APIs with Python. It automatically creates interactive documentation (Swagger UI), handles data validation, and manages asynchronous requests. 
**Role:** It receives the client request, runs business logic (like AI generation or DB writes), and emits text-based metrics on the `/metrics` endpoint.

### 2. Postman Theory
Postman is an industry-standard API client. Instead of writing code to send HTTP requests, Postman provides a graphical interface to easily construct GET, POST, PUT, PATCH, and DELETE requests, add headers, and inject JSON body data.
**Role:** It acts as our "simulated user" to forcefully generate traffic and test edge cases against our FastAPI backend.

### 3. Prometheus Theory
Prometheus is a time-series database and monitoring system. It operates on a "pull" model. Every 15 seconds, it reaches out to `http://api:8000/metrics`, takes a snapshot of how many requests happened, how long they took, and saves them.
**Role:** It is the storage engine and metric gatherer. It turns a chaotic stream of user requests into organized mathematical data (histograms, gauges, counters).

### 4. Grafana Theory & Dashboard Imports
Grafana is the visual layer. It doesn't collect data itself; it queries Prometheus and turns that raw mathematical data into beautiful charts and graphs.
**Role:** It provides the human-readable alerts and graphs. 
**Dashboard Import:** You do not need to build graphs completely from scratch. You can import community templates:
- Under Grafana, go to `Dashboards > Import`.
- Input a community ID designed for `prometheus-fastapi-instrumentator` (like ID **14694** or **18987**).
- Grafana automatically creates panels for Requests/Sec, Latency, and Error rates based on the imported rules.

---

## Part 3: The Full API Testing Suite (Postman)

By executing these tests in Postman, you are actively pushing data through FastAPI, which is captured by Prometheus and displayed in Grafana.

### Test 1: The GET Request (Health Check & Fetching Data)
**Purpose:** Test rapid, low-latency data retrieval.
- **Method:** `GET`
- **URL:** `http://localhost:8000/health`
- **Action:** Click "Send" repeatedly.
- **Expected FastAPI Response:** `200 OK`
- **Grafana Effect:** Immediate spike in **Requests per Second (RPS)** for the `/health` endpoint. Latency will show near 0ms because no database action is required.

### Test 2: The POST Request (Creating a Ticket)
**Purpose:** Test payload processing and database write latency.
- **Method:** `POST`
- **URL:** `http://localhost:8000/api/tickets`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
      "customer_email": "jane.doe@example.com",
      "customer_name": "Jane Doe",
      "subject": "Login Failure",
      "description": "I cannot log into my account.",
      "priority": "high",
      "auto_generate": false
  }
  ```
- **Expected FastAPI Response:** Returns a new ticket JSON structure.
- **Grafana Effect:** The **Total Requests** counter increments for the POST method on `/api/tickets`.

### Test 3: The PATCH / PUT Request (Updating a Draft)
**Purpose:** Test updating an existing record. (Our app uses `PATCH` for draft updates).
- **Method:** `PATCH`
- **URL:** `http://localhost:8000/api/drafts/1`
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**
  ```json
  {
      "content": "Updated AI Draft text",
      "status": "accepted"
  }
  ```
- **Expected FastAPI Response:** The updated draft model.
- **Grafana Effect:** Grafana categorizes requests by HTTP verb. You will now see `PATCH` or `PUT` appear as a distinct slice in your "Traffic by Method" pie chart.

### Test 4: The DELETE Configuration (Theoretical)
**Purpose:** Test record deletion. *(Note: This project's current scope has not implemented a DELETE ticket endpoint, but this is how you would test it if added).*
- **Method:** `DELETE`
- **URL:** `http://localhost:8000/api/tickets/1`
- **Expected FastAPI Response:** `204 No Content` or `200 OK`.
- **Grafana Effect:** A successful deletion registers on Grafana, and an attempt to GET that deleted ticket immediately after will trigger a `404 Not Found` spike in the Grafana "Client Errors" panel.

### Test 5: The "AI Test" (Long-Running Generation Request)
**Purpose:** Test how the system handles heavy GPU/LLM bottlenecks and slow responses.
- **Method:** `POST`
- **URL:** `http://localhost:8000/api/tickets/1/generate-draft`
- **Expected FastAPI Response:** It takes multiple seconds (2-10s) to return the generated response from the LLM.
- **Grafana Effect:** This is the most crucial test for Prometheus! In Grafana, the **Response Time 95th Percentile** and **99th Percentile** widgets will skyrocket. This allows you to visually prove to stakeholders exactly how long AI computing is blocking user requests compared to normal database calls.

---

## Part 4: What Exactly Are You Seeing in Grafana?

When you successfully run the Postman tests above, you are validating these specific Grafana features:

1. **Throughput (Traffic Volume):** As you click "Send" in Postman, the RPS graph rises and falls resembling a heartbeat. 
2. **Endpoint Stratification:** Grafana doesn't just clump all traffic together. You will see specifically that your `/health` requests are colored blue, `/api/tickets` colored green, etc., proving Prometheus is indexing path data.
3. **Status Code Segmentation:** If you test fetching a ticket that doesn't exist (`GET /api/tickets/99999`), Postman shows a 404. In Grafana, the **4xx Errors Rate** panel instantly turns red, alerting you of failing queries.
4. **Latency Histograms / Buckets:** The "AI Test" takes 4 seconds, the Health Check takes 5ms. 
---

## Part 5: Feedback Loop & AI Model Evaluation

We evaluate the "Human-Approved -> Memory" loop and specific model performance using automated metrics.

### 1. Specific Model Roles
To ensure high precision, we use dedicated models for targeted tasks instead of relying solely on a general-purpose LLM:
- **RoBERTa (`twitter-roberta-base-sentiment`):** Analyzes the claimant's sentiment (Positive, Neutral, Negative). High negative sentiment automatically scales the internal `urgency_score`.
- **BART/BERT (`bart-large-mnli`):** Performs zero-shot classification to categorize claims into folders (e.g., *Auto Accident, Theft, Natural Disaster*). This enables precise triage.
- **Google GenAI Embeddings:** Power the long-term semantic memory (LangMem) to store and retrieve historical resolutions.

### 2. Evaluation Metrics (The Feedback Loop)
Every time an adjuster approves or edits a draft, the `EvaluationMetricsService` logs the delta:

| Metric | Meaning | Target |
| :--- | :--- | :--- |
| **Human Fidelity** | Similarity between the generated draft and the final approved version. | > 0.85 |
| **Acceptance Rate** | % of AI drafts that were accepted without being discarded. | > 90% |
| **Memory Hit Ratio** | How many relevant historical "memories" were found and used per claim. | > 1.5 |
| **Fidelity Correlation** | Does frequent use of memory lead to higher fidelity (less editing)? | Positive Trend |

### 3. Real-World Data Integration
We have integrated a real-world automobile insurance dataset (`data/real_world_claims.csv`) containing 1,000 anonymized claims. This data is used to:
- Stress test the categorization models.
- Validate fraud indicators across diverse scenarios.
- Seed the knowledge base with realistic policy edge-cases.

### 4. Running the Tests
- **Unit Tests:** `uv run pytest tests/test_langmem_detailed.py`
- **Evaluation Log:** Check `data/evaluation_metrics.json` for live performance data.
- **Model Check:** Run `uv run python -c "from customer_support_agent.services.model_service import get_model_service; print(get_model_service().analyze_claim_text('Your text here'))"`
