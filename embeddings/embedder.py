from functools import lru_cache

import numpy as np


@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )


class Embedder:

    def __init__(self):
        self.model = None

    def embed(self, text):
        if self.model is None:
            self.model = _load_model()

        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return np.asarray(
            vector,
            dtype="float32"
        )