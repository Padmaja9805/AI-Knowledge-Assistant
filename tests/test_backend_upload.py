import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi import UploadFile

from backend import main
from vector_store.faiss_store import IncompatibleEmbeddingError


class UploadRouteTests(unittest.TestCase):
    def test_upload_rebuilds_incompatible_index_before_adding_new_vectors(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            indexer = Mock()
            indexer.index_document.side_effect = IncompatibleEmbeddingError(
                "Embedding metadata is missing."
            )
            manager = Mock()
            store = Mock()
            store.chunks = [
                {"source": "existing.txt"},
                {"source": "new.txt"},
                {"source": "new.txt"},
            ]
            pipeline = Mock()
            upload = UploadFile(
                filename="new.txt",
                file=BytesIO(b"new document"),
            )

            with (
                patch.object(
                    main,
                    "UPLOAD_FOLDER",
                    Path(temporary_directory),
                ),
                patch.object(main, "document_indexer", indexer),
                patch.object(main, "document_manager", manager),
                patch.object(main, "rag_pipeline", pipeline),
                patch.object(main.FAISSVectorStore, "load", return_value=store),
            ):
                result = main.upload_document(upload)

            self.assertEqual(result["filename"], "new.txt")
            self.assertEqual(result["chunks_added"], 2)
            manager.rebuild_index.assert_called_once_with()
            pipeline.refresh.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
