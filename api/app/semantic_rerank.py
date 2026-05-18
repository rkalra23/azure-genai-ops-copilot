from sentence_transformers import CrossEncoder


model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def semantic_rerank(results, query):
    pairs = []

    for item in results:
        chunk_text = item.get("chunk_text", "")

        pairs.append((query, chunk_text))

    scores = model.predict(pairs)

    reranked = []

    for item, score in zip(results, scores):
        item["semantic_rerank_score"] = float(score)
        reranked.append(item)

    reranked.sort(
        key=lambda x: x["semantic_rerank_score"],
        reverse=True,
    )

    # return reranked[:3]
    filtered = []

    for item in reranked:
        if item["semantic_rerank_score"] > 0:
            filtered.append(item)

    return filtered[:3]