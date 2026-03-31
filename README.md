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

User  
→ FastAPI  
→ Azure AI Search (retrieve relevant chunks)  
→ Azure OpenAI (generate grounded response)  
→ Final Answer with Sources  

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