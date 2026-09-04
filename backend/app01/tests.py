import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings

from app01.models import Person, Project, RagChatMessage, RagChatSession
from app01.services.rag_resilience_service import (
    check_rag_chat_admission,
    is_circuit_allowed,
    record_component_failure,
    record_component_success,
    release_rag_chat_admission,
)


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rag-resilience-tests",
    }
}


@override_settings(
    EMBEDDING_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1',
    EMBEDDING_MODEL='qwen3.7-text-embedding',
    EMBEDDING_API_KEY='dashscope-test-key',
    EMBEDDING_BATCH_SIZE=8,
    EMBEDDING_TIMEOUT=60,
)
class DashScopeEmbeddingConfigTests(SimpleTestCase):
    def test_embedding_client_uses_dashscope_api_key_and_model(self):
        from app01.services.rag import embeddings as embeddings_module

        with patch.object(embeddings_module, 'OpenAI') as openai_cls:
            embeddings = embeddings_module.DashScopeTextEmbeddings()

        self.assertEqual(embeddings.model, 'qwen3.7-text-embedding')
        _, kwargs = openai_cls.call_args
        self.assertEqual(kwargs['api_key'], 'dashscope-test-key')
        self.assertEqual(kwargs['base_url'], 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.assertEqual(kwargs['timeout'], 60)


class RagKeywordIndexFallbackTests(SimpleTestCase):
    @override_settings(RAG_KEYWORD_INDEX_REQUIRED=False)
    def test_optional_keyword_index_failure_does_not_break_vector_index_flow(self):
        from app01.services.rag.vector_store import _run_keyword_index_operation

        result = _run_keyword_index_operation(lambda: (_ for _ in ()).throw(RuntimeError('ES unavailable')))

        self.assertTrue(result['skipped'])
        self.assertEqual(result['error_type'], 'RuntimeError')
        self.assertIn('Elasticsearch', result['message'])

    @override_settings(RAG_KEYWORD_INDEX_REQUIRED=True)
    def test_required_keyword_index_failure_is_raised(self):
        from app01.services.rag.vector_store import _run_keyword_index_operation

        with self.assertRaises(RuntimeError):
            _run_keyword_index_operation(lambda: (_ for _ in ()).throw(RuntimeError('ES unavailable')))


@override_settings(
    RAG_SEMANTIC_CHUNKING_ENABLED=True,
    EMBEDDING_API_KEY='semantic-test-key',
    RAG_SEMANTIC_CHUNKING_SIMILARITY_THRESHOLD=0.62,
    RAG_SEMANTIC_CHUNKING_SHORT_MERGE_MIN_SIMILARITY=0.5,
    RAG_SEMANTIC_CHUNKING_TARGET_CHARS=900,
    RAG_SEMANTIC_CHUNKING_MAX_CHUNK_CHARS=1400,
)
class RagSemanticChunkingTests(SimpleTestCase):
    class FakeEmbeddings:
        def __init__(self, vectors):
            self.vectors = vectors
            self.seen_texts = []

        def embed_documents(self, texts):
            self.seen_texts.extend(texts)
            return self.vectors[:len(texts)]

    def make_doc(self, text, order, block_type='paragraph_semantic', section_path=None):
        from langchain_core.documents import Document

        section_path = section_path or ['工程概况']
        return Document(
            page_content=text,
            metadata={
                'file_id': 1,
                'order': order,
                'block_type': block_type,
                'section_path': section_path,
                'section_title': section_path[-1] if section_path else None,
            },
        )

    def test_heading_document_forces_an_independent_chunk(self):
        from app01.services.rag.semantic_chunking import semantic_merge_documents

        docs = [
            self.make_doc('一、工程概况', 0, block_type='title'),
            self.make_doc('本工程位于城市主干路沿线。', 1),
            self.make_doc('建设内容包括候车亭基础和钢结构。', 2),
        ]

        merged = semantic_merge_documents(
            docs,
            embeddings=self.FakeEmbeddings([[1, 0], [0.99, 0.01]]),
        )

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].metadata['block_type'], 'title')
        self.assertEqual(merged[0].metadata['semantic_split_reason'], 'heading')
        self.assertEqual(merged[0].metadata['source_block_count'], 1)
        self.assertEqual(merged[1].metadata['source_block_count'], 2)

    def test_table_document_stays_independent_and_is_not_embedded_for_merging(self):
        from app01.services.rag.semantic_chunking import semantic_merge_documents

        fake_embeddings = self.FakeEmbeddings([[1, 0], [0.9, 0.1]])
        table_text = '| 名称 | 数量 |\n| --- | --- |\n| 候车亭 | 10 |'
        docs = [
            self.make_doc('候车亭采购范围包括基础施工。', 0),
            self.make_doc(table_text, 1, block_type='table'),
            self.make_doc('安装完成后需要组织验收。', 2),
        ]

        merged = semantic_merge_documents(docs, embeddings=fake_embeddings)

        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[1].metadata['block_type'], 'table')
        self.assertEqual(merged[1].metadata['semantic_split_reason'], 'table')
        self.assertEqual(merged[1].metadata['source_block_count'], 1)
        self.assertNotIn(table_text, fake_embeddings.seen_texts)

    def test_low_similarity_splits_adjacent_paragraphs(self):
        from app01.services.rag.semantic_chunking import semantic_merge_documents

        docs = [
            self.make_doc('项目位于市政道路沿线。', 0),
            self.make_doc('建设内容包括候车亭基础和钢结构。', 1),
            self.make_doc('安全检查应重点关注临边防护。', 2),
        ]

        merged = semantic_merge_documents(
            docs,
            embeddings=self.FakeEmbeddings([[1, 0], [0.99, 0.01], [0, 1]]),
        )

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].metadata['source_block_count'], 2)
        self.assertEqual(merged[0].metadata['semantic_split_reason'], 'low_similarity')
        self.assertEqual(merged[1].metadata['source_block_count'], 1)

    def test_recursive_splitter_preserves_semantic_metadata_for_long_chunks(self):
        from langchain_core.documents import Document
        from app01.services.rag.splitters import split_documents

        long_text = '工程质量检查需要形成闭环记录。' * 180
        document = Document(
            page_content=long_text,
            metadata={
                'file_id': 1,
                'block_type': 'paragraph_semantic',
                'section_title': '质量管理',
                'section_path': ['质量管理'],
                'semantic_group_id': 'group-1',
                'semantic_score': 0.88,
                'semantic_split_reason': 'target_chars',
                'source_block_count': 3,
            },
        )

        chunks = split_documents([document])

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertEqual(chunk.metadata['semantic_group_id'], 'group-1')
            self.assertEqual(chunk.metadata['section_title'], '质量管理')
            self.assertEqual(chunk.metadata['source_block_count'], 3)
            self.assertIn('chunk_index', chunk.metadata)

    def test_pdf_heading_enrichment_updates_following_section_metadata(self):
        from app01.services.rag.blocks import enrich_block_sections, make_block

        base_metadata = {
            'file_id': 1,
            'file_name': '示例.pdf',
            'project_id': 1,
            'project_name': '测试项目',
            'file_extension': '.pdf',
        }
        blocks = [
            make_block('1 工程概况', 'pdf_title', base_metadata, 0, page=1),
            make_block('本项目包含公交候车亭基础施工。', 'pdf_paragraph', base_metadata, 1, page=1),
            make_block('1.1 安全检查', 'pdf_title', base_metadata, 2, page=2),
            make_block('安全检查包括临边防护和用电检查。', 'pdf_paragraph', base_metadata, 3, page=2),
        ]

        enriched = enrich_block_sections(blocks)

        self.assertEqual(enriched[1]['section_title'], '1 工程概况')
        self.assertEqual(enriched[1]['section_path'], ['1 工程概况'])
        self.assertEqual(enriched[3]['section_title'], '1.1 安全检查')
        self.assertEqual(enriched[3]['section_path'], ['1 工程概况', '1.1 安全检查'])


@override_settings(
    CACHES=TEST_CACHES,
    RAG_CHAT_RATE_LIMIT_ENABLED=True,
    RAG_CHAT_RATE_WINDOW_SECONDS=60,
    RAG_CHAT_USER_RATE_LIMIT_PER_MINUTE=2,
    RAG_CHAT_PROJECT_RATE_LIMIT_PER_MINUTE=100,
    RAG_CHAT_GLOBAL_RATE_LIMIT_PER_MINUTE=100,
    RAG_CHAT_USER_MAX_IN_FLIGHT=100,
    RAG_CHAT_GLOBAL_MAX_IN_FLIGHT=100,
    RAG_CIRCUIT_BREAKER_ENABLED=True,
    RAG_CHAT_MODEL_CIRCUIT_FAILURE_THRESHOLD=2,
    RAG_CHAT_MODEL_CIRCUIT_OPEN_SECONDS=60,
)
class RagResilienceServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_user_rate_limit_blocks_excess_requests(self):
        first = check_rag_chat_admission(user_id=1, project_id=10)
        second = check_rag_chat_admission(user_id=1, project_id=10)
        third = check_rag_chat_admission(user_id=1, project_id=10)

        self.assertTrue(first.allowed)
        self.assertTrue(second.allowed)
        self.assertFalse(third.allowed)
        self.assertEqual(third.status_code, 429)

        release_rag_chat_admission(first)
        release_rag_chat_admission(second)

    @override_settings(
        RAG_CHAT_USER_RATE_LIMIT_PER_MINUTE=100,
        RAG_CHAT_USER_MAX_IN_FLIGHT=1,
        RAG_CHAT_GLOBAL_MAX_IN_FLIGHT=100,
    )
    def test_in_flight_slot_is_released_after_streaming(self):
        first = check_rag_chat_admission(user_id=2, project_id=10)
        second = check_rag_chat_admission(user_id=2, project_id=10)

        self.assertTrue(first.allowed)
        self.assertFalse(second.allowed)

        release_rag_chat_admission(first)
        third = check_rag_chat_admission(user_id=2, project_id=10)

        self.assertTrue(third.allowed)
        release_rag_chat_admission(third)

    def test_chat_model_circuit_opens_after_repeated_failures(self):
        self.assertTrue(is_circuit_allowed("chat_model"))

        record_component_failure("chat_model", RuntimeError("first"))
        self.assertTrue(is_circuit_allowed("chat_model"))

        record_component_failure("chat_model", RuntimeError("second"))
        self.assertFalse(is_circuit_allowed("chat_model"))

        record_component_success("chat_model")
        self.assertTrue(is_circuit_allowed("chat_model"))


@override_settings(
    CACHES=TEST_CACHES,
    RAG_CHAT_API_KEY="test-key",
    RAG_MULTI_QUERY_ENABLED=True,
    RAG_MULTI_QUERY_COUNT=3,
    RAG_MULTI_QUERY_RECALL_LIMIT=2,
    RAG_CIRCUIT_BREAKER_ENABLED=False,
    RAG_RERANK_API_KEY="",
)
class RagMultiQueryTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_generate_multi_search_queries_keeps_original_and_deduplicates(self):
        from app01.services.langchain_rag_service import generate_multi_search_queries

        class FakeMessage:
            content = "1. 安全整改措施有哪些\n- 质量风险整改要求\n安全整改措施有哪些\n成本风险处理建议"

        class FakeChoice:
            message = FakeMessage()

        class FakeCompletions:
            def create(self, **kwargs):
                return type("FakeResponse", (), {"choices": [FakeChoice()]})()

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            chat = FakeChat()

        with patch("app01.services.langchain_rag_service.get_chat_client", return_value=FakeClient()):
            queries = generate_multi_search_queries("安全问题怎么处理？")

        self.assertEqual(queries[0], "安全问题怎么处理？")
        self.assertEqual(len(queries), 4)
        self.assertIn("安全整改措施有哪些", queries)
        self.assertEqual(len(queries), len(set(queries)))

    def test_hybrid_search_runs_vector_and_keyword_for_each_query_then_reranks_once(self):
        from app01.services.langchain_rag_service import hybrid_search_file_chunks

        vector_questions = []
        keyword_questions = []
        rerank_calls = []

        def fake_vector(question, project_id=None, limit=5):
            vector_questions.append((question, project_id, limit))
            return [{
                "file_id": 1,
                "chunk_index": 1 if question == "主查询" else 2,
                "score": 0.9,
                "text": f"{question} 向量结果",
            }]

        def fake_keyword(query, project_id=None, limit=20):
            keyword_questions.append((query, project_id, limit))
            return [{
                "file_id": 1,
                "chunk_index": 1,
                "score": 12.0,
                "text": f"{query} 关键词结果",
            }]

        def fake_rerank(question, search_results, top_k=8):
            rerank_calls.append((question, len(search_results), top_k))
            return search_results[:top_k]

        with patch("app01.services.langchain_rag_service.generate_multi_search_queries", return_value=["主查询", "扩展查询"]):
            with patch("app01.services.langchain_rag_service.search_file_chunks_langchain", side_effect=fake_vector):
                with patch("app01.services.langchain_rag_service.keyword_search_file_chunks", side_effect=fake_keyword):
                    with patch("app01.services.langchain_rag_service.rerank_search_results_with_model", side_effect=fake_rerank):
                        results = hybrid_search_file_chunks("主查询", project_id=7, final_limit=5)

        self.assertEqual(vector_questions, [("主查询", 7, 2), ("扩展查询", 7, 2)])
        self.assertEqual(keyword_questions, [("主查询", 7, 2), ("扩展查询", 7, 2)])
        self.assertEqual(rerank_calls, [("主查询", 2, 5)])
        self.assertTrue(results)
        self.assertIn("retrieval_sources", results[0])
        self.assertTrue(any(source.get("query_index") == 2 for item in results for source in item["retrieval_sources"]))


@override_settings(
    RAG_CONTEXT_COMPRESSION_ENABLED=True,
    RAG_CONTEXT_COMPRESSION_CANDIDATE_LIMIT=8,
    RAG_CONTEXT_COMPRESSION_MIN_KEEP_ITEMS=2,
    RAG_CONTEXT_COMPRESSION_MAX_ITEM_CHARS=120,
    RAG_CONTEXT_COMPRESSION_MAX_SENTENCES=2,
    RAG_CONTEXT_COMPRESSION_SENTENCE_WINDOW=0,
    RAG_CONTEXT_COMPRESSION_DROP_UNMATCHED_AFTER_MIN_KEEP=False,
    RAG_LLM_CONTEXT_COMPRESSION_ENABLED=False,
)
class RagContextCompressionTests(SimpleTestCase):
    def test_contextual_compression_extracts_query_related_sentences(self):
        from app01.services.langchain_rag_service import compress_context_text_by_query

        text = (
            "项目成本计划已经完成，预算执行情况整体稳定。"
            "成本台账、合同付款和材料采购计划已经完成复核。"
            "本段还记录了预算偏差、供应商付款节点和月度成本分析。"
            "安全整改措施包括临边防护复查、脚手架验收和夜间巡检。"
            "质量验收资料由质量员在月底统一归档。"
            "质量检查表、材料报验单和隐蔽工程记录需要按批次整理。"
        )

        compressed_text, metadata = compress_context_text_by_query(text, "安全整改措施有哪些？")

        self.assertIn("安全整改措施", compressed_text)
        self.assertNotIn("项目成本计划", compressed_text)
        self.assertTrue(metadata["matched"])
        self.assertTrue(metadata["compressed"])

    def test_rule_contextual_compression_keeps_fallback_candidates_conservatively(self):
        from app01.services.langchain_rag_service import contextual_compress_search_results

        long_irrelevant_text = "成本计划说明。" * 80
        long_relevant_text = (
            "质量检查记录。" * 20
            + "安全整改措施包括临边防护复查和脚手架验收。"
            + "成本计划说明。" * 20
        )
        search_results = [
            {
                "file_id": 1,
                "chunk_index": 1,
                "score": 0.9,
                "text": long_relevant_text,
            },
            {
                "file_id": 1,
                "chunk_index": 2,
                "score": 0.8,
                "text": long_irrelevant_text,
            },
            {
                "file_id": 1,
                "chunk_index": 3,
                "score": 0.7,
                "text": long_irrelevant_text,
            },
        ]

        compressed_results = contextual_compress_search_results(search_results, "安全整改措施有哪些？")

        self.assertEqual(len(compressed_results), 3)
        self.assertIn("安全整改措施", compressed_results[0]["text"])
        self.assertLess(len(compressed_results[0]["text"]), len(long_relevant_text))
        self.assertTrue(compressed_results[0]["contextual_compressed"])
        self.assertTrue(compressed_results[1]["contextual_compression_fallback_kept"])


@override_settings(
    CACHES=TEST_CACHES,
    RAG_CHAT_API_KEY="test-key",
    RAG_CONTEXT_COMPRESSION_ENABLED=True,
    RAG_CONTEXT_COMPRESSION_CANDIDATE_LIMIT=8,
    RAG_CONTEXT_COMPRESSION_MIN_KEEP_ITEMS=2,
    RAG_CONTEXT_COMPRESSION_MAX_ITEM_CHARS=500,
    RAG_CONTEXT_COMPRESSION_DROP_UNMATCHED_AFTER_MIN_KEEP=False,
    RAG_LLM_CONTEXT_COMPRESSION_ENABLED=True,
    RAG_LLM_CONTEXT_COMPRESSION_MODEL="qwen-compress-test",
    RAG_LLM_CONTEXT_COMPRESSION_CANDIDATE_LIMIT=2,
    RAG_LLM_CONTEXT_COMPRESSION_MIN_ITEM_CHARS=20,
    RAG_LLM_CONTEXT_COMPRESSION_MAX_ITEM_CHARS=80,
    RAG_CIRCUIT_BREAKER_ENABLED=False,
)
class RagLlmContextCompressionTests(SimpleTestCase):
    def test_llm_contextual_compression_refines_rule_results(self):
        from app01.services.langchain_rag_service import contextual_compress_search_results

        class FakeMessage:
            content = json.dumps([
                {
                    "index": 1,
                    "keep": True,
                    "compressed_text": "安全整改措施包括临边防护复查和脚手架验收。",
                },
                {
                    "index": 2,
                    "keep": False,
                    "compressed_text": "",
                },
            ], ensure_ascii=False)

        class FakeChoice:
            message = FakeMessage()

        class FakeCompletions:
            def create(self, **kwargs):
                self.last_kwargs = kwargs
                return type("FakeResponse", (), {"choices": [FakeChoice()]})()

        fake_completions = FakeCompletions()

        class FakeChat:
            completions = fake_completions

        class FakeClient:
            chat = FakeChat()

        search_results = [
            {
                "file_id": 1,
                "chunk_index": 1,
                "score": 0.9,
                "text": "质量检查记录。" * 20 + "安全整改措施包括临边防护复查和脚手架验收。" + "成本说明。" * 20,
            },
            {
                "file_id": 1,
                "chunk_index": 2,
                "score": 0.8,
                "text": "成本计划说明。" * 40,
            },
            {
                "file_id": 1,
                "chunk_index": 3,
                "score": 0.7,
                "text": "进度计划说明。" * 40,
            },
        ]

        with patch("app01.services.langchain_rag_service.get_chat_client", return_value=FakeClient()):
            compressed_results = contextual_compress_search_results(search_results, "安全整改措施有哪些？")

        self.assertEqual(fake_completions.last_kwargs["model"], "qwen-compress-test")
        self.assertEqual(fake_completions.last_kwargs["max_tokens"], 1600)
        self.assertEqual(compressed_results[0]["text"], "安全整改措施包括临边防护复查和脚手架验收。")
        self.assertTrue(compressed_results[0]["llm_contextual_compressed"])
        self.assertTrue(compressed_results[1]["llm_contextual_compression_fallback_kept"])


class RagTokenBudgetSettingsTests(SimpleTestCase):
    def test_rag_llm_token_budgets_are_configured_conservatively(self):
        from django.conf import settings

        self.assertEqual(settings.RAG_MULTI_QUERY_MAX_TOKENS, 384)
        self.assertEqual(settings.RAG_LLM_CONTEXT_COMPRESSION_MAX_TOKENS, 1600)
        self.assertEqual(settings.RAG_CHAT_MAX_TOKENS, 2400)
        self.assertEqual(settings.RAG_CHAT_MEMORY_SUMMARY_MAX_TOKENS, 1800)
        self.assertEqual(settings.RAG_CHAT_QUERY_REWRITE_MAX_TOKENS, 512)
        self.assertEqual(settings.RAGAS_EVAL_MAX_TOKENS, 4096)


@override_settings(
    CACHES=TEST_CACHES,
    RAG_CHAT_RATE_LIMIT_ENABLED=False,
    RAG_CIRCUIT_BREAKER_ENABLED=False,
    RAG_CHAT_HISTORY_MAX_MESSAGES=10,
    RAG_CHAT_RECENT_MESSAGES=10,
    RAG_CHAT_SUMMARY_MAX_MESSAGES=70,
    RAG_CHAT_SUMMARY_TRIGGER_MESSAGES=10,
    RAG_CHAT_SUMMARY_UPDATE_INTERVAL_MESSAGES=4,
)
class RagChatSessionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="rag_user", password="testpass123")
        self.person = Person.objects.create(
            user=self.user,
            NAME_Person="测试用户",
            NUM_Person="P001",
            MAIL_Person="rag@example.com",
            POS_Person="成员",
            sys_role="member",
        )
        self.project = Project.objects.create(
            NUM_Project="PJ001",
            NAME_Project="测试项目",
            TYPE_Project="房建",
            VALUE_Project="100",
            START_Project="2026-01-01",
            END_Project="2026-12-31",
            ADDRESS_Project="上海",
            DESC_Project="测试项目描述",
            MANA_Project="测试经理",
            CUR_Project="CNY",
        )
        self.project.ID_Person.add(self.person)
        self.client.login(username="rag_user", password="testpass123")

    def _read_stream_events(self, response):
        payload = b"".join(response.streaming_content).decode("utf-8")
        return [
            json.loads(line)
            for line in payload.splitlines()
            if line.strip()
        ]

    def test_rag_chat_creates_session_and_reuses_database_history(self):
        captured_history = []

        def fake_answer_question_with_rag(question, project_id=None, limit=8, history=None, history_summary=''):
            captured_history.append(history or [])
            yield {"type": "delta", "content": f"回答：{question}"}
            yield {"type": "done", "sources": []}

        with patch("app01.views.answer_question_with_rag", side_effect=fake_answer_question_with_rag):
            first_response = self.client.post(
                f"/projects/{self.project.pk}/rag/chat/",
                data=json.dumps({"question": "这份文件主要讲什么？"}),
                content_type="application/json",
            )
            first_events = self._read_stream_events(first_response)

            self.assertEqual(first_response.status_code, 200)
            session_id = first_events[0]["session_id"]
            self.assertEqual(RagChatSession.objects.count(), 1)
            self.assertEqual(RagChatMessage.objects.count(), 2)

            second_response = self.client.post(
                f"/projects/{self.project.pk}/rag/chat/",
                data=json.dumps({"question": "它有哪些风险点？", "session_id": session_id}),
                content_type="application/json",
            )
            self._read_stream_events(second_response)

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(RagChatSession.objects.count(), 1)
        self.assertEqual(RagChatMessage.objects.count(), 4)
        self.assertEqual(captured_history[0], [])
        self.assertEqual(
            captured_history[1],
            [
                {"role": "user", "content": "这份文件主要讲什么？"},
                {"role": "assistant", "content": "回答：这份文件主要讲什么？"},
            ],
        )

    def test_can_list_session_messages(self):
        session = RagChatSession.objects.create(
            project=self.project,
            owner=self.person,
            title="测试会话",
        )
        RagChatMessage.objects.create(session=session, role="user", content="第一问")
        RagChatMessage.objects.create(session=session, role="assistant", content="第一答")

        response = self.client.get(f"/projects/{self.project.pk}/rag/sessions/{session.pk}/messages/")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["session"]["session_id"], session.pk)
        self.assertEqual(len(data["messages"]), 2)

    def test_can_delete_owned_rag_session(self):
        session = RagChatSession.objects.create(
            project=self.project,
            owner=self.person,
            title="待删除会话",
        )
        RagChatMessage.objects.create(session=session, role="user", content="第一问")

        response = self.client.delete(f"/projects/{self.project.pk}/rag/sessions/{session.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(RagChatSession.objects.filter(pk=session.pk).exists())
        self.assertEqual(RagChatMessage.objects.count(), 0)

    def test_rag_memory_keeps_recent_messages_and_summarizes_older_messages(self):
        from app01.views import get_rag_memory_context, maybe_update_rag_session_summary

        session = RagChatSession.objects.create(
            project=self.project,
            owner=self.person,
            title="长对话",
        )
        for index in range(40):
            RagChatMessage.objects.create(session=session, role="user", content=f"第{index + 1}问")
            RagChatMessage.objects.create(session=session, role="assistant", content=f"第{index + 1}答")

        def fake_summary(history, previous_summary=''):
            return f"摘要覆盖{len(history)}条消息：{history[0]['content']} 到 {history[-1]['content']}"

        with patch("app01.views.summarize_chat_history_for_memory", side_effect=fake_summary):
            maybe_update_rag_session_summary(session)

        session.refresh_from_db()
        history_summary, recent_history = get_rag_memory_context(session)

        self.assertIn("摘要覆盖70条消息", history_summary)
        self.assertEqual(session.summarized_message_count, 80)
        self.assertEqual(len(recent_history), 10)
        self.assertEqual(recent_history[0], {"role": "user", "content": "第36问"})
        self.assertEqual(recent_history[-1], {"role": "assistant", "content": "第40答"})
