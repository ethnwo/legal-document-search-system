from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from rapidfuzz.distance import DamerauLevenshtein
from app.data.loader import load_cases
import re

def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

class BM25Retriever:
    def __init__(self, cases):
        self.cases = cases
        self.vocabulary = set()
        tokenized_documents = []
        for case in cases:
            tokens = tokenize(case["text"])
            tokenized_documents.append(tokens)
            self.vocabulary.update(tokens)
        self.bm25 = BM25Okapi(tokenized_documents)

    def fuzzy_correct(self, query_tokens, threshold=90):
        corrected_tokens = []

        for token in query_tokens:
            if token in self.vocabulary:
                corrected_tokens.append(token)
                continue

            if len(token) <= 4:
                max_distance = 1
            else:
                max_distance = 2

            candidates = []
            for candidate in self.vocabulary:
                distance = DamerauLevenshtein.distance(token, candidate)

                if distance <= max_distance:
                    similarity = fuzz.ratio(token, candidate)
                    candidates.append((candidate, distance, similarity))

            candidates.sort(key=lambda item: (item[1], -item[2]))

            if candidates and candidates[0][2] >= threshold:
                corrected_tokens.append(candidates[0][0])
            else:
                corrected_tokens.append(token)
        return corrected_tokens

    def search(self, query, top_k=5):
        tokenized_query = tokenize(query)
        corrected_query = self.fuzzy_correct(tokenized_query)
        print(f"Corrected query: {' '.join(corrected_query)}")
        scores = self.bm25.get_scores(corrected_query)
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
    query = "judical reveiw administrative law"
    results = retriever.search(query, top_k=5)

    print("Top results:")
    for rank, result in enumerate(results, start=1):
        print(f"\n{rank}. {result['case_name']}")
        print(f"   Citation: {result['citation']}")
        print(f"   Date: {result['decision_date']}")
        print(f"   Court: {result['court']}")
        print(f"   BM25 score: {result['score']:.4f}")