from openai import AzureOpenAI

from .config import Settings


def build_llm_client(settings: Settings) -> AzureOpenAI:
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        raise ValueError("Azure OpenAI endpoint or API key is missing.")

    return AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )

