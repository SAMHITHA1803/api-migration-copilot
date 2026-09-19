from rag.retriever import load_documents


retriever = load_documents()

results = retriever.search(
    "How should DataFrame.append be migrated?",
    n_results=2
)

print(results)