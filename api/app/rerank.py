def simple_rerank(results, query):
    query_words = set(query.lower().split())

    reranked = []

    for item in results:
        text = item.get("chunk_text", "").lower()
        title = item.get("title", "").lower()

        bonus = 0

        for word in query_words:
            if word in text:
                bonus += 0.01

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

    # return reranked
    return reranked[:3]