import json
import os
from typing import Any

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient

load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "ops-docs-index")

STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
INDEXED_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_INDEXED", "indexed-docs")


def read_indexed_docs_from_blob() -> list[dict[str, Any]]:
    if not STORAGE_CONNECTION_STRING:
        raise ValueError("Missing AZURE_STORAGE_CONNECTION_STRING")

    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(INDEXED_CONTAINER_NAME)
    print("blob_service_client",blob_service_client)
    print("container_client",container_client)
    

    docs: list[dict[str, Any]] = []

    for blob in container_client.list_blobs():
        blob_name = blob.name

        # Only read JSON/JSONL style files
        if not (blob_name.endswith(".json") or blob_name.endswith(".jsonl")):
            continue

        print(f"Reading blob: {blob_name}")

        blob_client = container_client.get_blob_client(blob_name)
        content = blob_client.download_blob().readall().decode("utf-8")

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))

    return docs


def main() -> None:
    if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY")
    print("hererererre")
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )
    print("hererererre 2")
    docs = read_indexed_docs_from_blob()
    if not docs:
        raise ValueError("No indexed docs found in Azure Blob Storage container")

    results = search_client.upload_documents(documents=docs)
    succeeded = sum(1 for r in results if r.succeeded)

    print(f"Uploaded {succeeded}/{len(docs)} indexed chunks to index '{INDEX_NAME}'.")


if __name__ == "__main__":
    main()