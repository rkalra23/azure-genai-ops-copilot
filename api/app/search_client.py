from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from .config import Settings


def build_search_client(settings: Settings) -> SearchClient:
    if not settings.azure_search_endpoint or not settings.azure_search_api_key:
        raise ValueError("Azure AI Search endpoint or API key is missing.")

    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )