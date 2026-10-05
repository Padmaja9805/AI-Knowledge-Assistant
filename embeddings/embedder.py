import numpy as np

from config.settings import settings


EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384
EMBEDDING_ID = f"huggingface-inference:{EMBEDDING_MODEL}:normalized-v1"
EMBEDDING_BATCH_SIZE = 32


class Embedder:
    def __init__(self, client=None):
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not settings.HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN is not configured. Set it to use Hugging Face "
                "embeddings and answer generation."
            )

        from huggingface_hub import InferenceClient

        self._client = InferenceClient(
            api_key=settings.HF_TOKEN,
            provider="hf-inference",
        )
        return self._client

    def embed(self, text):
        vectors = self.embed_many([text])
        return vectors[0]

    def embed_many(self, texts):
        if not texts:
            return np.empty((0, EMBEDDING_DIMENSION), dtype=np.float32)
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Embedding input must contain non-empty text.")

        client = self._get_client()
        batches = []
        for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            text_batch = texts[start:start + EMBEDDING_BATCH_SIZE]
            try:
                response = client.feature_extraction(
                    text_batch,
                    model=EMBEDDING_MODEL,
                    normalize=True,
                )
            except Exception as error:
                raise RuntimeError(
                    "Hugging Face embedding request failed. Check that "
                    "HF_TOKEN is valid and the embedding provider is available."
                ) from error

            vectors = np.asarray(response, dtype=np.float32)
            if vectors.ndim == 1 and len(text_batch) == 1:
                vectors = vectors.reshape(1, -1)
            if vectors.shape != (len(text_batch), EMBEDDING_DIMENSION):
                raise RuntimeError(
                    "Hugging Face returned embeddings with shape "
                    f"{vectors.shape}; expected "
                    f"({len(text_batch)}, {EMBEDDING_DIMENSION})."
                )

            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise RuntimeError(
                    "Hugging Face returned an empty embedding vector."
                )
            batches.append(vectors / norms)

        return np.vstack(batches).astype(np.float32, copy=False)
