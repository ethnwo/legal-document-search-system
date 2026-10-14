from app.retrieval.bm25 import BM25Retriever
from app.retrieval.semantic import SemanticRetriever
from app.data.loader import load_cases

class RRF:
    def __init__(self, bm25_retriever, semantic_retriever, k=60):
        self.bm25 = bm25_retriever
        self.semantic = semantic_retriever
        self.k = k

    def search(self, query, top_k=5, fusion_k=200):
        bm25_results = self.bm25.search(query, top_k=fusion_k)
        semantic_results = self.semantic.search(query, top_k=fusion_k)

        bm25_ranks = {
            result["case_id"]: rank
            for rank, result in enumerate(bm25_results, start=1)
        }

        semantic_ranks = {
            result["case_id"]: rank
            for rank, result in enumerate(semantic_results, start=1)
        }

        rrf_scores = {}

        for rank, result in enumerate(bm25_results, start=1):
            case_id = result["case_id"]

            if case_id not in rrf_scores:
                rrf_scores[case_id] = 0.0

            rrf_scores[case_id] += 1 / (self.k + rank)

        for rank, result in enumerate(semantic_results, start=1):
            case_id = result["case_id"]

            if case_id not in rrf_scores:
                rrf_scores[case_id] = 0.0

            rrf_scores[case_id] += 1 / (self.k + rank)

        ranked_cases = sorted(rrf_scores.items(), key=lambda item:item[1], reverse=True)

        results = []

        for case_id, rrf_score in ranked_cases[:top_k]:
            result = {
                "case_id": case_id,
                "bm25_rank": bm25_ranks.get(case_id),
                "semantic_rank": semantic_ranks.get(case_id),
                "rrf_score": rrf_score
            }
            results.append(result)

        return results

if __name__ == "__main__":
    cases = load_cases()
    bm25 = BM25Retriever(cases)
    semantic = SemanticRetriever(cases)
    rrf = RRF(bm25, semantic)
    query = "copyright infringement"
    results = rrf.search(query, top_k=5)
    print(f"\nQuery: {query}\n")
    print("RRF results:")

    for rank, result in enumerate(results, start=1):
        print(f"\n{rank}. Case ID: {result['case_id']}")
        print(f"   BM25 rank: {result['bm25_rank']}")
        print(f"   Semantic rank: {result['semantic_rank']}")
        print(f"   RRF score: {result['rrf_score']:.6f}")