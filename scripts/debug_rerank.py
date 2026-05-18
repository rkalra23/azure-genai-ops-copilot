# def simple_rerank(results, query):
#     query_words = set(query.lower().split())

#     reranked = []

#     for item in results:
#         text = item.get("chunk_text", "").lower()
#         title = item.get("title", "").lower()

#         bonus = 0

#         # keyword overlap boost
#         for word in query_words:
#             if word in text:
#                 bonus += 0.01

#         # title boost
#         for word in query_words:
#             if word in title:
#                 bonus += 0.02

#         original_score = item.get("@search.score") or 0

#         final_score = original_score + bonus

#         reranked.append((final_score, item))

#     reranked.sort(key=lambda x: x[0], reverse=True)

#     return reranked

from api.app.config import get_settings
from api.app.search_client import build_search_client
from api.app.retrieval import _get_query_embedding
from api.app.llm_client import build_llm_client

from azure.search.documents.models import VectorizedQuery


QUESTION = "How do I restart billing service after timeout failures?"


from collections import defaultdict


def simple_rerank(results, query, max_per_doc=2):
    query_words = set(query.lower().split())

    reranked = []

    for item in results:
        text = item.get("chunk_text", "").lower()
        title = item.get("title", "").lower()

        bonus = 0

        # keyword overlap boost
        for word in query_words:
            if word in text:
                bonus += 0.01

        # title overlap boost
        for word in query_words:
            if word in title:
                bonus += 0.02

        original_score = item.get("@search.score") or 0

        final_score = original_score + bonus

        item["rerank_score"] = final_score

        reranked.append(item)

    reranked.sort(
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    # diversity filtering
    final_results = []

    doc_counts = defaultdict(int)

    for item in reranked:
        doc_id = item.get("doc_id")

        if doc_counts[doc_id] >= max_per_doc:
            continue

        final_results.append(item)

        doc_counts[doc_id] += 1

    return final_results

def main():
    settings = get_settings()

    search_client = build_search_client(settings)
    llm_client = build_llm_client(settings)

    query_embedding = _get_query_embedding(
        llm_client=llm_client,
        settings=settings,
        text=QUESTION,
    )

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=10,
        fields="embedding",
    )

    results = list(
        search_client.search(
            search_text=QUESTION,
            vector_queries=[vector_query],
            top=10,
        )
    )
    print(results)
    print("\n==============================")
    print(" RAW RETRIEVAL RESULTS ")
    print("==============================\n")

    for i, item in enumerate(results, start=1):
        print(f"Rank #{i}")
        print("Title:", item.get("title"))
        print("Chunk:", item.get("chunk_id"))
        print("Retrieval Score:", item.get("@search.score"))
        print("Preview:", item.get("chunk_text")[:150])
        print("-" * 80)

    reranked_results = simple_rerank(results, QUESTION)

    print("\n==============================")
    print(" RERANKED RESULTS ")
    print("==============================\n")

    for i, item in enumerate(reranked_results, start=1):
        print(f"Rank #{i}")
        print("Title:", item.get("title"))
        print("Chunk:", item.get("chunk_id"))
        print("Retrieval Score:", item.get("@search.score"))
        print("Rerank Score:", item.get("rerank_score"))
        print("Preview:", item.get("chunk_text")[:150])
        print("-" * 80)


if __name__ == "__main__":
    main()