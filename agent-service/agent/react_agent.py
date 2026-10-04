from langchain.agents import create_agent

from model.factory import chat_model
from utils.prompt_loader import load_system_prompt
from agent.tools.agent_tools import tool_list
from agent.tools.middleware import middleware_list


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompt(),
            tools=[*tool_list],
            middleware=[*middleware_list],
        )

    def execute(self, query: str, user_id: str = "") -> str:
        """执行一次问答，返回最终回答（非流式）。"""
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            context={"user_id": user_id, "report": False},
        )
        return self._final_text(result)

    @staticmethod
    def _final_text(result) -> str:
        messages = result.get("messages", []) if isinstance(result, dict) else []
        for message in reversed(messages):
            if getattr(message, "type", "") != "ai":
                continue
            content = getattr(message, "content", "")
            if isinstance(content, list):
                text = "".join(
                    block.get("text", "") for block in content if isinstance(block, dict)
                )
                if text.strip():
                    return text
            elif content and str(content).strip():
                return str(content)
        return "抱歉，暂时无法回答，请稍后再试。"
