import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "ops-docs-index")

INDEXED_DIR = Path(os.getenv("INDEXED_DOCS_PATH", "data/indexed_docs"))


def read_indexed_chunks() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    for file_path in INDEXED_DIR.rglob("*.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                docs.append(json.loads(line))

    return docs


def main() -> None:
    if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY")

    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )

    docs = read_indexed_chunks()
    if not docs:
        raise ValueError("No processed docs found in data/processed_docs")
    print(docs)
    results = client.upload_documents(documents=docs)
    succeeded = sum(1 for r in results if r.succeeded)

    print(f"Uploaded {succeeded}/{len(docs)} processed chunks to index '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()