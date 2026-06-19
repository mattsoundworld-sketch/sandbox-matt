import chromadb
from chromadb.utils import embedding_functions

CHROMA_DATA_PATH = "chroma_data/"
EMBED_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "demo_docs"


def main():
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Example: Add documents
    documents = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Embeddings are numerical representations of text"
    ]
    
    collection.add(
        ids=[f"doc_{i}" for i in range(len(documents))],
        documents=documents
    )
    
    # Example: Query
    results = collection.query(
        query_texts=["artificial intelligence"],
        n_results=3
    )
    
    print("Query results:")
    print(results)


if __name__ == "__main__":
    main()


