from utils.logger_handler import logger
from utils.config_handler import prompts_conf
from utils.path_tool import get_abs_path


def _read(key: str) -> str:
    try:
        path = get_abs_path(prompts_conf[key])
    except KeyError as e:
        logger.error(f"[prompt_loader]缺少配置项 {key}")
        raise e
    try:
        return open(path, "r", encoding="utf-8").read()
    except FileNotFoundError as e:
        logger.error(f"[prompt_loader]提示词文件不存在：{path}，{e}")
        raise e


def load_system_prompt() -> str:
    return _read("main_prompt_path")


def load_rag_prompt() -> str:
    return _read("rag_summarize_prompt_path")


def load_report_prompt() -> str:
    return _read("report_prompt_path")
