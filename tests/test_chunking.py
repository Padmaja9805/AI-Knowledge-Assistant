from document_ai.chunker import create_chunks
import unittest


class ChunkingTests(unittest.TestCase):

    def test_chunks_are_limited_and_overlap(self):
        text = " ".join(
            f"word{index}"
            for index in range(350)
        )

        chunks = create_chunks(
            text,
            chunk_size=1000,
            chunk_overlap=200,
            source="sample.txt"
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(
            all(len(chunk["text"]) <= 1000 for chunk in chunks)
        )
        overlaps = []
        for index in range(len(chunks) - 1):
            left = chunks[index]["text"]
            right = chunks[index + 1]["text"]
            overlap_size = min(len(left), len(right))
            while (
                overlap_size > 0
                and left[-overlap_size:] != right[:overlap_size]
            ):
                overlap_size -= 1
            overlaps.append(overlap_size)
        self.assertTrue(any(overlap >= 180 for overlap in overlaps))
        self.assertTrue(
            all(chunk["source"] == "sample.txt" for chunk in chunks)
        )

    def test_default_chunk_size_and_overlap(self):
        text = " ".join(
            f"word{index}"
            for index in range(350)
        )
        chunks = create_chunks(text)

        self.assertTrue(
            all(len(chunk["text"]) <= 1000 for chunk in chunks)
        )
        self.assertTrue(
            any(
                set(chunks[index]["text"].split())
                & set(chunks[index + 1]["text"].split())
                for index in range(len(chunks) - 1)
            )
        )

    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            create_chunks("sample text", chunk_size=100, chunk_overlap=100)


if __name__ == "__main__":
    unittest.main()