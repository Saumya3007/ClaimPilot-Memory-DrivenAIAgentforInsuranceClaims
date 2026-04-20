# Grafana and Prometheus Deployment Guide on EC2

This guide outlines the step-by-step process used to add Prometheus and Grafana for monitoring the FastAPI backend, and how to deploy this stack onto an AWS EC2 instance. The entire process was executed from the new `test` branch to prevent impacting `main`.

## 1. Branch Strategy
To safely test the deployment and integration of Grafana and Prometheus, we began on a new branch.

```bash
# Executed on local machine
git checkout -b test
```

## 2. CI/CD Updates
We updated `.github/workflows/deploy-ec2.yml` so that it will be triggered when code is pushed to both `main` and `test` branches.

```yaml
# In .github/workflows/deploy-ec2.yml
on:
  workflow_dispatch:
  push:
    branches:
      - main
      - test
```

## 3. Dependency Updates
We added `prometheus-fastapi-instrumentator` to track HTTP requests and hardware metrics.

```toml
# In pyproject.toml
dependencies = [
    # ... other dependencies
    "prometheus-fastapi-instrumentator"
]
```

We applied it locally via:
```bash
uv sync --dev
```

## 4. FastAPI Instrumentation
In `customer_support_agent/api/app_factory.py`, we exposed the `/metrics` endpoint for Prometheus.

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title=resolved_settings.app_name, lifespan=lifespan)

# Instrument FastAPI for Prometheus scraping at /metrics
Instrumentator().instrument(app).expose(app)
```

## 5. Docker Compose Updates
We added two new services in `docker-compose.yml`:
- **Prometheus** (Port 9090)
- **Grafana** (Port 3000)

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: support-copilot-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
    networks:
      - default

  grafana:
    image: grafana/grafana:latest
    container_name: support-copilot-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - default
```

## 6. Monitoring Configurations
We created the YAML configurations to automatically map the stack topology.

**`prometheus/prometheus.yml`**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'support-copilot-api'
    static_configs:
      - targets: ['api:8000']
```

**`grafana/provisioning/datasources/prometheus.yml`**
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

---

## 7. Step-by-Step EC2 Deployment Walkthrough

To deploy this entire update to EC2, follow these instructions carefully.

### Step 7.1: Configure Security Groups
1. Go to your AWS EC2 Console.
2. Select your Instance -> **Security** -> **Security Groups**.
3. Edit the Inbound rules to allow:
   - **Port 8000** (FastAPI & Swagger UI)
   - **Port 8501** (Streamlit Interface)
   - **Port 3000** (Grafana Interface)
   - **Port 9090** (Prometheus Interface - Optional, mostly for debugging)
   - Setup source to `0.0.0.0/0` (Anywhere) for open access.

### Step 7.2: EC2 Preparation and Docker Installation
SSH into your instance:
```bash
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
```

If you don't already have Docker installed on the EC2, ensure the system is up-to-date and install it:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 curl

# Verify installation
docker --version
docker compose version

# Prevent using sudo with docker
sudo usermod -aG docker $USER
newgrp docker

# Create the working directory
sudo mkdir -p /opt/customer_support_agent
sudo chown -R $USER:$USER /opt/customer_support_agent
```

### Step 7.3: Push Code from Local to Trigger GitHub Actions

Ensure everything is committed to your `test` branch. On your local machine, run:

```bash
git add .
git commit -m "feat: Add prometheus and grafana for observability"
git push origin test
```

Because we added `test` to `.github/workflows/deploy-ec2.yml`, pushing to `test` will automatically trigger the workflow. 
The Action will:
1. `ssh` into your EC2.
2. Transfer the application code via `scp`.
3. Auto-run `docker compose up -d --build --remove-orphans`.
4. Run an automated curl to `http://localhost:8000/health` inside the EC2 to assure it's working.

### Step 7.4: Verification post-deployment & Postman Testing

To verify everything has launched correctly on your EC2 instance, perform the following tests:

**1. Test FastAPI is Working (Swagger UI)**
- Visit `http://<EC2_PUBLIC_IP>:8000/docs` in your browser.
- You should see the interactive FastAPI Swagger interface.
- Expand the `GET /health` endpoint, click **Try it out**, and execute. You should receive a `200 OK` response with `{"status": "ok"}`.

**2. Test FastAPI via Postman**
If you prefer API testing with Postman, you can verify your deployed endpoints:
- Open Postman and create a new **GET** request.
- Enter the URL: `http://<EC2_PUBLIC_IP>:8000/health`.
- Click **Send**.
- You should immediately get a 200 OK status code.
- You can similarly test your main API queries like `GET http://<EC2_PUBLIC_IP>:8000/tickets` (adding any needed Auth/Headers per your app requirements).

**3. Application Interface**
- Visit `http://<EC2_PUBLIC_IP>:8501`.
- Verify the Streamlit app loads and connects to your bot.

**4. Test Prometheus Monitoring**
- Visit `http://<EC2_PUBLIC_IP>:9090/targets` (ensure port 9090 is allowed in your Security Group).
- Look for the `support-copilot-api` job. The status should be **UP**.
- Visit `http://<EC2_PUBLIC_IP>:8000/metrics` directly via your browser or Postman to see the raw text metrics generated by your requests.

**5. Test Grafana Dashboard**
- Visit `http://<EC2_PUBLIC_IP>:3000`.
- Log in with the default credentials: username `admin` and password `admin`.
- Navigate to **Connections -> Data sources**. You should see "Prometheus" already listed as the default.
- Click on it and hit **Save & Test**. It should return a green tick "Data source is working".
- To instantly visualize your FastAPI data, go to **Dashboards -> Import**, and insert a community FastAPI Prometheus dashboard ID (e.g., ID: `18987` or `14694` from the Grafana marketplace) and select Prometheus as the data source.
