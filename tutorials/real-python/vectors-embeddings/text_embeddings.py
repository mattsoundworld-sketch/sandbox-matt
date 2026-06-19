from sentence_transformers import SentenceTransformer
from cosine_similarity import cosine_similarity
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_text_vector(texts: list[str]) -> np.ndarray:
    return model.encode(texts)


if __name__ == "__main__":
    # Example texts
    texts = [
        "The cat stared at me.",
        "The cat looked at me."
    ]
    
    # Get embeddings
    embeddings = get_text_vector(texts)
    
    # Print results
    print(f"Number of texts: {len(texts)}")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"First embedding (first 10 dimensions): {embeddings[0][:10]}")
    
    # Example: Calculate similarity between first two texts
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    print(f"Similarity between text 1 and 2: {similarity:.4f}")

