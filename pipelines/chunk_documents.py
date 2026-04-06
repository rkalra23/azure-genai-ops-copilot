from pyspark.sql import SparkSession
import os
import uuid

CHUNK_SIZE = 500


def parse_document(content: str) -> dict:
    lines = content.splitlines()

    metadata = {
        "title": "",
        "version": "",
        "effective_date": "",
        "department": "",
        "doc_type": "",
        "body": "",
    }

    for line in lines:
        if line.startswith("Title:"):
            metadata["title"] = line.replace("Title:", "").strip()
        elif line.startswith("Version:"):
            metadata["version"] = line.replace("Version:", "").strip()
        elif line.startswith("Effective Date:"):
            metadata["effective_date"] = line.replace("Effective Date:", "").strip()
        elif line.startswith("Department:"):
            metadata["department"] = line.replace("Department:", "").strip()
        elif line.startswith("Doc Type:"):
            metadata["doc_type"] = line.replace("Doc Type:", "").strip()

    metadata["body"] = content
    return metadata


def chunk_text(text: str):
    return [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]


def main():
    spark = SparkSession.builder.appName("ChunkDocs").getOrCreate()

    input_dir = "data/raw_docs"
    output_dir = "data/processed_docs"

    rows = []

    for filename in os.listdir(input_dir):
        filepath = os.path.join(input_dir, filename)

        with open(filepath, "r") as f:
            content = f.read()

        meta = parse_document(content)
        chunks = chunk_text(meta["body"])

        doc_id = filename.replace(".txt", "")

        for i, chunk in enumerate(chunks):
            rows.append({
                "chunk_id": f"{doc_id}-chunk-{i+1}",
                "doc_id": doc_id,
                "title": meta["title"],
                "version": meta["version"],
                "effective_date": meta["effective_date"],
                "department": meta["department"],
                "doc_type": meta["doc_type"],
                "chunk_text": chunk,
            })

    df = spark.createDataFrame(rows)

    df.write.mode("overwrite").json(output_dir)

    print(f"Processed {len(rows)} chunks → {output_dir}")


if __name__ == "__main__":
    main()