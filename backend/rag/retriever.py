import chromadb
from pathlib import Path


class MigrationRetriever:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="migration_docs"
        )

    def add_document(
        self,
        document: str,
        source: str,
        chunk_id: int,
        section: str
    ):
        document_id = f"{source}::chunk_{chunk_id}"

        self.collection.upsert(
            documents=[document],
            ids=[document_id],
            metadatas=[
                {
                    "source": source,
                    "section": section,
                    "chunk_id": chunk_id
                }
            ]
        )

    def search(
        self,
        query: str,
        n_results: int = 3
    ):
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )


def chunk_markdown(content: str):
    """
    Split Markdown documentation into meaningful sections.

    Each ## heading starts a new chunk.
    """

    sections = []
    current_section = "Introduction"
    current_content = []

    for line in content.splitlines():

        if line.startswith("## "):

            if current_content:
                sections.append({
                    "section": current_section,
                    "content": "\n".join(current_content).strip()
                })

            current_section = line.replace("## ", "").strip()
            current_content = [line]

        else:
            current_content.append(line)

    # Add final section
    if current_content:
        sections.append({
            "section": current_section,
            "content": "\n".join(current_content).strip()
        })

    return sections


def load_documents():

    retriever = MigrationRetriever()

    docs_path = Path("docs")

    for file in docs_path.rglob("*.md"):

        content = file.read_text(
            encoding="utf-8"
        )

        chunks = chunk_markdown(content)

        for chunk_id, chunk in enumerate(chunks):

            retriever.add_document(
                document=chunk["content"],
                source=str(file),
                chunk_id=chunk_id,
                section=chunk["section"]
            )

    return retriever