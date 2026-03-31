# Azure GenAI Operations Copilot

## Overview
Enterprise-style RAG assistant built with FastAPI, Azure AI Search, and Azure OpenAI.

## Features
- Azure AI Search document retrieval
- Azure OpenAI grounded answer generation
- Metadata filtering
- FastAPI microservice
- Source-backed answers

## Architecture
User → FastAPI → Azure AI Search → Azure OpenAI → Response

## Tech Stack
- Python
- FastAPI
- Azure AI Search
- Azure OpenAI
- Pydantic

## Sample Query
How do I restart billing service?

## Sample Response
- step-by-step restart instructions
- troubleshooting notes
- escalation guidance
- sources used

## Project Status
- Step 1: API scaffold ✅
- Step 2: Azure AI Search retrieval ✅
- Step 3: Azure OpenAI answer generation ✅
- Step 4: Vector and hybrid retrieval ⏳

## Setup
1. Copy `.env.example` to `.env`
2. Fill Azure credentials
3. Create search index
4. Load sample docs
5. Run FastAPI