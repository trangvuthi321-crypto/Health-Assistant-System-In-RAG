from typing import List

from langchain_milvus import Milvus

from utils.config_handler import milvus_conf
from model.factory import embed_model


class VectorStoreService:
    """健康知识向量库（由系统 tb_knowledge 已发布文章同步而来）。"""

    def __init__(self):
        self.vector_store = Milvus(
            collection_name=milvus_conf["collection_name"],
            embedding_function=embed_model,
            connection_args={"uri": milvus_conf["uri"]},
            text_field="text",
            vector_field="vector",
            auto_id=False,
            enable_dynamic_field=True,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": milvus_conf["k"]})

    def add_texts(self, texts: List[str], metadatas: List[dict], ids: List[str]) -> List[str]:
        return self.vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def delete_ids(self, ids: List[str]) -> None:
        if ids:
            self.vector_store.delete(ids=ids)
