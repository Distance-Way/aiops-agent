import json

from app import db
from app.rag import LocalHashEmbedder, RagService, chunk_text, cosine_similarity


def test_embedder_similar_texts_are_similar():
    embedder = LocalHashEmbedder()
    first = embedder.embed("磁盘满了，需要清理日志")
    second = embedder.embed("磁盘空间不足，清理历史日志")
    different = embedder.embed("Python FastAPI 数据库连接池")
    assert cosine_similarity(first, second) > cosine_similarity(first, different)


def test_chunk_text_creates_overlapping_chunks():
    text = ("这是排障内容。\n" * 30) + "结尾"
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) >= 3
    assert "".join(chunks).startswith("这是排障内容")


def test_rag_ingest_search_and_delete():
    db.reset_db()
    service = RagService()
    document = service.ingest_document(
        "runbook.md",
        "当磁盘满时先执行 df -h。\n检查日志目录使用情况。",
    )
    assert document.chunk_count >= 1

    hits = service.search("磁盘满 怎么检查")
    assert hits
    assert "df -h" in hits[0].content

    db.delete_document(document.id)
    assert service.search("磁盘满 怎么检查") == []
