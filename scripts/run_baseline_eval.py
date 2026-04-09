import json
import os
from pathlib import Path

import requests

API_URL = os.getenv("BASELINE_API_URL", "http://127.0.0.1:8000/ask")
OUTPUT_FILE = Path("eval/baseline_results_with_top_k_3_and_filtered_results_with_score_min_2_doc.json")

QUESTIONS = [
    "How do I restart billing service?",
    "What should I do if billing restart fails?",
    "How do I handle a severity 1 incident?",
    "How do I troubleshoot API timeout?",
    "What is the escalation path if service health remains degraded?",
    "How do I validate billing service health after restart?",
    "What are the common causes of payment failure?",
    "When should I escalate to L2 support?",
]

MODES = ["keyword", "vector", "hybrid"]


def main() -> None:
    results = []

    for question in QUESTIONS:
        for mode in MODES:
            payload = {
                "question": question,
                "retrieval_mode": mode,
                "top_k": 3,
            }

            print(f"Running | mode={mode} | question={question}")
            response = requests.post(API_URL, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            results.append(
                {
                    "question": question,
                    "mode": mode,
                    "latency_ms": data.get("latency_ms"),
                    "request_id": data.get("request_id"),
                    "prompt_tokens":data.get("prompt_tokens"),
                    "completion_tokens":data.get("completion_tokens"),
                    "total_tokens": data.get("total_tokens"),
                    "estimated_cost_usd": data.get("estimated_cost_usd"),
                    "answer": data.get("answer"),
                    "sources": [
                        {
                            "title": s.get("title"),
                            "chunk_id": s.get("chunk_id"),
                            "effective_date": s.get("effective_date"),
                            "score": s.get("score"),
                        }
                        for s in data.get("sources", [])
                    ],
                    "notes": "",
                }
            )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved baseline results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()