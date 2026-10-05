from pathlib import Path
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from config.settings import settings
from document_ai.indexer import DocumentIndexer
from document_ai.manager import DocumentManager
from rag.rag_pipeline import RAGPipeline
from utils.logger import get_logger
from vector_store.faiss_store import (
    FAISSVectorStore,
    IncompatibleEmbeddingError,
)


logger = get_logger(__name__)
UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}

app = FastAPI(
    title="AI Knowledge Assistant",
    description="Document question answering with retrieval-augmented generation.",
    version="1.0.0",
)

document_indexer = DocumentIndexer()
document_manager = DocumentManager()
rag_pipeline = RAGPipeline()


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    recent_questions: list[str] = Field(default_factory=list, max_length=8)


@app.get("/")
def home():
    return {"message": "AI Knowledge Assistant API is running", "status": "healthy"}


@app.get("/health")
def health():
    documents = document_manager.list_documents()
    return {
        "status": "healthy",
        "llm": bool(settings.HF_TOKEN),
        "vector_store": rag_pipeline.vector_store is not None,
        "documents": len(documents),
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")

    try:
        result = rag_pipeline.answer(
            question,
            recent_questions=request.recent_questions,
        )
        return {
            "answer": result["answer"],
            "sources": result["sources"],
        }
    except Exception as error:
        logger.exception("Question answering failed.")
        raise HTTPException(
            status_code=503,
            detail=f"Question answering failed: {error}",
        ) from error


@app.post("/upload")
def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload TXT, PDF, or DOCX.",
        )

    file_path = UPLOAD_FOLDER / filename
    if file_path.exists():
        raise HTTPException(
            status_code=409,
            detail="This document already exists in the knowledge base.",
        )

    try:
        with file_path.open("wb") as saved_file:
            shutil.copyfileobj(file.file, saved_file)

        try:
            result = document_indexer.index_document(file_path, filename)
        except IncompatibleEmbeddingError:
            logger.info(
                "Existing FAISS index uses a different embedding method; "
                "rebuilding it from all uploaded documents."
            )
            document_manager.rebuild_index()
            store = FAISSVectorStore.load()
            result = {
                "chunks_added": sum(
                    chunk.get("source") == filename
                    for chunk in store.chunks
                ),
                "source": filename,
            }
        if not result:
            raise RuntimeError("Document indexing returned no result.")

        rag_pipeline.refresh()
        logger.info(
            "Indexed document %s with %d chunks.",
            filename,
            result["chunks_added"],
        )
        return {
            "message": "Document uploaded and indexed successfully.",
            "filename": filename,
            "chunks_added": result["chunks_added"],
        }
    except Exception as error:
        logger.exception("Document upload or indexing failed: %s", filename)
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload and index the document: {error}",
        ) from error


@app.get("/documents")
def get_documents():
    try:
        documents = rag_pipeline.indexed_documents()
        return {"documents": documents, "count": len(documents)}
    except Exception as error:
        logger.exception("Document listing failed.")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {error}",
        ) from error


@app.delete("/documents/{filename}")
def delete_document(filename: str):
    try:
        result = document_manager.delete_document(filename)
        rag_pipeline.refresh()
        return {
            "message": "Document deleted successfully.",
            "filename": filename,
            "rebuild": result,
        }
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Document not found.") from error
    except Exception as error:
        logger.exception("Document deletion failed: %s", filename)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {error}",
        ) from error


@app.post("/documents/{filename}/reindex")
def reindex_document(filename: str):
    try:
        result = document_manager.reindex_document(filename)
        rag_pipeline.refresh()
        return {
            "message": "Knowledge base re-indexed successfully.",
            "filename": filename,
            "documents": result["documents"],
            "chunks": result["chunks"],
        }
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Document not found.") from error
    except Exception as error:
        logger.exception("Document re-indexing failed: %s", filename)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-index documents: {error}",
        ) from error
