import os
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from dotenv import load_dotenv
load_dotenv()
# ===== ENV =====
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "ops-docs-index")

DOCS_DIR = Path("data/sample_docs")
CHUNK_SIZE = 800


# ===== SIMPLE CHUNKING =====
def chunk_text(text: str, chunk_size=CHUNK_SIZE):
    chunks = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) < chunk_size:
            current += " " + line
        else:
            chunks.append(current.strip())
            current = line

    if current:
        chunks.append(current.strip())

    return chunks


# ===== MAIN =====
def main():
    print("\n=== DEBUG START ===\n")

    # 1. Check env
    print("SEARCH_ENDPOINT:", SEARCH_ENDPOINT)
    print("INDEX_NAME:", INDEX_NAME)

    if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
        raise ValueError("Missing Azure Search env vars")

    # 2. Check files
    print("\nChecking files...")
    files = list(DOCS_DIR.glob("*.txt"))
    print(f"Found {len(files)} files")

    if not files:
        raise ValueError("No .txt files found in data/sample_docs")

    # 3. Read + chunk one file
    sample_file = files[0]
    print(f"\nReading file: {sample_file}")

    text = sample_file.read_text(encoding="utf-8")
    chunks = chunk_text(text)

    print(f"Chunks created: {len(chunks)}")
    print("Sample chunk:\n", chunks[0][:200], "...")

    # 4. Build ONE document (simplify debugging)
    doc = {
        "chunk_id": "debug-chunk-1",
        "doc_id": "debug-doc",
        "title": "Debug Document",
        "doc_type": "test",
        "department": "test",
        "version": "v1",
        "effective_date": "2026-01-01",
        "chunk_text": chunks[0],
        "source_path": str(sample_file),
    }

    # 5. Connect to search
    client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )

    # 6. Upload
    print("\nUploading test document...")
    result = client.upload_documents(documents=[doc])[0]

    print("Upload success:", result.succeeded)
    if not result.succeeded:
        print("Error:", result.error_message)

    # 7. Search immediately
    print("\nSearching index...")
    results = list(client.search(search_text="*", top=5))

    print(f"Documents found: {len(results)}")
    for r in results:
        print(f"- {r['chunk_id']} | {r['title']}")

    print("\n=== DEBUG END ===\n")


if __name__ == "__main__":
    main()