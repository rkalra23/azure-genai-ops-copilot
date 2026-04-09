# Azure GenAI Operations Copilot

## Overview
Enterprise-style Retrieval-Augmented Generation (RAG) assistant built using FastAPI, Azure AI Search, and Azure OpenAI.

This project simulates an internal operations copilot that answers questions using runbooks, SOPs, and troubleshooting documents.

---

## 🚀 Features

- 🔍 Keyword-based search (Azure AI Search)
- 🧠 Vector search using Azure OpenAI embeddings
- ⚡ Hybrid retrieval (keyword + semantic search)
- 📄 Document chunking and indexing
- 🤖 Grounded LLM responses using retrieved context
- 🧾 Source-backed answers
- 🔧 Metadata filtering (department, doc_type)
- Baseline evaluation for retrieval quality, latency, and token usage
- Token and estimated cost tracking for LLM requests
- Retrieval filtering to reduce noisy context and improve efficiency

---

## 🏗️ Architecture

```text
Raw Documents (Azure Blob Storage)
        ↓
PySpark Pipeline (chunking + metadata extraction)
        ↓
Processed Documents
        ↓
Embedding Enrichment (Azure OpenAI)
        ↓
Indexed Documents
        ↓
Azure AI Search (Hybrid Retrieval)
        ↓
FastAPI Backend (RAG)
        ↓
Frontend UI

## ⚙️ Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript
- Search: Azure AI Search (keyword + vector + hybrid)
- LLM: Azure OpenAI (chat + embeddings)
- Data Pipeline: PySpark
- Storage: Azure Blob Storage

---

## 🧱 Data Pipeline

This project implements a multi-stage ingestion pipeline:

1. Raw documents are stored in Azure Blob Storage
2. PySpark pipeline performs:
   - metadata extraction
   - document chunking
3. Embedding enrichment using Azure OpenAI
4. Enriched documents are indexed into Azure AI Search

This design separates preprocessing, enrichment, and indexing stages, aligning with production data engineering practices.

---

## 📊 Observability & Production Considerations

- Latency measurement for each query
- Retrieval mode comparison (keyword vs vector vs hybrid)
- Modular pipeline design for scalability

---

## 🧠 Retrieval Modes

| Mode | Description |
|------|------------|
| Keyword | Exact text matching |
| Vector | Semantic similarity using embeddings |
| Hybrid | Combines keyword + vector (best results) |

---

## 📈 Evaluation & Optimization

To improve retrieval quality and reduce LLM cost, the system was evaluated using a baseline test suite across keyword, vector, and hybrid retrieval modes.

### Baseline Evaluation
The project includes a repeatable evaluation script that measures:
- latency per request
- retrieved sources
- prompt / completion / total tokens
- estimated per-request LLM cost
- answer quality across retrieval modes

### Optimization Work
After establishing the baseline, the retrieval pipeline was improved by:
- reducing `top_k` from 5 to 3
- limiting the number of chunks per document
- filtering lower-value chunks before sending context to the LLM

These changes reduced prompt size, improved source relevance, and lowered estimated cost.

### Observability
The API now tracks:
- `request_id`
- `latency_ms`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `estimated_cost_usd`




---

## 📈 Evaluation & Optimization (Recent Updates)

Recent improvements focused on making the system more production-ready and cost-efficient:

### Baseline Evaluation
- Implemented a reusable evaluation script to test queries across:
  - keyword
  - vector
  - hybrid modes
- Captures:
  - latency (`latency_ms`)
  - token usage (`prompt_tokens`, `completion_tokens`, `total_tokens`)
  - estimated cost per request
  - retrieved sources

### Retrieval Optimization
- Reduced `top_k` from **5 → 3**
- Introduced **chunk filtering before LLM call**
- Limited chunks per document to reduce redundancy
- Improved context quality by removing low-relevance chunks

### Impact
- Lower prompt size and token usage
- Reduced estimated cost per request
- Cleaner and more relevant context sent to LLM
- Improved answer quality and consistency

### Observability Enhancements
- Added request-level tracking:
  - `request_id`
  - `latency_ms`
  - token usage
  - estimated cost (`estimated_cost_usd`)

These updates align the system with **real-world GenAI production practices** including monitoring, cost-awareness, and iterative optimization.


## 🧪 Sample Query

```json
{
  "question": "How do I safely restart the billing system?",
  "retrieval_mode": "hybrid",
  "top_k": 3
}