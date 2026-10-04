"""健康助手的工具集（ReAct Agent 可调用）。"""
import datetime

from langchain_core.tools import tool
from langchain.tools import ToolRuntime

from rag.rag_service import get_rag_service
from utils.db_handler import list_olders as db_list_olders
from utils.db_handler import fetch_health_record as db_fetch_health_record
from utils.logger_handler import logger


def _ctx_user_id(runtime) -> str:
    ctx = getattr(runtime, "context", None)
    if ctx is None:
        return ""
    if isinstance(ctx, dict):
        return str(ctx.get("user_id", "") or "")
    return str(getattr(ctx, "user_id", "") or "")


@tool(description="从健康知识向量库中检索与query最相关的健康知识参考资料，以字符串返回")
def rag_summary(query: str) -> str:
    return get_rag_service().rag_summary(query)


@tool(description="获取系统当前月份，返回 YYYY-MM 格式字符串")
def get_current_month() -> str:
    return datetime.date.today().strftime("%Y-%m")


@tool(description="获取当前登录用户的ID，以纯字符串返回")
def get_user_id(runtime: ToolRuntime) -> str:
    return _ctx_user_id(runtime)


@tool(description="查询系统中的老人列表（含老人ID、姓名、年龄、性别、病史），用于确定要生成谁的健康报告")
def list_olders(runtime: ToolRuntime) -> str:
    return db_list_olders(_ctx_user_id(runtime))


@tool(description="查询指定老人(older_id)在指定月份(month，YYYY-MM)的健康档案与内科体检指标，以字符串返回")
def fetch_health_record(older_id: str, month: str) -> str:
    try:
        return db_fetch_health_record(older_id, month)
    except Exception as e:  # noqa: BLE001
        logger.error("查询健康档案失败：%s", e)
        return f"查询健康档案失败：{e}"


@tool(description="生成/查询老人健康报告前必须调用，无入参、无返回，用于触发报告生成模式")
def fill_context_for_report() -> str:
    return "fill_context_for_report工具已被调用"


tool_list = [
    rag_summary,
    get_current_month,
    get_user_id,
    list_olders,
    fetch_health_record,
    fill_context_for_report,
]
