from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from app.data.loader import load_cases
from app.data.metadata_store import MetadataStore
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.semantic import SemanticRetriever
from app.retrieval.rrf import RRF
import time

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cases = load_cases()
metadata_store = MetadataStore()
metadata_store.import_cases(cases)
bm25 = BM25Retriever(cases)
semantic = SemanticRetriever(cases)
rrf = RRF(bm25, semantic)

@app.get("/")
def root():
    return {"message": "Legal Document Search API is running"}


@app.get("/search")
def search(
    query: str,
    method: str = Query(
        default="hybrid",
        pattern="^(bm25|semantic|hybrid)$"
    ),
    top_k: int = Query(default=100, ge=1, le=1000),
    court: str | None = None,
    jurisdiction: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None
):
    total_start = time.perf_counter()
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date"
        )

    # Select the retrieval method.
    retrieval_start = time.perf_counter()

    if method == "bm25":
        results = bm25.search(query, top_k=top_k)
    elif method == "semantic":
        results = semantic.search(query, top_k=top_k)
    else:
        results = rrf.search(query, top_k=top_k)

    retrieval_time_ms = (time.perf_counter() - retrieval_start) * 1000

    # Apply metadata filters after retrieval and ranking.
    filtered_case_ids = metadata_store.get_filtered_case_ids(
        court=court,
        jurisdiction=jurisdiction,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None
    )

    filtered_results = [
        result
        for result in results
        if str(result["case_id"]) in filtered_case_ids
    ]

    # Retrieve metadata from SQLite.
    metadata_by_id = metadata_store.get_many(
        result["case_id"] for result in filtered_results
    )

    final_results = []

    for result in filtered_results:
        final_result = result.copy()
        metadata = metadata_by_id.get(str(result["case_id"]))

        if metadata:
            final_result.update({
                "case_name": metadata["case_name"],
                "decision_date": metadata["decision_date"],
                "court": metadata["court"],
                "jurisdiction": metadata["jurisdiction"],
                "citation": metadata["citation"],
                "source": metadata["source"]
            })

        final_results.append(final_result)

    total_search_time_ms = (time.perf_counter() - total_start) * 1000

    return {
        "query": query,
        "method": method,
        "total_candidates": len(results),
        "total_filtered": len(final_results),
        "retrieval_time_ms": round(retrieval_time_ms, 3),
        "total_search_time_ms": round(total_search_time_ms, 3),
        "results": final_results
    }


@app.get("/filters")
def get_filters():
    return metadata_store.get_filter_options()
