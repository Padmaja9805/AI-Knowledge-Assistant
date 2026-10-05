from pathlib import Path
import re

from pypdf import PdfReader
from docx import Document


def load_text_file(file_path):

    path = Path(file_path)

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def load_pdf(file_path):

    reader = PdfReader(file_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def load_docx(file_path):

    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n\n".join(paragraphs)


def clean_text(text):

    # Replace repeated spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def load_document(file_path):

    path = Path(file_path)

    extension = path.suffix.lower()

    if extension == ".txt":
        text = load_text_file(file_path)

    elif extension == ".pdf":
        text = load_pdf(file_path)

    elif extension == ".docx":
        text = load_docx(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    return clean_text(text)