import unittest

from rag.rag_pipeline import OUT_OF_SCOPE_ANSWER, RAGPipeline


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(text)
        return [1.0, 0.0]


class FakeLLM:
    def __init__(self, answer="Grounded answer."):
        self.answer_text = answer
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.answer_text


class FakeVectorStore:
    def __init__(self, chunks):
        self.chunks = chunks
        self.search_calls = 0

    def search(self, query_vector, top_k, min_score):
        self.search_calls += 1
        return [
            {"chunk": chunk, "score": chunk.get("score", 0.8)}
            for chunk in self.chunks[:top_k]
            if chunk.get("score", 0.8) >= min_score
        ]


def chunk(source, chunk_id=0, text="Evidence from this document."):
    return {
        "source": source,
        "chunk_id": chunk_id,
        "text": text,
        "score": 0.8,
    }


class RAGPipelineTests(unittest.TestCase):
    def make_pipeline(self, chunks, answer="Grounded answer."):
        llm = FakeLLM(answer)
        pipeline = RAGPipeline(
            embedder=FakeEmbedder(),
            llm=llm,
            vector_store=FakeVectorStore(chunks),
        )
        return pipeline, llm

    def test_week_number_selects_task_number_filename(self):
        pipeline, _ = self.make_pipeline([
            chunk("TASK 1 REPORT.pdf"),
            chunk("TASK 3 REPORT.pdf", 1),
        ])
        self.assertEqual(
            pipeline._requested_source("Tell me about the week 3 report document"),
            "TASK 3 REPORT.pdf",
        )

    def test_ordinal_task_matches_report(self):
        pipeline, _ = self.make_pipeline([
            chunk("TASK 3 REPORT.pdf"),
        ])
        self.assertEqual(
            pipeline._requested_source("Tell me about the 3rd task"),
            "TASK 3 REPORT.pdf",
        )

    def test_second_number_in_multiweek_filename_is_matchable(self):
        pipeline, _ = self.make_pipeline([
            chunk("WEEK 7 & 8.pdf"),
        ])
        self.assertEqual(
            pipeline._requested_source("What happened in week 8?"),
            "WEEK 7 & 8.pdf",
        )

    def test_single_report_overview_selects_its_document(self):
        pipeline, _ = self.make_pipeline([
            chunk("Annual Report.pdf"),
        ])
        self.assertEqual(
            pipeline._requested_source("Explain the report"),
            "Annual Report.pdf",
        )

    def test_unavailable_numbered_report_is_not_substituted_with_another(self):
        pipeline, llm = self.make_pipeline([
            chunk("TASK 3 REPORT.pdf"),
        ])
        result = pipeline.answer(
            "Tell me about task 4 report",
            recent_questions=["Tell me about task 3 report"],
        )
        self.assertIn("couldn't find an uploaded document", result["answer"])
        self.assertEqual(result["sources"], [])
        self.assertEqual(llm.prompts, [])

    def test_semantic_question_searches_all_documents(self):
        pipeline, llm = self.make_pipeline([
            chunk("TASK 1 REPORT.pdf", text="Nmap scanned a host."),
            chunk("TASK 3 REPORT.pdf", 1, text="Nmap found open ports."),
        ])
        result = pipeline.answer("What did Nmap find?")
        self.assertEqual(result["answer"], "Grounded answer.")
        self.assertEqual(len(result["sources"]), 2)
        self.assertIn("Nmap found open ports.", llm.prompts[0])
        self.assertIn("What did Nmap find?", llm.prompts[0])

    def test_specific_document_limits_retrieved_sources(self):
        pipeline, _ = self.make_pipeline([
            chunk("TASK 1 REPORT.pdf"),
            chunk("TASK 3 REPORT.pdf", 1),
        ])
        result = pipeline.answer("What happened in week 3?")
        self.assertEqual(
            {source["source"] for source in result["sources"]},
            {"TASK 3 REPORT.pdf"},
        )

    def test_no_relevant_chunks_returns_out_of_scope_without_llm_call(self):
        pipeline, llm = self.make_pipeline([
            {**chunk("TASK 3 REPORT.pdf"), "score": 0.0},
        ])
        result = pipeline.answer("What is quantum computing?")
        self.assertEqual(result, {"answer": OUT_OF_SCOPE_ANSWER, "sources": []})
        self.assertEqual(llm.prompts, [])

    def test_empty_knowledge_base_is_explicit(self):
        pipeline, llm = self.make_pipeline([])
        result = pipeline.answer("What happened?")
        self.assertIn("no indexed documents", result["answer"].lower())
        self.assertEqual(result["sources"], [])
        self.assertEqual(llm.prompts, [])

    def test_source_metadata_contains_similarity_and_excerpt(self):
        pipeline, _ = self.make_pipeline([
            chunk("TASK 3 REPORT.pdf", text="Only this passage is evidence."),
        ])
        result = pipeline.answer("What is in the report?")
        self.assertEqual(result["sources"][0]["score"], 0.8)
        self.assertEqual(
            result["sources"][0]["text"],
            "Only this passage is evidence.",
        )

    def test_lexical_match_recovers_exact_terms_below_similarity_threshold(self):
        passage = chunk(
            "TASK 3 REPORT.pdf",
            text="Kali Linux and Metasploitable machines were used in the exercise.",
        )
        passage["score"] = 0.1
        pipeline, _ = self.make_pipeline([passage])

        result = pipeline.answer("What machines were used in the exercise?")

        self.assertEqual(result["sources"][0]["chunk_id"], 0)
        self.assertIn("Metasploitable", result["sources"][0]["text"])

    def test_report_overview_samples_each_matching_report(self):
        chunks = [
            chunk("TASK 3 REPORT.pdf", index, f"Task 3 section {index}")
            for index in range(5)
        ] + [
            chunk("TASK 5 REPORT.pdf", index, f"Task 5 section {index}")
            for index in range(5)
        ]
        pipeline, _ = self.make_pipeline(chunks)

        result = pipeline.answer("Summarize the entire report.")

        self.assertEqual(
            {source["source"] for source in result["sources"]},
            {"TASK 3 REPORT.pdf", "TASK 5 REPORT.pdf"},
        )

    def test_followup_points_from_both_uses_both_recently_named_documents(self):
        chunks = [
            chunk("TASK 3 REPORT.pdf", index, f"Task 3 section {index}")
            for index in range(4)
        ] + [
            chunk("TASK 4 REPORT.pdf", index, f"Task 4 section {index}")
            for index in range(4)
        ]
        pipeline, llm = self.make_pipeline(chunks)

        result = pipeline.answer(
            "Key points from both the document",
            recent_questions=[
                "Explain about the task 3 report",
                "Can you tell me about the task 4 report?",
            ],
        )

        self.assertEqual(
            {source["source"] for source in result["sources"]},
            {"TASK 3 REPORT.pdf", "TASK 4 REPORT.pdf"},
        )
        self.assertIn("Task 3 section", llm.prompts[0])
        self.assertIn("Task 4 section", llm.prompts[0])

    def test_uploaded_document_question_lists_indexed_sources(self):
        chunks = [
            chunk("TASK 3 REPORT.pdf"),
            chunk("TASK 4 REPORT.pdf", 1),
        ]
        embedder = FakeEmbedder()
        store = FakeVectorStore(chunks)
        llm = FakeLLM()
        pipeline = RAGPipeline(
            embedder=embedder,
            llm=llm,
            vector_store=store,
        )

        result = pipeline.answer("What are the documents uploaded?")

        self.assertEqual(
            result["answer"],
            "You have 2 documents uploaded:\n\n"
            "1. TASK 3 REPORT.pdf\n"
            "2. TASK 4 REPORT.pdf",
        )
        self.assertEqual(result["sources"], [])
        self.assertEqual(embedder.calls, [])
        self.assertEqual(store.search_calls, 0)
        self.assertEqual(llm.prompts, [])

    def test_inventory_question_patterns_are_direct_metadata_requests(self):
        questions = (
            "What documents are uploaded?",
            "How many documents are uploaded?",
            "List my documents",
            "What files do I have?",
            "Show uploaded files",
            "Which reports are available?",
            "How many PDFs are there?",
        )
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(
                    RAGPipeline._asks_for_document_inventory(question)
                )

    def test_pdf_count_only_counts_unique_pdf_sources(self):
        embedder = FakeEmbedder()
        store = FakeVectorStore([
            chunk("TASK 3 REPORT.pdf", 0),
            chunk("TASK 3 REPORT.pdf", 1),
            chunk("TASK 4 REPORT.pdf", 2),
            chunk("NOTES.txt", 3),
        ])
        llm = FakeLLM()
        pipeline = RAGPipeline(
            embedder=embedder,
            llm=llm,
            vector_store=store,
        )

        result = pipeline.answer("How many PDFs are there?")

        self.assertEqual(
            result["answer"],
            "You have 2 PDFs uploaded:\n\n"
            "1. TASK 3 REPORT.pdf\n"
            "2. TASK 4 REPORT.pdf",
        )
        self.assertEqual(result["sources"], [])
        self.assertEqual(embedder.calls, [])
        self.assertEqual(store.search_calls, 0)
        self.assertEqual(llm.prompts, [])

    def test_report_inventory_only_lists_report_filenames(self):
        pipeline, llm = self.make_pipeline([
            chunk("TASK 3 REPORT.pdf"),
            chunk("meeting-notes.txt", 1),
        ])

        result = pipeline.answer("Which reports are available?")

        self.assertEqual(
            result["answer"],
            "You have 1 report uploaded:\n\n1. TASK 3 REPORT.pdf",
        )
        self.assertEqual(result["sources"], [])
        self.assertEqual(llm.prompts, [])

    def test_indexed_document_metadata_is_unique_and_name_only(self):
        pipeline, _ = self.make_pipeline([
            chunk("TASK 3 REPORT.pdf", 0),
            chunk("TASK 3 REPORT.pdf", 1),
            chunk("TASK 4 REPORT.pdf", 2),
        ])

        self.assertEqual(
            pipeline.indexed_documents(),
            [
                {"name": "TASK 3 REPORT.pdf"},
                {"name": "TASK 4 REPORT.pdf"},
            ],
        )

    def test_content_question_about_report_is_not_inventory(self):
        self.assertFalse(
            RAGPipeline._asks_for_document_inventory(
                "What is in the report?"
            )
        )


if __name__ == "__main__":
    unittest.main()
