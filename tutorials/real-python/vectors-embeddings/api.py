import json
import os

import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

os.environ["TOKENIZERS_PARALLELISM"] = "false"

CHROMA_PATH = "car_review_embeddings"
EMBEDDING_FUNC_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "car_reviews"
SYSTEM_CONTEXT = (
    "You are a customer success employee at a large car dealership. "
    "Use the following car reviews to answer the question. "
    "Reviews: {reviews}. "
    "If the answer is not in the reviews, say 'I don't know'."
)


def load_api_key() -> str:
    if os.path.exists("config.json"):
        with open("config.json") as f:
            return json.load(f).get("gemini-secret-key", "")
    return os.getenv("GEMINI_API_KEY", "")


app = FastAPI(title="Car Reviews RAG API")

# Initialize clients once at startup — expensive to recreate per request
_gemini: genai.Client | None = None
_collection: chromadb.Collection | None = None


@app.on_event("startup")
def startup():
    global _gemini, _collection

    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("Gemini API key not found. Set GEMINI_API_KEY or provide config.json")

    _gemini = genai.Client(api_key=api_key)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_FUNC_NAME
    )
    _collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_func,
    )


class QuestionRequest(BaseModel):
    question: str
    n_results: int = 5
    min_rating: float = 3.0


class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    results = _collection.query(
        query_texts=[request.question],
        n_results=request.n_results,
        include=["documents"],
        where={"Rating": {"$gte": request.min_rating}},
    )

    sources = results["documents"][0]
    if not sources:
        raise HTTPException(status_code=404, detail="No relevant reviews found")

    reviews_str = "\n---\n".join(sources)
    system_prompt = SYSTEM_CONTEXT.format(reviews=reviews_str)

    response = _gemini.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=system_prompt),
        contents=request.question,
    )

    return AnswerResponse(answer=response.text, sources=sources)


@app.get("/health")
def health():
    return {"status": "ok", "collection": COLLECTION_NAME}
