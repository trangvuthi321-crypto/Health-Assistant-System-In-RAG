"""社区老人健康管理系统 - 健康助手服务（FastAPI）。

供 SpringBoot 调用：
    GET  /assistant/health
    POST /assistant/chat   {message, user_id, session_id} -> {code,status,answer}
    POST /assistant/sync   {articles:[...]} -> 同步统计

启动：
    uvicorn api_server:app --host 127.0.0.1 --port 8000
"""
import logging
import os
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.config_handler import milvus_conf  # noqa: F401  触发 .env 加载

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_assistant")

SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

app = FastAPI(title="Health Assistant Agent Service")


# ---------------------------------------------------------------------------
# 单例：避免每次请求重建 Agent / 向量库连接
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def get_agent():
    from agent.react_agent import ReactAgent
    return ReactAgent()


@lru_cache(maxsize=1)
def get_sync_service():
    from rag.knowledge_sync import KnowledgeSyncService
    return KnowledgeSyncService()


@app.on_event("startup")
def warmup():
    try:
        get_agent()
        get_sync_service()
        logger.info("健康助手服务预热完成，知识库集合=%s", milvus_conf.get("collection_name"))
    except Exception as e:  # noqa: BLE001
        logger.warning("服务预热失败（后续请求会重试）：%s", e)


def check_token(x_service_token: str = Header(default="")):
    if SERVICE_TOKEN and x_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="invalid service token")


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    user_id: str = ""
    session_id: str = "default"


class Article(BaseModel):
    id: int
    title: Optional[str] = None
    author: Optional[str] = None
    introduction: Optional[str] = None
    content: Optional[str] = None


class SyncRequest(BaseModel):
    articles: List[Article] = []


# ---------------------------------------------------------------------------
# 端点
# ---------------------------------------------------------------------------
@app.get("/assistant/health")
def health():
    return {"status": "ok", "collection": milvus_conf.get("collection_name")}


@app.post("/assistant/chat")
def chat(req: ChatRequest, request: Request):
    check_token(request.headers.get("x-service-token", ""))
    question = (req.message or "").strip()
    if not question:
        return {"code": 400, "status": "error", "message": "message 不能为空", "answer": ""}
    try:
        answer = get_agent().execute(question, req.user_id or "")
        return {"code": 200, "status": "success", "answer": answer}
    except Exception as e:  # noqa: BLE001
        logger.exception("chat 处理失败")
        return {"code": 500, "status": "error", "message": str(e), "answer": ""}


@app.post("/assistant/sync")
def sync(req: SyncRequest, request: Request):
    check_token(request.headers.get("x-service-token", ""))
    try:
        stats = get_sync_service().sync_articles([a.model_dump() for a in req.articles])
        return {"code": 200, "status": "success", **stats}
    except Exception as e:  # noqa: BLE001
        logger.exception("sync 处理失败")
        return {"code": 500, "status": "error", "message": str(e)}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常：%s", exc)
    return JSONResponse(status_code=200, content={
        "code": 500, "status": "error", "message": str(exc), "answer": ""
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
