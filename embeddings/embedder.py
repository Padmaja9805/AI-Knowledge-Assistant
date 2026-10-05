from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _load_model():
    return SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )


class Embedder:

    def __init__(self):
        self.model = _load_model()

    def embed(self, text):

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