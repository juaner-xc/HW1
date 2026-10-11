"""一个最小但完整的 ReAct 风格代码审查 Agent。"""
from __future__ import annotations

import json
import re
from typing import Protocol

from llm import OpenAICompatibleLLM
from tools import CodeTools, ToolError


class ChatModel(Protocol):
    async def chat(self, messages: list[dict[str, str]]) -> str: ...


AGENT_PROMPT = """你是中文代码审查 Agent。用户要求审查、解释或找 Bug 时，必须先用 read_file 读取涉及的本地文件，再依据文件内容回答；未读取文件时不能假装看过代码。

每次只能返回一个 JSON 对象，不能使用 Markdown：
1. 调用工具：{"action":{"name":"read_file","arguments":{"path":"相对路径"}}}
2. 最终回答：{"final":"简洁的中文审查结论，说明问题、影响和建议"}

工具观察结果会在下一轮提供。最多使用 3 轮工具调用。"""


class CodeReviewAgent:
    def __init__(self, model: ChatModel, tools: CodeTools, max_steps: int = 3) -> None:
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    async def run(self, user_input: str, history: list[dict[str, str]] | None = None) -> str:
        messages = [
            {
                "role": "system",
                "content": AGENT_PROMPT + "\n可用工具：" + json.dumps(self.tools.schema(), ensure_ascii=False),
            }
        ]
        messages.extend((history or [])[-6:])
        messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_steps):
            raw = await self.model.chat(messages)
            decision = self._parse(raw)
            final = decision.get("final")
            if isinstance(final, str) and final.strip():
                return final.strip()

            action = decision.get("action")
            if not isinstance(action, dict):
                return "模型没有给出可执行的代码审查结果，请重试。"
            name = str(action.get("name") or "")
            arguments = action.get("arguments")
            try:
                observation = self.tools.call(name, arguments if isinstance(arguments, dict) else {})
            except ToolError as exc:
                observation = f"工具错误：{exc}"
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": f"工具 {name} 的观察结果：\n{observation}\n请继续，只返回 JSON。",
                }
            )

        return "已达到本次工具调用上限，请指定更具体的文件。"

    @staticmethod
    def _parse(raw: str) -> dict[str, object]:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"模型没有返回合法 JSON：{raw[:120]}") from exc
        if not isinstance(value, dict):
            raise ValueError("模型 JSON 必须是对象")
        return value
