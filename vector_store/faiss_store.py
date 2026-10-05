import faiss
import json
from pathlib import Path

import numpy as np


class FAISSVectorStore:

    def __init__(self, dimension=None):

        self.dimension = dimension
        self.index = None
        self.chunks = []

        if dimension is not None:
            self.index = faiss.IndexFlatIP(
                dimension
            )

    @staticmethod
    def normalize_vector(vector):

        vector = np.asarray(
            vector,
            dtype="float32"
        )

        norm = np.linalg.norm(vector)

        if norm == 0:
            return vector

        return vector / norm

    @classmethod
    def create(cls, dimension=384):

        return cls(
            dimension=dimension
        )

    def add(self, vectors, chunks):

        vectors = np.array(
            vectors,
            dtype="float32"
        )

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        if len(vectors) != len(chunks):
            raise ValueError(
                "The number of vectors must match the number of chunks."
            )
        if not len(vectors):
            return

        if self.index is None:

            self.dimension = vectors.shape[1]

            self.index = faiss.IndexFlatIP(
                self.dimension
            )

        normalized = np.vstack([
            self.normalize_vector(vector)
            for vector in vectors
        ])

        self.index.add(normalized)

        self.chunks.extend(chunks)

    def search(
        self,
        query_vector,
        top_k=3,
        min_score=0.0
    ):
        if self.index is None or not self.chunks:
            return []
        if top_k <= 0:
            return []

        query_vector = np.asarray(
            query_vector,
            dtype="float32"
        )

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        if query_vector.shape[1] != self.dimension:
            raise ValueError(
                "Query embedding dimensions do not match the FAISS index."
            )

        normalized_query = self.normalize_vector(
            query_vector[0]
        ).reshape(1, -1)

        scores, indices = self.index.search(
            normalized_query,
            min(top_k, self.index.ntotal)
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index == -1:
                continue

            if score < min_score:
                continue

            results.append({
                "chunk": self.chunks[index],
                "score": float(score)
            })

        return results

    def save(
        self,
        folder="vector_data"
    ):

        folder_path = Path(folder)

        folder_path.mkdir(
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            str(
                folder_path / "index.faiss"
            )
        )

        with open(
            folder_path / "chunks.json",
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.chunks,
                file,
                ensure_ascii=False,
                indent=2
            )

    @classmethod
    def load(
        cls,
        folder="vector_data"
    ):

        folder_path = Path(folder)

        index = faiss.read_index(
            str(
                folder_path / "index.faiss"
            )
        )

        with open(
            folder_path / "chunks.json",
            "r",
            encoding="utf-8"
        ) as file:

            chunks = json.load(file)

        if index.ntotal != len(chunks):
            raise ValueError(
                "Vector index and chunk metadata are out of sync. "
                "Please rebuild the knowledge base."
            )

        store = cls()

        store.index = index

        store.dimension = index.d

        store.chunks = chunks

        return store