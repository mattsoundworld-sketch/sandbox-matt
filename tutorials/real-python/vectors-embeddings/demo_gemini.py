import json
import os
import chromadb
from chromadb.utils import embedding_functions
from google import genai
from google.genai import types

os.environ["TOKENIZERS_PARALLELISM"] = "false"
CHROMA_PATH = "car_review_embeddings"
EMBEDDING_FUNC_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "car_reviews"


def main():
    # Load config from file or environment variable
    config_file = "config.json"
    
    if os.path.exists(config_file):
        with open(config_file, mode="r") as json_file:
            config = json.load(json_file)
        api_key = config.get("gemini-secret-key")
    else:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("Gemini API key not found. Set GEMINI_API_KEY or provide config.json")
    
    gemini = genai.Client(api_key=api_key)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_FUNC_NAME)

    collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding_function)
    
    context = """You are a customer success employee at a large car dealership. 
                Use the following car reviews to answer the question {}. 
                If the answer is not in the reviews, say 'I don't know'.    
                """
    question = "What's the key to great customer satisfaction based on detailed positive reviews? Under 200 words."
    
    good_reviews = collection.query(
        query_texts=[question],
        n_results=5,
        include=["documents"],
        where={"Rating": {"$gte": 3}}
    )

    reviews_str = ",".join(good_reviews['documents'][0])
    
    response = gemini.models.generate_content(
        model="gemini-2.5-flash",
        config =types.GenerateContentConfig(system_instruction=context.format(reviews_str)),
        contents = question
    )

    print("Response from Gemini API:")
    print(response.text)


if __name__ == "__main__":
    main()


