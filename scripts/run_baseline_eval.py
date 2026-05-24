import json
import os
from pathlib import Path
from statistics import mean
from typing import Any
from openai import BadRequestError
from dotenv import load_dotenv
import requests


API_URL = os.getenv("BASELINE_API_URL", "http://127.0.0.1:8000/ask")
DATASET_FILE = Path("eval/datasets/rag_eval_dataset.jsonl")
RESULTS_FILE = Path("eval/results/eval_results.json")
SUMMARY_FILE = Path("eval/results/eval_summary.json")


load_dotenv()
API_HEADERS = {
    "Content-Type": "application/json",
}
api_key = os.getenv("APP_API_KEY", "")

if api_key:
    API_HEADERS["x-api-key"] = api_key

def load_dataset(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Eval dataset not found: {path}")

    cases = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc

    return cases


def contains_any(text: str, expected_terms: list[str]) -> bool:
    if not expected_terms:
        return True

    lowered = text.lower()
    return any(term.lower() in lowered for term in expected_terms)


def source_matches(sources: list[dict[str, Any]], expected_sources: list[str]) -> bool:
    if not expected_sources:
        return True

    source_text = " ".join(
        [
            str(source.get("title", ""))
            + " "
            + str(source.get("doc_id", ""))
            + " "
            + str(source.get("chunk_id", ""))
            for source in sources
        ]
    ).lower()

    return any(expected.lower() in source_text for expected in expected_sources)


def score_case(case: dict[str, Any], response_data: dict[str, Any]) -> tuple[bool, list[str]]:
    failures = []

    answer = response_data.get("answer") or ""
    sources = response_data.get("sources") or []

    requires_sources = case.get("requires_sources", True)
    expected_no_answer = case.get("expected_no_answer", False)

    expected_answer_terms_any = case.get("expected_answer_terms_any", [])
    expected_sources_any = case.get("expected_sources_any", [])

    if requires_sources and not sources:
        failures.append("required_sources_missing")

    if not source_matches(sources, expected_sources_any):
        failures.append("expected_source_not_found")

    if not contains_any(answer, expected_answer_terms_any):
        failures.append("expected_answer_terms_not_found")

    if expected_no_answer:
        safe_fallback_terms = [
            "could not find",
            "not enough evidence",
            "provided documents",
            "cannot",
            "do not have enough information",
        ]
        if not contains_any(answer, safe_fallback_terms):
            failures.append("unsupported_question_not_handled_safely")
        if sources:
            failures.append("unsupported_question_returned_sources")

        if (response_data.get("prompt_tokens") or 0) != 0:
            failures.append("unsupported_question_used_prompt_tokens")

        if (response_data.get("completion_tokens") or 0) != 0:
            failures.append("unsupported_question_used_completion_tokens")

        if (response_data.get("total_tokens") or 0) != 0:
            failures.append("unsupported_question_used_total_tokens")

        if (response_data.get("estimated_cost_usd") or 0.0) != 0.0:
            failures.append("unsupported_question_incurred_cost")

    return len(failures) == 0, failures


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "question": case["question"],
        "rerank_mode": case.get("rerank_mode", "azure_semantic"),
        "retrieval_mode": case.get("retrieval_mode", "hybrid"),
        "top_k": case.get("top_k", 3),
    }
    try:
        response = response = requests.post(API_URL,json=payload,headers=API_HEADERS,timeout=120,)
        response.raise_for_status()
        data = response.json()

        passed, failures = score_case(case, data)

        return {
         "id": case["id"],
            "question": case["question"],
            "retrieval_mode": payload["retrieval_mode"],
            "rerank_mode": data.get("rerank_mode"),
            "requested_rerank_mode": payload.get("rerank_mode"),
            "top_k": payload["top_k"],
            "passed": passed,
            "failures": failures,
            "latency_ms": data.get("latency_ms"),
            "request_id": data.get("request_id"),
            "raw_result_count": data.get("raw_result_count"),
            "filtered_result_count": data.get("filtered_result_count"),
            "reranked_result_count": data.get("reranked_result_count"),
            "final_context_count": data.get("final_context_count"),
            "prompt_tokens": data.get("prompt_tokens"),
            "completion_tokens": data.get("completion_tokens"),
            "total_tokens": data.get("total_tokens"),
            "estimated_cost_usd": data.get("estimated_cost_usd"),
            "answer": data.get("answer"),
            "sources": data.get("sources", []),
            }
    except Exception as exc:
        return {
            "id": case.get("id"),
            "question": case.get("question"),
            "retrieval_mode": payload.get("retrieval_mode"),
            "requested_rerank_mode": payload.get("rerank_mode"),
            "rerank_mode": None,
            "top_k": payload.get("top_k"),
            "passed": False,
            "failures": [f"eval_case_failed: {type(exc).__name__}: {exc}"],
            "latency_ms": None,
            "request_id": None,
            "raw_result_count": None,
            "filtered_result_count": None,
            "reranked_result_count": None,
            "final_context_count": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
            "answer": None,
            "sources": [],
        }

def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    failed = total - passed

    latencies = [
    item["latency_ms"]
    for item in results
    if isinstance(item.get("latency_ms"), (int, float))
    ]

    total_cost = sum(
        item.get("estimated_cost_usd") or 0
        for item in results
    )

    return {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / total) * 100, 2) if total else 0,
        "average_latency_ms": round(mean(latencies), 2) if latencies else None,
        "total_estimated_cost_usd": round(total_cost, 8),
    }


def main() -> None:
    cases = load_dataset(DATASET_FILE)

    results = []
    for case in cases:
        print(f"Running eval | id={case['id']} | question={case['question']}")
        result = run_case(case)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{status} | id={result['id']} | failures={result['failures']}")
        results.append(result)

    summary = build_summary(results)

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with RESULTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with SUMMARY_FILE.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nEval summary")
    print(json.dumps(summary, indent=2))

    if summary["failed"] > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()