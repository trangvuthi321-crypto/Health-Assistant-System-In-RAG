"""
配置加载：yaml + 环境变量（.env）
"""
import os

import yaml
from dotenv import load_dotenv

from utils.path_tool import get_abs_path

# 加载 .env：本目录优先，其次仓库根目录
load_dotenv(get_abs_path(".env"))
load_dotenv(os.path.join(os.path.dirname(get_abs_path("")), ".env"))


def load_rag_config(config_path: str = get_abs_path("config/rag.yaml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_milvus_config(config_path: str = get_abs_path("config/milvus.yaml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_prompts_config(config_path: str = get_abs_path("config/prompts.yaml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def load_agent_config(config_path: str = get_abs_path("config/agent.yaml"), encoding: str = "utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


rag_conf = load_rag_config()
milvus_conf = load_milvus_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()
