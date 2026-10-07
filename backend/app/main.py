from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data.loader import load_cases
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.semantic import SemanticRetriever
from app.retrieval.rrf import RRF

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cases = load_cases()
bm25 = BM25Retriever(cases)
semantic = SemanticRetriever(cases)
rrf = RRF(bm25, semantic)

@app.get("/")
def root():
    return {"message": "Legal Document Search API is running"}

@app.get("/search")
def search(query: str, top_k: int=5):
    results = rrf.search(query, top_k=top_k)
    return {
        "query": query,
        "results": results
    }