from pathlib import Path

from document_ai.loader import load_document
from document_ai.chunker import create_chunks
from embeddings.embedder import Embedder
from vector_store.faiss_store import FAISSVectorStore


VECTOR_FOLDER = "vector_data"


class DocumentIndexer:

    def __init__(self, embedder=None):
        self.embedder = embedder

    def prepare_document(
        self,
        file_path,
        source
    ):

        text = load_document(file_path)

        if not text.strip():

            raise ValueError(
                "The document contains no readable text."
            )

        chunks = create_chunks(
            text,
            source=source
        )

        if not chunks:

            raise ValueError(
                "No chunks were created."
            )

        if self.embedder is None:
            self.embedder = Embedder()

        vectors = []
        for chunk in chunks:

            vector = self.embedder.embed(
                chunk["text"]
            )

            vectors.append(vector)

        return vectors, chunks

    def index_document(
        self,
        file_path,
        source
    ):

        vectors, chunks = self.prepare_document(
            file_path,
            source
        )

        index_file = Path(
            VECTOR_FOLDER
        ) / "index.faiss"

        chunks_file = Path(
            VECTOR_FOLDER
        ) / "chunks.json"


        # ------------------------------------------
        # LOAD EXISTING STORE OR CREATE NEW STORE
        # ------------------------------------------

        if index_file.exists() != chunks_file.exists():
            raise RuntimeError(
                "The FAISS index and chunk metadata are incomplete. "
                "Rebuild the knowledge base before adding documents."
            )

        if index_file.exists():
            store = FAISSVectorStore.load(
                VECTOR_FOLDER
            )

        else:

            store = FAISSVectorStore.create()


        # ------------------------------------------
        # ADD DOCUMENT
        # ------------------------------------------

        store.add(
            vectors,
            chunks
        )


        # ------------------------------------------
        # SAVE VECTOR DATABASE
        # ------------------------------------------

        store.save(
            VECTOR_FOLDER
        )


        return {
            "chunks_added":
                len(chunks),

            "source":
                source
        }

    def index_document_into_store(
        self,
        file_path,
        source,
        store
    ):

        vectors, chunks = self.prepare_document(
            file_path,
            source
        )

        store.add(
            vectors,
            chunks
        )

        return {
            "chunks_added":
                len(chunks),

            "source":
                source
        }