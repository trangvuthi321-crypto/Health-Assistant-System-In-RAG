# 社区老人健康管理系统 · 健康助手（Health Agent Assistant System）

基于 SpringBoot + Vue 的社区老人健康管理系统，集成基于 **ReAct Agent + 向量检索** 的"健康助手"：
既能回答老年人健康知识问题，也能读取系统健康档案生成"老人健康报告"。

## 架构

```
Vue (frontend, :8080)
   │  axios  http://localhost:9001
   ▼
SpringBoot (backend, :9001) ── MyBatis ──▶ MySQL (communitypension)
   │  HTTP  /assistant/*
   ▼
FastAPI Agent (agent-service, :8000)
   ├─ ReAct Agent（LangChain create_agent）+ 工具 + 中间件
   ├─ Milvus (:19530) 健康知识库  ◀── 由系统已发布文章同步
   ├─ 兼容 OpenAI 协议模型服务（对话 + 向量化）
   └─ 只读查询 MySQL：tb_older / tb_healthyfiles / tb_internal（生成报告）
```

- 知识来源：`tb_knowledge` 中已发布（`style='1'`）的文章，管理员点"同步知识库"写入 Milvus
- 对话：Vue → 后端 → Agent（自主调用工具）→ 返回最终回答（非流式、每轮独立）
- 报告：Agent 识别"生成健康报告"意图后，先 `fill_context_for_report` 切换报告提示词，再查档案与内科指标生成报告

## 目录结构

```
Health-Agent-Assistant-System/
├── backend/        # SpringBoot + MyBatis 后端
├── frontend/       # Vue2 + element-ui 前端
├── agent-service/  # Python FastAPI 健康助手 Agent 服务
│   ├── api_server.py
│   ├── agent/      # react_agent、tools（agent_tools/middleware）
│   ├── rag/        # rag_service、vector_store、knowledge_sync
│   ├── model/      # 模型工厂
│   ├── utils/      # config/db/logger/path/prompt
│   ├── config/  prompts/
│   └── requirements.txt  .env.example
├── sql/            # communitypension.sql、assistant_menu.sql
├── .env.example
└── README.md
```

## 环境要求

- JDK 1.8、Maven 3.6+
- Node.js 14+（Vue CLI 4 项目）
- Python 3.10+、可访问的 Milvus（`localhost:19530`）
- MySQL 5.7/8.0
- 兼容 OpenAI 协议的模型服务（对话 + 向量）

## 快速开始

### 1. 数据库

```bash
mysql -uroot -p < sql/communitypension.sql
mysql -uroot -p < sql/assistant_menu.sql      # 添加"健康助手"菜单
```

### 2. 后端

```bash
# Windows PowerShell
$env:DB_USERNAME="root"; $env:DB_PASSWORD="你的密码"
# 可选：$env:SERVICE_TOKEN="abc123"; $env:ASSISTANT_BASE_URL="http://127.0.0.1:8000"

cd backend
mvn spring-boot:run          # :9001
```

### 3. 健康助手 Agent 服务

```bash
cd agent-service
pip install -r requirements.txt
# 在本目录或仓库根目录创建 .env（参考 .env.example）：OPENAI_API_KEY / DB_PASSWORD / SERVICE_TOKEN
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000
```

验证：`http://127.0.0.1:8000/assistant/health` → `{"status":"ok",...}`。

### 4. 前端

```bash
cd frontend
npm install
npm run serve                # :8080
```

### 5. 使用

1. 登录系统 →「健康知识推荐」→ 点击 **同步知识库**，把已发布文章写入向量库。
2. 打开「健康助手」菜单：
   - 知识问答：如"老年人高血压饮食要注意什么？"
   - 生成报告：如"生成徐老 2022-03 的健康报告"（助手会先列出老人、切换报告模式，再输出报告）

## 配置说明

| 变量 | 作用 | 所属 |
|---|---|---|
| `OPENAI_API_KEY` | 模型/向量服务密钥 | agent-service |
| `SERVICE_TOKEN` | Java↔Python 共享口令，留空不校验 | backend / agent-service |
| `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` | 报告工具只读访问数据库 | agent-service |
| `ASSISTANT_BASE_URL` | Python 服务地址，默认 `http://127.0.0.1:8000` | backend |
| `DB_URL/DB_USERNAME/DB_PASSWORD` | 后端数据库连接 | backend |

## 说明

- 向量集合为 `health_knowledge`，仅由本服务读写；同步为增量策略（内容哈希判断，删除/取消发布时回收向量）。
- 对话每轮独立、无多轮记忆；仅返回最终回答，不向前端暴露思考过程。
- 报告数据来自 `tb_older`（基本信息/病史）、`tb_healthyfiles`（档案）、`tb_internal`（内科指标，经 `healthy_Id` 关联）。
- `.env` 含密钥，已被 `.gitignore` 忽略，请勿提交。
