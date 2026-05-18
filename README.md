# Azure GenAI Operations Copilot

## Overview

Enterprise-style Retrieval-Augmented Generation (RAG) assistant built using FastAPI, Azure AI Search, and Azure OpenAI.

This project simulates an internal operations copilot capable of answering operational and troubleshooting questions using runbooks, SOPs, and support documentation.

The system evolved from a basic hybrid retrieval pipeline into a more production-oriented retrieval architecture using semantic reranking, semantic chunking, observability, and cost-aware optimizations.

---

# 🚀 Features

* 🔍 Keyword-based retrieval using Azure AI Search
* 🧠 Vector search using Azure OpenAI embeddings
* ⚡ Hybrid retrieval (keyword + vector search)
* 🤖 Cross-encoder semantic reranking
* ✂️ Semantic chunking for operational documents
* 📄 Document ingestion and indexing pipeline
* 🧾 Source-grounded LLM responses
* 🔧 Metadata filtering (`department`, `doc_type`)
* 📊 Baseline retrieval evaluation framework
* 💰 Token usage and estimated cost tracking
* ⏱️ Latency and request observability
* 🎯 Semantic threshold filtering for cleaner prompts

---

# 🏗️ Architecture

```text
Raw Documents (Azure Blob Storage)
        ↓
PySpark Pipeline
(metadata extraction + semantic chunking)
        ↓
Embedding Enrichment (Azure OpenAI)
        ↓
Indexed Documents
        ↓
Azure AI Search
(Hybrid Retrieval - top-k candidate generation)
        ↓
Cross-Encoder Semantic Reranking
        ↓
Semantic Threshold Filtering
        ↓
GPT-4o Response Generation
        ↓
FastAPI Backend
        ↓
Frontend UI
```

---

# ⚙️ Tech Stack

| Layer             | Technology                             |
| ----------------- | -------------------------------------- |
| Backend           | FastAPI (Python)                       |
| Frontend          | HTML, CSS, JavaScript                  |
| Search            | Azure AI Search                        |
| LLM               | Azure OpenAI                           |
| Embeddings        | Azure OpenAI Embeddings                |
| Semantic Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Data Pipeline     | PySpark                                |
| Storage           | Azure Blob Storage                     |

---

# 🧱 Data Pipeline

The project implements a multi-stage ingestion and retrieval pipeline.

## 1. Raw Document Storage

Operational documents such as:

* runbooks
* SOPs
* troubleshooting guides

are stored in Azure Blob Storage.

---

## 2. Semantic Chunking Pipeline

A PySpark pipeline performs:

* metadata extraction
* semantic chunking
* structured document processing

The original implementation used fixed-size character chunking, which produced fragmented semantic context.

The pipeline was later improved using section-aware semantic chunking based on operational document structure:

* Overview
* Preconditions
* Restart Procedure
* Validation Steps
* Troubleshooting

This produced coherent standalone semantic chunks and significantly improved reranking quality.

---

## 3. Embedding Enrichment

Each semantic chunk is enriched using Azure OpenAI embeddings before indexing into Azure AI Search.

---

## 4. Hybrid Retrieval

Azure AI Search performs:

* keyword retrieval
* vector similarity retrieval
* hybrid retrieval

The retriever generates a broader candidate set (`top-k`) for downstream semantic reranking.

---

# 🧠 Semantic Reranking

To improve retrieval precision and reduce noisy context, the project evolved from basic hybrid retrieval into a multi-stage semantic retrieval architecture.

## Problem Identified

Initial retrieval occasionally returned semantically weak or operationally unrelated chunks due to:

* broad embedding similarity
* keyword overlap
* fragmented chunk boundaries

Examples included unrelated troubleshooting documents appearing in billing restart queries.

---

## Cross-Encoder Semantic Reranking

Implemented a second-stage semantic reranker using:

```text
cross-encoder/ms-marco-MiniLM-L-6-v2
```

The reranker evaluates:

```text
(query + document chunk)
```

together and assigns semantic relevance scores.

This significantly improved:

* retrieval precision
* context quality
* grounding quality
* token efficiency

compared to heuristic keyword-based reranking.

---

## Semantic Threshold Filtering

After reranking, low-confidence chunks are removed before prompt construction.

Benefits:

* reduced noisy context
* cleaner prompts
* lower token usage
* improved answer grounding
* reduced hallucination risk

---

# 📈 Evaluation & Optimization

The project includes a repeatable evaluation workflow to measure retrieval and generation quality.

## Baseline Evaluation

Implemented evaluation tooling that measures:

* retrieval quality
* latency per request
* retrieved sources
* prompt tokens
* completion tokens
* total tokens
* estimated LLM cost

---

## Retrieval Optimization Journey

The retrieval pipeline evolved through multiple stages:

### Phase 1 — Baseline Hybrid Retrieval

* keyword + vector retrieval
* direct prompt construction

### Phase 2 — Heuristic Reranking

* keyword overlap boosts
* title boosts
* chunk filtering

### Phase 3 — Semantic Cross-Encoder Reranking

* semantic relevance scoring
* improved operational precision
* cleaner grounding

### Phase 4 — Semantic Chunking

* section-aware chunking
* coherent semantic context
* improved reranking quality

---

# 📊 Observability

The API tracks request-level observability metrics including:

* `request_id`
* `latency_ms`
* `prompt_tokens`
* `completion_tokens`
* `total_tokens`
* `estimated_cost_usd`

This enables:

* retrieval benchmarking
* token optimization
* cost monitoring
* performance analysis

---

# 🧪 Sample Query

```json
{
  "question": "How do I safely restart the billing system?",
  "retrieval_mode": "hybrid",
  "top_k": 10
}
```

---

# ✅ Example Improvements Achieved

The final retrieval pipeline achieved:

* cleaner retrieval results
* removal of noisy operational documents
* improved semantic relevance
* lower prompt token usage
* more focused grounded answers
* improved retrieval explainability

---

# 🔮 Future Improvements

Planned future enhancements include:

* Query decomposition
* Agentic retrieval workflows
* Automated evaluation framework
* Adaptive retrieval strategies
* Streaming responses
* Reranker latency optimization
* Multi-query retrieval
* Semantic caching

---

# 🧠 Key Learnings

* Retrieval quality directly impacts answer quality.
* Semantic chunking significantly improves reranking effectiveness.
* Cross-encoder rerankers outperform heuristic keyword-based reranking for operational queries.
* Candidate recall and semantic precision must be balanced carefully in production RAG systems.
* Chunk boundary quality is critical for semantic retrieval systems.

---

# 📌 Final Retrieval Architecture

```text
Azure AI Search
(Hybrid Retrieval - top 10 candidates)
        ↓
Cross-Encoder Semantic Reranking
        ↓
Semantic Threshold Filtering
        ↓
Top Relevant Semantic Chunks
        ↓
GPT-4o
```
