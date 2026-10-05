from pathlib import Path
import shutil

from document_ai.indexer import DocumentIndexer
from vector_store.faiss_store import FAISSVectorStore


UPLOAD_FOLDER = Path("uploads")
VECTOR_FOLDER = Path("vector_data")

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx"
}


class DocumentManager:

    def __init__(self):

        self.indexer = DocumentIndexer()

        UPLOAD_FOLDER.mkdir(
            exist_ok=True
        )

    # ------------------------------------------
    # LIST DOCUMENTS
    # ------------------------------------------

    def list_documents(self):

        documents = []

        for file_path in UPLOAD_FOLDER.iterdir():

            if not file_path.is_file():
                continue

            if (
                file_path.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):
                continue

            documents.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size
            })

        return documents

    # ------------------------------------------
    # CHECK DOCUMENT
    # ------------------------------------------

    def document_exists(self, filename):

        if Path(filename).name != filename:
            return False

        file_path = UPLOAD_FOLDER / filename

        return file_path.exists()

    # ------------------------------------------
    # DELETE DOCUMENT
    # ------------------------------------------

    def delete_document(self, filename):

        if Path(filename).name != filename:
            raise FileNotFoundError("Document not found.")

        file_path = UPLOAD_FOLDER / filename

        if not file_path.exists():

            raise FileNotFoundError(
                "Document not found."
            )

        file_path.unlink()

        return self.rebuild_index()

    # ------------------------------------------
    # REINDEX DOCUMENT
    # ------------------------------------------

    def reindex_document(self, filename):

        if Path(filename).name != filename:
            raise FileNotFoundError("Document not found.")

        file_path = UPLOAD_FOLDER / filename

        if not file_path.exists():

            raise FileNotFoundError(
                "Document not found."
            )

        return self.rebuild_index()

    # ------------------------------------------
    # REBUILD COMPLETE VECTOR INDEX
    # ------------------------------------------

    def rebuild_index(self):

        documents = []

        for file_path in UPLOAD_FOLDER.iterdir():

            if not file_path.is_file():
                continue

            if (
                file_path.suffix.lower()
                not in SUPPORTED_EXTENSIONS
            ):
                continue

            documents.append(file_path)

        # ------------------------------------------
        # NO DOCUMENTS
        # ------------------------------------------

        if not documents:

            if VECTOR_FOLDER.exists():

                shutil.rmtree(
                    VECTOR_FOLDER
                )

            return {
                "documents": 0,
                "chunks": 0
            }

        # ------------------------------------------
        # CREATE EMPTY VECTOR STORE
        # ------------------------------------------

        store = FAISSVectorStore.create()

        total_chunks = 0

        # ------------------------------------------
        # INDEX EACH DOCUMENT
        # ------------------------------------------

        for file_path in documents:

            result = (
                self.indexer
                .index_document_into_store(
                    file_path,
                    file_path.name,
                    store
                )
            )

            if result is None:

                raise RuntimeError(
                    "Document indexing returned no result."
                )

            total_chunks += result[
                "chunks_added"
            ]

        # ------------------------------------------
        # SAVE VECTOR STORE
        # ------------------------------------------

        store.save(
            str(VECTOR_FOLDER)
        )

        return {
            "documents": len(documents),
            "chunks": total_chunks
        }