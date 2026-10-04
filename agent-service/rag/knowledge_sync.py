"""将系统健康知识文章（tb_knowledge 已发布）同步进 Milvus。

增量策略：
    - 按内容 hash 判断是否变化；未变化跳过
    - 变化 -> 先删旧分片主键，再写入新分片
    - 文章消失 -> 按记录的分片主键删除
"""
import os
import json
import hashlib
from typing import List, Dict, Optional, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.config_handler import milvus_conf
from utils.path_tool import get_abs_path
from utils.logger_handler import logger
from rag.vector_store import VectorStoreService

STATE_PATH = get_abs_path(os.path.join("data", "sync_state.json"))


def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"articles": {}}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("articles", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"articles": {}}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


class KnowledgeSyncService:
    def __init__(self, vector_service: Optional[VectorStoreService] = None):
        self.vector_service = vector_service or VectorStoreService()
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=milvus_conf.get("chunk_size", 1000),
            chunk_overlap=milvus_conf.get("chunk_overlap", 80),
            separators=milvus_conf.get("separators"),
            length_function=len,
        )

    def _split(self, article: dict) -> Tuple[List[str], List[dict], List[str]]:
        article_id = str(article.get("id"))
        title = (article.get("title") or "").strip()
        author = (article.get("author") or "").strip()
        introduction = (article.get("introduction") or "").strip()
        content = (article.get("content") or "").strip()

        full_text = content
        if introduction and introduction not in content:
            full_text = f"{introduction}\n{content}"

        chunks = self.spliter.split_text(full_text) if full_text else []
        texts, metadatas, ids = [], [], []
        for i, chunk in enumerate(chunks):
            if not chunk or not chunk.strip():
                continue
            texts.append(chunk)
            metadatas.append({
                "article_id": article_id,
                "title": title,
                "author": author,
                "source": "tb_knowledge",
                "chunk_index": i,
            })
            ids.append(f"{article_id}_{i}")
        return texts, metadatas, ids

    def sync_articles(self, articles: List[dict]) -> dict:
        state = _load_state()
        old_articles: Dict[str, dict] = state.get("articles", {})
        stats = {"total": len(articles), "inserted": 0, "updated": 0, "deleted": 0, "skipped": 0}
        seen_ids = set()

        for article in articles:
            if article.get("id") is None:
                continue
            article_id = str(article["id"])
            content = (article.get("content") or "").strip()
            if not content or len(content) < 10:
                stats["skipped"] += 1
                seen_ids.add(article_id)
                continue

            seen_ids.add(article_id)
            new_hash = _content_hash(content)
            old = old_articles.get(article_id)
            if old and old.get("hash") == new_hash:
                stats["skipped"] += 1
                continue

            if old and old.get("chunk_ids"):
                self.vector_service.delete_ids(old["chunk_ids"])

            texts, metadatas, ids = self._split(article)
            if texts:
                self.vector_service.add_texts(texts=texts, metadatas=metadatas, ids=ids)

            old_articles[article_id] = {"hash": new_hash, "chunk_ids": ids}
            if old:
                stats["updated"] += 1
            else:
                stats["inserted"] += 1

        for article_id in list(old_articles.keys()):
            if article_id not in seen_ids:
                old = old_articles.pop(article_id)
                if old.get("chunk_ids"):
                    self.vector_service.delete_ids(old["chunk_ids"])
                stats["deleted"] += 1

        state["articles"] = old_articles
        _save_state(state)
        logger.info("知识库同步完成：%s", stats)
        return stats
