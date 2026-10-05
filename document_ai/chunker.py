def create_chunks(
    text,
    chunk_size=1000,
    chunk_overlap=200,
    source="unknown",
):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be between zero and chunk_size - 1."
        )

    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    boundaries = ("\n\n", "\n", ". ", " ")

    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            minimum_boundary = int(chunk_size * 0.6)
            for separator in boundaries:
                position = window.rfind(separator)
                if position >= minimum_boundary:
                    end = start + position + len(separator)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break
        start = max(start + 1, end - chunk_overlap)
        while start < len(text) and text[start].isspace():
            start += 1

    return [
        {"text": chunk, "source": source, "chunk_id": chunk_id}
        for chunk_id, chunk in enumerate(chunks)
    ]
