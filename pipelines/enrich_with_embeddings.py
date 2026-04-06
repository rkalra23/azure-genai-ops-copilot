import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

PROCESSED_DIR = Path(os.getenv("PROCESSED_DOCS_PATH", "data/processed_docs"))
INDEXED_DIR = Path(os.getenv("INDEXED_DOCS_PATH", "data/indexed_docs"))

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION,
)


def read_processed_chunks() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    for file_path in PROCESSED_DIR.rglob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                docs.append(json.loads(line))

    return docs


def get_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=text,
    )
    return response.data[0].embedding


def enrich_chunks(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched_docs: list[dict[str, Any]] = []

    for i, doc in enumerate(docs, start=1):
        chunk_text = doc.get("chunk_text", "")
        if not chunk_text:
            continue

        embedding = get_embedding(chunk_text)
        doc["embedding"] = embedding
        enriched_docs.append(doc)

        print(f"Embedded chunk {i}/{len(docs)}: {doc.get('chunk_id')}")

    return enriched_docs


def write_indexed_docs(docs: list[dict[str, Any]]) -> None:
    INDEXED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = INDEXED_DIR / "indexed_chunks.json"

    with open(output_file, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc) + "\n")

    print(f"Wrote {len(docs)} enriched chunks to {output_file}")


def main() -> None:
    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
        raise ValueError(
            "Missing AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, or AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        )

    docs = read_processed_chunks()
    if not docs:
        raise ValueError("No processed docs found in processed docs directory")

    enriched_docs = enrich_chunks(docs)
    write_indexed_docs(enriched_docs)


if __name__ == "__main__":
    main()