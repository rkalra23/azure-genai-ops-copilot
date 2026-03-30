import os
import re
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "ops-docs-index")

DOCS_DIR = Path("data/sample_docs")
CHUNK_SIZE = 800


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def parse_metadata_and_body(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    metadata = {
        "title": "",
        "version": "",
        "effective_date": "",
        "department": "",
        "doc_type": "",
    }

    body_lines = []
    in_metadata = True

    for line in lines:
        stripped = line.strip()
        if in_metadata and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "title":
                metadata["title"] = value
            elif key == "version":
                metadata["version"] = value
            elif key == "effective date":
                metadata["effective_date"] = value
            elif key == "department":
                metadata["department"] = value
            elif key == "doc type":
                metadata["doc_type"] = value
            else:
                body_lines.append(line)
        else:
            in_metadata = False
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    return metadata, body


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


def build_documents() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    for path in DOCS_DIR.glob("*.txt"):
        raw = path.read_text(encoding="utf-8")
        metadata, body = parse_metadata_and_body(raw)

        title = metadata["title"] or path.stem
        doc_id = slugify(title)
        chunks = chunk_text(body)

        for i, chunk in enumerate(chunks, start=1):
            docs.append(
                {
                    "chunk_id": f"{doc_id}-chunk-{i}",
                    "doc_id": doc_id,
                    "title": title,
                    "doc_type": metadata["doc_type"] or "unknown",
                    "department": metadata["department"] or "unknown",
                    "version": metadata["version"] or "unknown",
                    "effective_date": metadata["effective_date"] or "",
                    "chunk_text": chunk,
                    "source_path": str(path),
                }
            )

    return docs


def main() -> None:
    if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY")

    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )

    docs = build_documents()
    if not docs:
        raise ValueError("No sample docs found in data/sample_docs")

    results = client.upload_documents(documents=docs)
    succeeded = sum(1 for r in results if r.succeeded)

    print(f"Uploaded {succeeded}/{len(docs)} documents to index '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()