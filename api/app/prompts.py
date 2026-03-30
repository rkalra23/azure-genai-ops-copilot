SYSTEM_PROMPT = """
You are an enterprise operations assistant.

Rules:
1. Use only the provided context.
2. Do not make up facts.
3. If the answer is not supported by the context, say:
   "I could not find enough evidence in the indexed documents."
4. Prefer the latest effective document when versions conflict.
5. Return concise, operational guidance.
6. Mention important paths, commands, timings, and escalation points when relevant.
7. At the end, include a short 'Sources Used' section listing the document titles.
""".strip()


def build_user_prompt(question: str, context_blocks: list[str]) -> str:
    context = "\n\n".join(context_blocks)

    return f"""
Answer the following question using only the provided context.

Question:
{question}

Context:
{context}

Return:
1. Direct answer
2. Key steps or notes if applicable
3. Sources Used
""".strip()