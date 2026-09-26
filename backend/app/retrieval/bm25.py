from rank_bm25 import BM25Okapi
from app.data.loader import load_cases

class BM25Retriever:
    def __init__(self, cases):
        self.cases = cases
        tokenized_documents = [
            case["text"].lower().split() # take a look at this again once all retrieval techniques are done
            for case in cases
        ]
        self.bm25 = BM25Okapi(tokenized_documents)

    def search(self, query, top_k=5):
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = scores.argsort()[::-1][:top_k]
        results = []
        for index in ranked_indices:
            case = self.cases[index]
            results.append({
                "case_id": case["case_id"],
                "case_name": case["case_name"],
                "decision_date": case["decision_date"],
                "court": case["court"],
                "jurisdiction": case["jurisdiction"],
                "citation": case["citation"],
                "score": float(scores[index])
            })
        return results

if __name__ == "__main__":
    cases = load_cases()
    retriever = BM25Retriever(cases)
    query = "breach of contract damages"
    results = retriever.search(query, top_k=5)

    print(f"\nQuery: {query}\n")
    print("Top results:")

    for rank, result in enumerate(results, start=1):
        print(f"\n{rank}. {result['case_name']}")
        print(f"   Citation: {result['citation']}")
        print(f"   Date: {result['decision_date']}")
        print(f"   Court: {result['court']}")
        print(f"   BM25 score: {result['score']:.4f}")