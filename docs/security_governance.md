# Security and Governance

## Overview

This project implements a Retrieval-Augmented Generation (RAG) operations copilot using FastAPI, Azure AI Search, and Azure OpenAI.

The security and governance controls focus on protecting cost-incurring endpoints, reducing hallucination risk, preventing obvious prompt-injection attempts, enforcing source grounding, and keeping secrets out of source control.

---

## Endpoint Protection

### Public Endpoints

`/health` is intentionally public.

It is used for local checks, Docker checks, CI smoke tests, and future deployment health probes.

It should return only minimal non-sensitive information.

### Protected Endpoints

`/ask` is protected with API key authentication.

Clients must send:

```http
x-api-key: <configured-api-key>
```

The backend compares this value against:

```env
APP_API_KEY
```

If the key is missing or invalid, the API returns:

```http
401 Unauthorized
```

This protects the cost-incurring RAG endpoint from casual unauthorized use.

---

## API Key Limitations

The current API key mechanism is intended for controlled demos and internal prototypes.

It does not provide:

* user signup
* per-user identity
* role-based access control
* user-level usage tracking
* enterprise login
* secure public frontend authentication

For a production public application, the recommended path is:

* Microsoft Entra ID for internal enterprise users
* Microsoft Entra External ID / Azure AD B2C for external signup/login
* JWT bearer token validation in the backend
* optional Azure API Management for rate limiting and policy enforcement

---

## CORS Policy

The backend supports a configurable allowed-origin list using:

```env
ALLOWED_ORIGINS
```

For local development, this may include:

```env
http://127.0.0.1:5500,http://localhost:5500
```

For deployment, this should be restricted to the deployed frontend domain only.

Example:

```env
ALLOWED_ORIGINS=https://your-frontend.azurestaticapps.net
```

---

## Secret Management

Secrets are provided through environment variables and must not be committed to source control.

Sensitive values include:

* `APP_API_KEY`
* `AZURE_OPENAI_API_KEY`
* `AZURE_SEARCH_API_KEY`
* Azure service endpoints if considered sensitive
* Azure Monitor connection strings

Local development uses `.env`.

The repository should only contain `.env.example` with placeholder values.

For production, use:

* Azure Container Apps environment variables
* Azure Key Vault
* Managed Identity where supported
* GitHub Actions secrets for CI/CD

---

## Prompt-Injection Guardrail

The API includes a basic prompt-injection guardrail for obvious attempts such as:

* ignoring previous instructions
* revealing the system prompt
* exposing developer or system messages
* jailbreak-style requests

When detected, the API returns a safe response without calling retrieval or Azure OpenAI.

This keeps token usage and cost at zero for blocked prompt-injection attempts.

---

## Source Grounding

The assistant is designed to answer only from indexed operational documents.

The prompt instructs the model to use retrieved context and cite sources.

The response includes source metadata such as:

* title
* chunk ID
* document ID
* effective date
* search score

This supports traceability and answer review.

---

## No-Evidence Guardrail

Before calling Azure OpenAI, the API checks whether retrieved chunks provide sufficient evidence for the user question.

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

---

## Cost Governance

The API reports token and cost metrics per request:

* `prompt_tokens`
* `completion_tokens`
* `total_tokens`
* `estimated_cost_usd`
* `latency_ms`
* `raw_result_count`
* `filtered_result_count`
* `reranked_result_count`
* `final_context_count`

Cost is controlled by:

* limiting `top_k`
* applying score filtering
* using `final_context_top_n`
* skipping the LLM when evidence is weak
* blocking prompt-injection attempts before generation

---

## Evaluation Governance

The project includes a JSONL-based evaluation dataset and runner.

The eval workflow checks:

* expected answer terms
* expected source usage
* unsupported question handling
* prompt-injection handling
* no-evidence zero-cost behavior
* token usage
* estimated cost
* latency

This helps prevent regressions in retrieval quality and guardrail behavior.

---

## Logging and Observability

The API logs request-level metadata such as:

* request ID
* retrieval mode
* rerank mode
* result counts
* latency
* skipped LLM calls
* fallback behavior

Development logs may include summarized retrieval results.

Production logging should avoid storing:

* secrets
* raw prompts containing sensitive data
* full retrieved document text
* personally identifiable information
* confidential customer data

---

## Current Limitations

Current controls are suitable for a controlled demo or internal prototype.

Known limitations:

* API key auth is not user-level authentication.
* Frontend JavaScript cannot securely store secrets.
* Prompt-injection detection is pattern-based and not exhaustive.
* Evidence gating is heuristic and should be tuned with evals.
* Full production identity should use Microsoft Entra ID or Entra External ID.
* Rate limiting is not yet implemented.
* Azure Key Vault integration is not yet implemented.

---

## Recommended Production Path

For a production deployment, the next security milestones are:

1. Use Microsoft Entra ID or Entra External ID for login.
2. Validate JWT bearer tokens in the FastAPI backend.
3. Store secrets in Azure Key Vault.
4. Use Managed Identity where possible.
5. Add Azure API Management for rate limiting and policy controls.
6. Restrict CORS to deployed frontend domains.
7. Add production-safe logging and monitoring.
8. Add budget alerts and usage monitoring.