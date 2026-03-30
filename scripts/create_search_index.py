import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    SearchableField,
)

load_dotenv()
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "ops-docs-index")

def main() -> None:
    if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_API_KEY")

    credential = AzureKeyCredential(SEARCH_API_KEY)
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

    fields = [
        SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="doc_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="department", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="version", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="effective_date", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="chunk_text", type=SearchFieldDataType.String),
        SimpleField(name="source_path", type=SearchFieldDataType.String),
    ]

    index = SearchIndex(name=INDEX_NAME, fields=fields)

    existing = None
    try:
        existing = index_client.get_index(INDEX_NAME)
    except Exception:
        existing = None

    if existing:
        print(f"Index '{INDEX_NAME}' already exists.")
    else:
        index_client.create_index(index)
        print(f"Created index '{INDEX_NAME}' successfully.")


if __name__ == "__main__":
    main()