import hashlib
import json
import math
import re
import uuid
from dataclasses import dataclass

from app import db
from app.config import settings
from app.schemas import SearchHit


class LocalHashEmbedder:
    """Deterministic local embedding used for the no-dependency MVP."""

    DIM = 192

    def _features(self, text: str) -> list[str]:
        lower = text.lower()
        tokens = re.findall(r"[\u4e00-\u9fff]|[a-z0-9]+", lower)
        chinese_chars = [token for token in tokens if "\u4e00" <= token <= "\u9fff"]
        features = list(tokens)
        for index in range(len(chinese_chars) - 1):
            features.append(chinese_chars[index] + chinese_chars[index + 1])
        return features

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.DIM
        for feature in self._features(text):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % self.DIM
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 8) for value in vector]


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 60) -> list[str]:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(
                text.rfind("\n", start + 1, end),
                text.rfind("。", start + 1, end),
                text.rfind(" ", start + 1, end),
            )
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        next_start = max(start + 1, end - overlap)
        if next_start <= start:
            break
        start = next_start
    return chunks


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    return float(dot)


@dataclass
class RagDocument:
    id: str
    name: str
    size: int
    chunk_count: int
    created_at: str


class RagService:
    def __init__(self, embedder: LocalHashEmbedder | None = None):
        self.embedder = embedder or LocalHashEmbedder()

    def ingest_document(self, name: str, content: str) -> RagDocument:
        doc_id = uuid.uuid4().hex[:12]
        db.add_document(doc_id, name, len(content.encode("utf-8")))
        chunks = chunk_text(
            content,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        rows = []
        for index, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}:{index}"
            vector = self.embedder.embed(chunk)
            rows.append((chunk_id, doc_id, index, chunk, json.dumps(vector)))
        db.add_chunks(rows)
        return RagDocument(
            id=doc_id,
            name=name,
            size=len(content.encode("utf-8")),
            chunk_count=len(rows),
            created_at=db.utc_now(),
        )

    def search(self, query: str, top_k: int = 3) -> list[SearchHit]:
        rows = db.list_chunks()
        if not rows:
            return []
        query_vector = self.embedder.embed(query)
        scored: list[tuple[float, SearchHit]] = []
        for row in rows:
            vector = json.loads(row["vector"])
            score = cosine_similarity(query_vector, vector)
            scored.append(
                (
                    score,
                    SearchHit(
                        chunk_id=row["chunk_id"],
                        document_id=row["document_id"],
                        document_name=row["document_name"],
                        position=row["position"],
                        content=row["content"],
                        score=round(score, 5),
                    ),
                )
            )
        scored.sort(key=lambda item: item[0], reverse=True)
        return [hit for _, hit in scored[:top_k]]
