import spacy
import numpy as np
from cosine_similarity import cosine_similarity

nlp = spacy.load("en_core_web_lg")

def get_word_vector(word: str) -> np.ndarray:
    doc = nlp(word)
    return doc.vector

def calculate_word_similarity(word1: str, word2: str) -> float:
    vec1 = get_word_vector(word1)
    vec2 = get_word_vector(word2)
    return cosine_similarity(vec1, vec2)

if __name__ == "__main__":
    word1 = input("Enter the first word: ").strip()
    word2 = input("Enter the second word: ").strip()

    if not word1 or not word2:
        print("Please enter two valid words.")
    else:
        similarity = calculate_word_similarity(word1, word2)
        print(f"Similarity between '{word1}' and '{word2}': {similarity:.4f}")


