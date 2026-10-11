"""命令行入口：python cli.py \"审查 examples/buggy.py\""""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent import CodeReviewAgent
from llm import ModelError, OpenAICompatibleLLM
from tools import CodeTools


async def main() -> None:
    load_dotenv()
    request = " ".join(sys.argv[1:]).strip()
    if not request:
        print('用法：python cli.py "审查 examples/buggy.py"')
        return

    model = OpenAICompatibleLLM(
        os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        os.getenv("LLM_API_KEY", ""),
        os.getenv("LLM_MODEL", "deepseek-chat"),
    )
    workspace = Path(os.getenv("CODE_AGENT_WORKSPACE", ".")).resolve()
    agent = CodeReviewAgent(model, CodeTools(workspace))
    try:
        print(await agent.run(request))
    except (ModelError, ValueError) as exc:
        print(f"执行失败：{exc}")


if __name__ == "__main__":
    asyncio.run(main())
