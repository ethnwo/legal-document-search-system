from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.data.loader import load_cases
import numpy as np
import faiss
import os
import json

class SemanticRetriever:
    def __init__(self, cases):
        self.cases = cases
        self.index_dir = Path("/var/data/indexes/semantic")
        self.index_path = self.index_dir / "index.faiss"
        self.mapping_path = self.index_dir / "chunk_case_indices.npy"
        self.chunks_path = self.index_dir / "chunks.json"
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path) and os.path.exists(self.chunks_path):
            self.load_index()
        else:
            self.build_index()

    def build_index(self):
        self.chunks = []
        self.chunk_case_indices = []

        for case_index, case in enumerate(self.cases):
            words = case["text"].split()
            chunk_size = 200
            overlap = 50

            for start in range(0, len(words), chunk_size-overlap):
                chunk = " ".join(words[start:start + chunk_size])
                if not chunk.strip():
                    continue
                self.chunks.append(chunk)
                self.chunk_case_indices.append(case_index)

            print(f"Total chunks: {len(self.chunks)}")

        self.embeddings = self.model.encode(
            self.chunks,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings.astype(np.float32))
        print("Semantic index created successfully.")

        os.makedirs(self.index_dir, exist_ok = True)
        faiss.write_index(self.index, str(self.index_path))
        np.save(self.mapping_path, np.array(self.chunk_case_indices))

        with open(self.chunks_path, "w", encoding = "utf-8") as file:
            json.dump(self.chunks, file)

        print("Semantic index saved successfully.")

    
    def load_index(self):
        self.index = faiss.read_index(str(self.index_path))
        self.chunk_case_indices = np.load(self.mapping_path).tolist()

        with open(self.chunks_path, "r", encoding="utf-8") as file:
            self.chunks = json.load(file)

        # Check that all stored index components have matching sizes.
        index_size = self.index.ntotal
        mapping_size = len(self.chunk_case_indices)
        chunks_size = len(self.chunks)

        if index_size != mapping_size or mapping_size != chunks_size:
            raise ValueError(
                "Semantic index files are inconsistent: "
                f"FAISS vectors={index_size}, "
                f"chunk mappings={mapping_size}, "
                f"stored chunks={chunks_size}."
            )

        # Check that each chunk points to a valid case.
        invalid_indices = [
            case_index
            for case_index in self.chunk_case_indices
            if case_index < 0 or case_index >= len(self.cases)
        ]

        if invalid_indices:
            raise ValueError(
                f"Semantic index contains {len(invalid_indices)} "
                "invalid case indices."
            )

        print("Semantic index loaded and validated successfully.")
    

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
                
        ranked_cases = sorted(case_scores.items(), key=lambda item:item[1], reverse=True)[:top_k]
        results = []

        for case_index, score in ranked_cases:
            case = self.cases[case_index]
            results.append({
                "case_id":case["case_id"],
                "score":score
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