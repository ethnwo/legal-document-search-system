from sentence_transformers import SentenceTransformer
from app.data.loader import load_cases
import numpy as np
import faiss

class SemanticRetriever:
    def __init__(self, cases):
        self.cases = cases
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.chunks = []
        self.chunk_case_indices = []

        for case_index, case in enumerate(cases):
            words = case["text"].split()
            chunk_size = 200
            overlap = 50

            for start in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[start:start + chunk_size])
                if not chunk.strip():
                    continue
                self.chunks.append(chunk)
                self.chunk_case_indices.append(case_index)

        print(f"Total chunks: {len(self.chunks)}")

        self.embeddings = self.model.encode(
            self.chunks,
            batch_size = 32,
            show_progress_bar = True,
            convert_to_numpy = True,
            normalize_embeddings = True
        )

        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings.astype(np.float32))
        print("Semantic index created successfully.")

    def search(self, query, top_k=5):
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy = True,
            normalize_embeddings = True
        ).astype(np.float32)

        scores, indices = self.index.search(query_embedding, top_k * 10)
        case_scores = {}

        for score, chunk_index in zip(scores[0], indices[0]):
            if chunk_index == -1:
                continue

            case_index = self.chunk_case_indices[chunk_index]

            if (case_index not in case_scores or score > case_scores[case_index]):
                case_scores[case_index] = float(score)

        ranked_cases = sorted(case_scores.items(), key = lambda item:item[1], reverse = True)[:top_k]
        results = []

        for case_index, score in ranked_cases:
            case = self.cases[case_index]
            results.append({
                "case_id": case["case_id"],
                "case_name": case["case_name"],
                "decision_date": case["decision_date"],
                "court": case["court"],
                "jurisdiction": case["jurisdiction"],
                "citation": case["citation"],
                "score": score
            })

        return results

if __name__ == "__main__":
    cases = load_cases()
    retriever = SemanticRetriever(cases)

    query = "negligence duty of care"
    results = retriever.search(query, top_k=5)

    print(f"\nQuery: {query}\n")
    print("Top results:")

    for rank, result in enumerate(results, start=1):
        print(f"\n{rank}. {result['case_name']}")
        print(f"   Citation: {result['citation']}")
        print(f"   Date: {result['decision_date']}")
        print(f"   Court: {result['court']}")
        print(f"   Similarity: {result['score']:.4f}")