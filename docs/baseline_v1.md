# Baseline v1

## Goal
This file captures the current state of the Azure GenAI Ops Copilot before optimization and code reduction.

## Current Architecture
- Raw documents stored in Azure Blob Storage
- PySpark pipeline for chunking and metadata extraction
- Embedding enrichment using Azure OpenAI
- Indexed documents uploaded to Azure AI Search
- FastAPI backend performs retrieval and RAG-based response generation
- Frontend UI for user interaction

## Current Retrieval Modes
- Keyword
- Vector
- Hybrid

## Current Retrieval Behavior
- Query embedding generated at request time
- Azure AI Search used for keyword, vector, and hybrid retrieval
- Retrieved chunks are passed to Azure OpenAI for grounded answer generation
- Fallback response returned when evidence is insufficient

## Current Settings
- default retrieval mode: hybrid
- default top_k: 5
- embeddings generated using Azure OpenAI
- sources returned with answer
- latency measured per request

## Baseline Questions
1. How do I restart billing service?
2. What should I do if the billing restart fails?
3. How do I handle a severity 1 incident?
4. How do I troubleshoot API timeout?
5. What is the escalation path if service health remains degraded?
6. How do I validate billing service health after restart?
7. What are the common causes of payment failure?
8. When should I escalate to L2 support?

## What Will Be Measured
- latency by retrieval mode
- relevance of retrieved sources
- correctness of final answer
- duplicate or noisy chunks
- code duplication and maintainability issues

## Optimization Goals
- reduce code duplication
- reduce retrieval noise
- improve readability of retrieval flow
- improve modularity
- preserve or improve answer quality