"""RAG 总结服务：检索健康知识 -> 结合提问交给模型总结回答。"""
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompt
from model.factory import chat_model


class RagSummaryService(object):
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_template = PromptTemplate.from_template(load_rag_prompt())
        self.chain = self.prompt_template | chat_model | StrOutputParser()

    def retrieve_docs(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)

    def rag_summary(self, query: str) -> str:
        context = ""
        for counter, doc in enumerate(self.retrieve_docs(query), start=1):
            context += f"【参考资料{counter}】: {doc.page_content} | 参考元数据：{doc.metadata}\n"
        return self.chain.invoke({"input": query, "context": context})


@lru_cache(maxsize=1)
def get_rag_service() -> RagSummaryService:
    """单例，避免每次工具调用都重建向量库连接。"""
    return RagSummaryService()
