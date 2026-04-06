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

## 🧪 Sample Query

```json
{
  "question": "How do I safely restart the billing system?",
  "retrieval_mode": "hybrid",
  "top_k": 3
}