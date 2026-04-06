from time import perf_counter
from uuid import uuid4

from azure.search.documents.models import VectorizedQuery

from .config import get_settings
from .llm_client import build_llm_client
from .models import AskRequest, AskResponse, SourceItem
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .search_client import build_search_client


def _build_filter(request: AskRequest) -> str | None:
    filters = []

    if request.department:
        filters.append(f"department eq '{request.department}'")

    if request.doc_type:
        filters.append(f"doc_type eq '{request.doc_type}'")

    if not filters:
        return None

    return " and ".join(filters)


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

def answer_question(request: AskRequest, default_mode: str, default_top_k: int) -> AskResponse:
    settings = get_settings()
    search_client = build_search_client(settings)
    llm_client = build_llm_client(settings)

    start = perf_counter()

    request_id = str(uuid4())
    retrieval_mode = request.retrieval_mode or default_mode
    top_k = request.top_k or default_top_k
    search_filter = _build_filter(request)

    if retrieval_mode == "keyword":
        results = search_client.search(
        search_text=request.question,
        filter=search_filter,
        top=top_k,
        )
    else:
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

    if retrieval_mode == "vector":
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=search_filter,
            top=top_k,
        )
    else:  # hybrid
        results = search_client.search(
            search_text=request.question,
            vector_queries=[vector_query],
            filter=search_filter,
            top=top_k,
        )

    sources, context_blocks = _build_context_blocks(results)

    if not context_blocks:
        latency_ms = int((perf_counter() - start) * 1000)
        return AskResponse(
            request_id=request_id,
            answer="I could not find enough evidence in the indexed documents.",
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            latency_ms=latency_ms,
            sources=[],
        )

    user_prompt = build_user_prompt(
        question=request.question,
        context_blocks=context_blocks,
    )
    
    print("DEPLOYMENT:", settings.azure_openai_chat_deployment)
    print("ENDPOINT:", settings.azure_openai_endpoint)
    print("API VERSION:", settings.azure_openai_api_version)

    completion = llm_client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    answer = completion.choices[0].message.content or (
        "I could not find enough evidence in the indexed documents."
    )

    latency_ms = int((perf_counter() - start) * 1000)

    return AskResponse(
        request_id=request_id,
        answer=answer,
        retrieval_mode=retrieval_mode,
        top_k=top_k,
        latency_ms=latency_ms,
        sources=sources,
    )