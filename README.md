# Azure GenAI Operations Copilot

## Overview

Enterprise-style Retrieval-Augmented Generation (RAG) assistant built using FastAPI, Azure AI Search, and Azure OpenAI.
This project simulates an internal operations copilot capable of answering operational and troubleshooting questions using runbooks, SOPs, and support documentation.
The system evolved from a basic hybrid retrieval pipeline into a more production-oriented retrieval architecture using configurable ranking strategies, Azure AI Search semantic ranking, source-grounded responses, evaluation, observability, and cost-aware guardrails.

---

# 🚀 Features

* 🔍 Keyword-based retrieval using Azure AI Search
* 🧠 Vector search using Azure OpenAI embeddings
* ⚡ Hybrid retrieval combining keyword + vector search
* 🧭 Configurable reranking modes:
  * `none`
  * `heuristic`
  * `azure_semantic`
* ☁️ Azure AI Search semantic ranking using index-level semantic configuration
* 🔧 Metadata filtering using `department` and `doc_type`
* ✂️ Section-aware semantic chunking for operational documents
* 📄 Document ingestion and indexing pipeline
* 🧾 Source-grounded LLM responses with citations
* 🎯 Final context limiting using `final_context_top_n`
* 🛡️ Prompt-injection guardrail
* 🚫 Zero-cost no-evidence guardrail that skips the LLM when retrieved evidence is weak
* 📊 Scored RAG evaluation workflow
* 💰 Token usage and estimated cost tracking
* ⏱️ Latency and request observability
* 🖥️ Frontend controls for retrieval mode, rerank mode, and top-k comparison

---

# 🏗️ Architecture

```text
Raw Documents
        ↓
Ingestion / Chunking Pipeline
(metadata extraction + section-aware chunking)
        ↓
Embedding Enrichment
(Azure OpenAI Embeddings)
        ↓
Azure AI Search Index
(keyword fields + vector embeddings + semantic configuration)
        ↓
FastAPI Backend
        ↓
Retrieval Mode
(keyword / vector / hybrid)
        ↓
Optional Ranking Strategy
(none / heuristic / Azure AI Search semantic ranking)
        ↓
Score Filtering + Evidence Gate
        ↓
Final Context Selection
(final_context_top_n)
        ↓
Azure OpenAI
(only called when sufficient evidence exists)
        ↓
Answer + Sources + Metrics
        ↓
Frontend UI
```

---

# ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | HTML, CSS, JavaScript |
| Search | Azure AI Search |
| LLM | Azure OpenAI |
| Embeddings | Azure OpenAI Embeddings |
| Managed semantic ranking | Azure AI Search semantic ranking |
| Local lightweight reranking | Heuristic reranker |
| Data Pipeline | PySpark |
| Storage | Azure Blob Storage |
| CI | GitHub Actions |
| Containerization | Docker |

---

# 🧱 Data Pipeline

The project implements a multi-stage ingestion and retrieval pipeline.

## 1. Raw Document Storage

Operational documents such as runbooks, SOPs, and troubleshooting guides are stored in Azure Blob Storage.

## 2. Semantic Chunking Pipeline

A PySpark pipeline performs:

* metadata extraction
* section-aware chunking
* structured document processing

The original implementation used fixed-size character chunking, which produced fragmented semantic context.

The pipeline was later improved using section-aware chunking based on operational document structure:

* Overview
* Preconditions
* Restart Procedure
* Validation Steps
* Troubleshooting

This produced more coherent standalone chunks for retrieval and grounding.

## 3. Embedding Enrichment

Each chunk is enriched using Azure OpenAI embeddings before indexing into Azure AI Search.

## 4. Azure AI Search Index

The search index contains:

* searchable text fields such as `title` and `chunk_text`
* metadata fields such as `department`, `doc_type`, and `effective_date`
* vector embeddings for vector and hybrid retrieval
* a semantic configuration used by Azure AI Search semantic ranking

---

# 🧠 Retrieval Ranking Strategies

The API supports multiple ranking strategies so retrieval quality, latency, and cost can be compared during development and demos.

## Retrieval Modes

| Mode | Description |
|---|---|
| `keyword` | Uses text search over indexed document fields. |
| `vector` | Uses Azure OpenAI embeddings and vector similarity search. |
| `hybrid` | Combines text search and vector similarity search. Recommended for demos. |

## Rerank Modes

| Mode | Description |
|---|---|
| `none` | Uses the Azure AI Search result order after score filtering. |
| `heuristic` | Applies a lightweight local reranker based on simple matching logic. Docker-safe and low overhead. |
| `azure_semantic` | Uses Azure AI Search semantic ranking with the configured semantic index profile. |

## Why CrossEncoder Was Removed From the Docker Demo Path

The project originally experimented with a local CrossEncoder reranker using `sentence-transformers`. While useful for experimentation, the local ML dependency stack increased Docker image size and caused runtime instability in the container environment.

The production/demo path now uses Azure AI Search semantic ranking instead of local CrossEncoder inference. This keeps the API container lightweight and deployment-friendly while still supporting semantic ranking.

## Recommended Demo Configuration

```json
{
  "retrieval_mode": "hybrid",
  "rerank_mode": "azure_semantic",
  "top_k": 10
}
```

Hybrid retrieval provides both text and vector signals, while Azure semantic ranking improves the ordering of text results using the semantic configuration defined on the Azure AI Search index.

---

# 💰 Cost Optimization and Guardrails

The API is designed to avoid unnecessary LLM calls and reduce prompt size.

## Final Context Limiting

The system retrieves a broad candidate set using `top_k`, then narrows the final prompt context using `final_context_top_n`.

Example:

```text
top_k = 10
filtered results = 6
final_context_top_n = 3
```

Only the final 3 chunks are sent to the LLM. This reduces prompt tokens, cost, latency, and noisy context.

## Zero-Cost No-Evidence Guardrail

Before calling Azure OpenAI, the API checks whether the retrieved chunks provide sufficient evidence for the user question.

If evidence is weak, irrelevant, or out-of-index, the API skips the LLM call and returns:

```json
{
  "answer": "I could not find enough evidence in the indexed documents to answer this question.",
  "final_context_count": 0,
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "estimated_cost_usd": 0.0,
  "sources": []
}
```

This prevents the model from answering from general knowledge and avoids unnecessary token cost.

## Prompt-Injection Guardrail

Obvious prompt-injection attempts, such as requests to reveal the system prompt or override instructions, are blocked before retrieval or generation.

---

# 📈 Evaluation & Optimization

The project includes a scored RAG evaluation workflow driven by a JSONL dataset.

The eval runner checks:

* expected answer terms
* expected source presence
* unsupported-question handling
* prompt-injection handling
* no-evidence zero-cost behavior
* latency
* token usage
* estimated cost

Example summary:

```json
{
  "total_cases": 9,
  "passed": 9,
  "failed": 0,
  "pass_rate": 100.0
}
```

Run evals with:

```bash
python scripts/run_baseline_eval.py
```

---

# 📊 Observability

The API tracks request-level observability metrics including:

* `request_id`
* `retrieval_mode`
* `rerank_mode`
* `top_k`
* `raw_result_count`
* `filtered_result_count`
* `reranked_result_count`
* `final_context_count`
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
* comparison between ranking strategies

---

# 🧪 Sample API Request

```json
{
  "question": "What should I check after bringing billing back online?",
  "retrieval_mode": "hybrid",
  "rerank_mode": "azure_semantic",
  "top_k": 10
}
```

Example response metrics:

```json
{
  "retrieval_mode": "hybrid",
  "rerank_mode": "azure_semantic",
  "top_k": 10,
  "raw_result_count": 10,
  "filtered_result_count": 6,
  "reranked_result_count": 6,
  "final_context_count": 3,
  "prompt_tokens": 439,
  "completion_tokens": 81,
  "total_tokens": 520,
  "estimated_cost_usd": 0.00341
}
```

---

# 🖥️ Frontend Demo

The frontend allows comparison of retrieval and ranking strategies from the browser.

Controls include:

* question input
* retrieval mode selector
* rerank mode selector
* top-k selector

The response panel displays:

* answer
* sources
* result counts
* final context count
* token usage
* estimated cost
* latency

A useful comparison query is:

```text
What should I check after bringing billing back online?
```

This demonstrates that cheaper heuristic ranking may not always retrieve the best operational validation context, while Azure semantic ranking can produce a more useful grounded answer.

---

# ✅ Example Improvements Achieved

The final retrieval pipeline achieved:

* cleaner retrieval results
* configurable ranking strategies
* Docker-safe semantic ranking path using Azure AI Search
* reduced noisy context through final context limiting
* zero-cost fallback for out-of-index questions
* improved answer grounding with citations
* request-level latency, token, and cost observability
* scored eval coverage for retrieval quality and guardrails

---

# 🔮 Future Improvements

Planned future enhancements include:

* LangSmith tracing for RAG observability
* Query decomposition
* Agentic retrieval workflows
* Adaptive retrieval strategies
* Streaming responses
* Multi-query retrieval
* Semantic caching
* Optional separate reranker service

---

# 🧠 Key Learnings

* Retrieval quality directly impacts answer quality.
* Hybrid retrieval provides both text and vector signals.
* Azure AI Search semantic ranking keeps the Docker path lighter than local CrossEncoder inference.
* Candidate recall and ranking precision must be balanced carefully in production RAG systems.
* Final context limiting is a practical token and cost optimization technique.
* Out-of-domain questions should skip the LLM instead of allowing ungrounded general-knowledge answers.
* Chunk boundary quality is critical for grounded retrieval systems.

---

# 📌 Final Retrieval Architecture

```text
User Question
        ↓
Prompt-Injection Guardrail
        ↓
Azure AI Search Retrieval
(keyword / vector / hybrid)
        ↓
Optional Ranking
(none / heuristic / Azure semantic ranking)
        ↓
Weak Result Filtering
        ↓
Final Context Selection
(final_context_top_n)
        ↓
Evidence Gate
        ├── Weak evidence → Skip LLM, cost = $0
        └── Strong evidence → Azure OpenAI
        ↓
Answer + Citations + Token/Cost Metrics
```