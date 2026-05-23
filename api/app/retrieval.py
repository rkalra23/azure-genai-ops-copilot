from time import perf_counter
from uuid import uuid4

import logging

from azure.search.documents.models import VectorizedQuery

from .config import get_settings
from .llm_client import build_llm_client
from .models import AskRequest, AskResponse, SourceItem
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .search_client import build_search_client
## rerank testing  , going ahead with Azure semantic reranking,cross encpder is breaking the application
# from .rerank import simple_rerank
#from .semantic_rerank import semantic_rerank
##Azure Sematic reranking
from azure.core.exceptions import HttpResponseError


logger = logging.getLogger(__name__)

def _build_filter(request: AskRequest) -> str | None:
    filters = []

    if request.department:
        filters.append(f"department eq '{request.department}'")

    if request.doc_type:
        filters.append(f"doc_type eq '{request.doc_type}'")

    if not filters:
        return None

    return " and ".join(filters)

# Add a strength check:
def _has_strong_evidence(question: str, results, retrieval_mode: str) -> bool:
    if not results:
        return False

    stop_words = {
        "what", "when", "where", "which", "with", "from", "this", "that",
        "should", "could", "would", "have", "after", "before", "into",
        "about", "there", "their", "then", "than", "does", "your", "you",
        "the", "and", "for", "are", "how",
    }

    question_terms = {
        token.strip(".,?!:;()[]{}").lower()
        for token in question.split()
        if len(token.strip(".,?!:;()[]{}")) >= 4
    } - stop_words

    if not question_terms:
        return False

    combined_text = " ".join(
        f"{item.get('title', '')} {item.get('chunk_text', '')}"
        for item in results
    ).lower()

    overlap_count = sum(1 for term in question_terms if term in combined_text)

    # Require at least one meaningful query term to appear in retrieved evidence.
    # This blocks out-of-domain questions like "capital of India".
    if overlap_count == 0:
        return False

    # Keep only a light score floor because Azure semantic/hybrid scores are not
    # always comparable across modes.
    top_score = results[0].get("@search.score") or 0.0
    thresholds = {
        "keyword": 1.0,
        "vector": 0.01,
        "hybrid": 0.01,
    }

    return top_score >= thresholds.get(retrieval_mode, 0.01)


def _build_context_blocks(search_results) -> tuple[list[SourceItem], list[str]]:
    sources: list[SourceItem] = []
    context_blocks: list[str] = []

    for item in search_results:
        title = item.get("title", "Unknown")
        chunk_id = item.get("chunk_id", "unknown")
        chunk_text = item.get("chunk_text", "")
        doc_id = item.get("doc_id")
        effective_date = item.get("effective_date")
        score = item.get("@search.score")

        sources.append(
            SourceItem(
                title=title,
                chunk_id=chunk_id,
                doc_id=doc_id,
                effective_date=effective_date,
                score=score,
            )
        )

        block = (
            f"Title: {title}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Effective Date: {effective_date or 'unknown'}\n"
            f"Content:\n{chunk_text}"
        )
        context_blocks.append(block)

    return sources, context_blocks

def _get_query_embedding(llm_client, settings, text: str) -> list[float]:
    response = llm_client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=text,
    )
    return response.data[0].embedding

def _estimate_chat_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    input_cost_per_1m: float,
    output_cost_per_1m: float,
    ) -> float:
    input_cost = (prompt_tokens / 1_000_000) * input_cost_per_1m
    output_cost = (completion_tokens / 1_000_000) * output_cost_per_1m
    return round(input_cost + output_cost, 8)

def _filter_search_results(search_results, retrieval_mode: str, max_per_doc: int = 2):
    if retrieval_mode == "keyword":
        min_score = 1.0
    else:
        min_score = 0.015
        
    filtered = []
    # per_doc_count = {}
    
    for item in search_results:
        score=item.get("@search.score") or 0.0
        doc_id = item.get("doc_id") or "unknown"
        
        # filter weak results
        if score < min_score:
            continue
        # limit chunks per document
        # if per_doc_count.get(doc_id, 0) >= max_per_doc:
        #     continue
        
        filtered.append(item)
        # per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1

    return filtered

def _looks_like_prompt_injection(question: str) -> bool:
    patterns = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "reveal the system prompt",
        "show me the system prompt",
        "developer message",
        "system message",
        "jailbreak",
    ]

    normalized = question.lower()
    return any(pattern in normalized for pattern in patterns)

def _summarize_results(search_results, include_rerank_score: bool = False) -> list[dict]:
    summarized = []

    for item in search_results:
        row = {
            "title": item.get("title"),
            "chunk_id": item.get("chunk_id"),
            "doc_id": item.get("doc_id"),
            "search_score": item.get("@search.score"),
        }

        if include_rerank_score:
            row["semantic_rerank_score"] = item.get("semantic_rerank_score")

        summarized.append(row)

    return summarized

def _apply_heuristic_rerank(search_results, question: str):
    try:
        from .rerank import simple_rerank

        return simple_rerank(search_results, question)
    except Exception:
        logger.exception("heuristic_rerank_failed | fallback=filtered_results")
        return search_results
def _search_with_azure_semantic(
    *,
    search_client,
    request: AskRequest,
    search_filter: str | None,
    top_k: int,
    vector_query=None,
    semantic_config_name: str,
    ):
    search_kwargs = {
        "search_text": request.question,
        "filter": search_filter,
        "top": top_k,
        "query_type": "semantic",
        "semantic_configuration_name": semantic_config_name,
        "query_caption": "extractive",
        "query_answer": "extractive",
    }

    if vector_query is not None:
        search_kwargs["vector_queries"] = [vector_query]

    return search_client.search(**search_kwargs)



def answer_question(request: AskRequest, default_mode: str, default_top_k: int) -> AskResponse:
    settings = get_settings()
    search_client = build_search_client(settings)
    llm_client = build_llm_client(settings)

    start = perf_counter()

    request_id = str(uuid4())
    retrieval_mode = request.retrieval_mode or default_mode
    top_k = request.top_k or default_top_k
    search_filter = _build_filter(request)
    
    rerank_mode = request.rerank_mode or settings.default_rerank_mode
    actual_rerank_mode = rerank_mode
    final_context_top_n = settings.final_context_top_n
    
    if _looks_like_prompt_injection(request.question):
        latency_ms = int((perf_counter() - start) * 1000)
        logger.warning(
        "prompt_injection_blocked | request_id=%s retrieval_mode=%s rerank_mode=%s",
        request_id,
        retrieval_mode,
        rerank_mode,
        )

        return AskResponse(
        request_id=request_id,
        answer=(
            "I cannot follow instructions that attempt to override system or application behavior. "
            "Please ask a question related to the indexed operations documents."
        ),
        retrieval_mode=retrieval_mode,
        rerank_mode="blocked_prompt_injection",
        top_k=top_k,
        latency_ms=latency_ms,
        raw_result_count=0,
        filtered_result_count=0,
        reranked_result_count=0,
        final_context_count=0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0.0,
        sources=[],
        )

    vector_query = None
    if retrieval_mode in ("vector", "hybrid"):
        query_embedding = _get_query_embedding(
        llm_client=llm_client,
        settings=settings,
        text=request.question,
        )
        vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding",
        )
    try:
        if rerank_mode == "azure_semantic" and retrieval_mode in ("keyword", "hybrid"):
            results_iter = _search_with_azure_semantic(
            search_client=search_client,
            request=request,
            search_filter=search_filter,
            top_k=top_k,
            vector_query=vector_query if retrieval_mode == "hybrid" else None,
            semantic_config_name=settings.azure_search_semantic_config_name,
            )
        elif retrieval_mode == "keyword":
            results_iter = search_client.search(
            search_text=request.question,
            filter=search_filter,
            top=top_k,)
        elif retrieval_mode == "vector":
            results_iter = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=search_filter,
            top=top_k,)
        else:
            results_iter = search_client.search(
            search_text=request.question,
            vector_queries=[vector_query],
            filter=search_filter,
            top=top_k,)

        results = list(results_iter)
    except HttpResponseError as exc:
        logger.warning(
        "azure_search_semantic_unavailable | request_id=%s rerank_mode=%s fallback=standard_%s error=%s",
        request_id,
        rerank_mode,
        retrieval_mode,
        str(exc).splitlines()[0],
        )
        actual_rerank_mode = f"standard_{retrieval_mode}_fallback"

        if retrieval_mode == "keyword":
            results_iter = search_client.search(
            search_text=request.question,
            filter=search_filter,
            top=top_k,
            )
        elif retrieval_mode == "vector":
            results_iter = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=search_filter,
            top=top_k,
            )
        else:
            results_iter = search_client.search(
            search_text=request.question,
            vector_queries=[vector_query],
            filter=search_filter,
            top=top_k,)
        results = list(results_iter)
    filtered_results = _filter_search_results(results, retrieval_mode)
    
    if rerank_mode == "heuristic":
        reranked_results = _apply_heuristic_rerank(
        filtered_results,
        request.question,
        )
    else:
        reranked_results = filtered_results
    
    logger.info(
    "reranked_retrieval_results | request_id=%s mode=%s reranked_count=%s results=%s",
    request_id,
    retrieval_mode,
    len(reranked_results),
    _summarize_results(reranked_results, include_rerank_score=True),
    )    
    # sources, context_blocks = _build_context_blocks(filtered_results)
    
    final_results = reranked_results[:final_context_top_n]
    if not final_results or not _has_strong_evidence(request.question,final_results,retrieval_mode,):
        latency_ms = int((perf_counter() - start) * 1000)
        logger.info(
        "skipping_llm_call | request_id=%s reason=%s top_score=%s",
        request_id,
        "no_results" if not final_results else "weak_evidence",
        final_results[0].get("@search.score") if final_results else None,
        )
        return AskResponse(
        request_id=request_id,
        answer="I could not find enough evidence in the indexed documents to answer this question.",
        retrieval_mode=retrieval_mode,
        rerank_mode=actual_rerank_mode,
        top_k=top_k,
        latency_ms=latency_ms,
        raw_result_count=len(results),
        filtered_result_count=len(filtered_results),
        reranked_result_count=len(reranked_results),
        final_context_count=0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0.0,
        sources=[],
        )
    logger.info(
        "retrieval_pipeline_completed | request_id=%s retrieval_mode=%s rerank_mode=%s top_k=%s raw_count=%s filtered_count=%s reranked_count=%s final_context_count=%s",
        request_id,
        retrieval_mode,
        rerank_mode,
        top_k,
        len(results),
        len(filtered_results),
        len(reranked_results),
        len(final_results),
        )
    sources, context_blocks = _build_context_blocks(final_results)

    if not context_blocks:
        latency_ms = int((perf_counter() - start) * 1000)
        return AskResponse(
        request_id=request_id,
        answer="I could not find enough evidence in the indexed documents.",
        retrieval_mode=retrieval_mode,
        rerank_mode=actual_rerank_mode,
        top_k=top_k,
        latency_ms=latency_ms,
        raw_result_count=len(results),
        filtered_result_count=len(filtered_results),
        reranked_result_count=len(reranked_results),
        final_context_count=0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0.0,
        sources=[],
        )

    user_prompt = build_user_prompt(
        question=request.question,
        context_blocks=context_blocks,
    )

    completion = llm_client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        
    )
    usage = completion.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else 0
    
    estimated_cost_usd = _estimate_chat_cost_usd(
    prompt_tokens=prompt_tokens,
    completion_tokens=completion_tokens,
    input_cost_per_1m=settings.azure_openai_input_cost_per_1m,
    output_cost_per_1m=settings.azure_openai_output_cost_per_1m,
    )
    

    answer = completion.choices[0].message.content or (
        "I could not find enough evidence in the indexed documents."
    )

    latency_ms = int((perf_counter() - start) * 1000)

    return AskResponse(
        request_id=request_id,
        answer=answer,
        retrieval_mode=retrieval_mode,
        rerank_mode=actual_rerank_mode,
        top_k=top_k,
        latency_ms=latency_ms,
        raw_result_count=len(results),
        filtered_result_count=len(filtered_results),
        reranked_result_count=len(reranked_results),
        final_context_count=len(final_results),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        sources=sources,
        )