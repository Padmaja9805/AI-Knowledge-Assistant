import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from embeddings.embedder import EMBEDDING_DIMENSION
from vector_store.faiss_store import (
    FAISSVectorStore,
    IncompatibleEmbeddingError,
)


class FAISSVectorStoreTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [{
            "source": "sample.txt",
            "chunk_id": 0,
            "text": "A sample passage.",
        }]
        self.vectors = np.zeros((1, EMBEDDING_DIMENSION), dtype=np.float32)
        self.vectors[0, 0] = 1.0

    def test_saved_vectors_load_and_retrieve_with_embedding_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = FAISSVectorStore.create()
            store.add(self.vectors, self.chunks)
            store.save(temporary_directory)

            loaded = FAISSVectorStore.load(temporary_directory)
            results = loaded.search(self.vectors[0], top_k=1)

        self.assertEqual(results[0]["chunk"]["source"], "sample.txt")
        self.assertAlmostEqual(results[0]["score"], 1.0)

    def test_legacy_chunk_list_requires_a_full_reindex(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = FAISSVectorStore.create()
            store.add(self.vectors, self.chunks)
            store.save(temporary_directory)
            chunks_file = Path(temporary_directory) / "chunks.json"
            chunks_file.write_text(
                json.dumps(self.chunks),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                IncompatibleEmbeddingError,
                "Re-index all uploaded documents",
            ):
                FAISSVectorStore.load(temporary_directory)

    def test_add_rejects_a_different_vector_dimension(self):
        store = FAISSVectorStore.create()
        with self.assertRaisesRegex(ValueError, "dimensions"):
            store.add([[1.0, 0.0]], self.chunks)


if __name__ == "__main__":
    unittest.main()
