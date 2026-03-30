# Azure GenAI Ops Copilot

Production-style Azure GenAI + RAG project for operational documents.

## Step 1 completed
- FastAPI scaffold
- config management
- request/response models
- health endpoint
- ask endpoint stub
- feedback endpoint
- Azure Monitor telemetry hook
- Dockerfile
- basic test

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn api.app.main:app --reload