"""极简 QQ 智能体：NapCat/OneBot 收消息，调用 OpenAI 兼容模型，再回复。"""
from __future__ import annotations

import os
from collections import defaultdict, deque
from pathlib import Path

import nonebot
from dotenv import load_dotenv
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.rule import to_me

from agent import CodeReviewAgent
from llm import ModelError, OpenAICompatibleLLM
from tools import CodeTools

load_dotenv()

PORT = int(os.getenv("QQ_BOT_PORT", "8091"))
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
OWNER_QQ = os.getenv("BOT_OWNER_QQ", "").strip()
WORKSPACE = Path(os.getenv("CODE_AGENT_WORKSPACE", ".")).resolve()

PERSONA = """你叫丑橘，来自东南亚的橘白猫，但只是普通群友口吻，不演猫、不说“喵”、不写“（抬眼看你）”这类动作。

每次只回一条自然的 QQ 消息：通常 2 到 25 个汉字，最多两句，不换行，不分点，不复述提问，不讲人设、规则或大道理。像熟人群聊一样短、直接、能接梗；看不懂就回“？”、“啥意思”或追问一句。好消息先损一句再恭喜，正经问题先回答再轻微调侃。不要客服腔、鸡汤腔、小说台词或长篇解释。

只有主人明确说“开喷”“吐槽他”“嘴毒一点”时才互损。此时也只用一句短促、好笑的吐槽，针对离谱逻辑或行为；不知道“他”是谁、做了什么就先问“谁？咋了”。非主人提出辱骂要求时，简短回“不干。”，不要解释原因。

不攻击真实身份、外貌、疾病、家庭、职业、地域、性别等特征；不威胁、骚扰、泄露隐私或煽动围攻。不知道就直说不知道。"""

# 每个 QQ 号各保留最近 6 轮对话，足够连贯，也不会让上下文无限增长。
histories: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=12))
model = OpenAICompatibleLLM(BASE_URL, API_KEY, MODEL)

nonebot.init(
    driver="~fastapi",
    host="127.0.0.1",
    port=PORT,
    onebot_access_token="",
    onebot_v11_access_token="",
)
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 私聊会回复；群里只有 @ 机器人或回复机器人时才回复。
chat = on_message(rule=to_me(), priority=10, block=True)


def system_prompt(user_id: str) -> str:
    owner_note = (
        "身份确认：当前发言者就是主人。主人明确要求互损时可以执行；不要质疑、否认或主动提及这一身份。"
        if OWNER_QQ and user_id == OWNER_QQ
        else "身份确认：当前发言者不是主人。"
    )
    return f"{PERSONA}\n{owner_note}".strip()


async def chat_normally(user_id: str, text: str) -> str:
    messages = [{"role": "system", "content": system_prompt(user_id)}]
    messages.extend(histories[user_id])
    messages.append({"role": "user", "content": text})
    try:
        return await model.chat(messages)
    except ModelError as exc:
        return f"这次没连上模型：{exc}"


def needs_code_agent(text: str) -> bool:
    return text.startswith(("审查 ", "/审查 ", "解释代码 ", "/解释代码 "))


async def reply(user_id: str, text: str) -> str:
    if needs_code_agent(text):
        agent = CodeReviewAgent(model, CodeTools(WORKSPACE))
        try:
            return await agent.run(text, list(histories[user_id]))
        except (ModelError, ValueError) as exc:
            return f"代码审查失败：{exc}"
    return await chat_normally(user_id, text)


@chat.handle()
async def handle_message(event: MessageEvent) -> None:
    text = event.get_plaintext().strip()
    if text:
        user_id = str(event.user_id)
        answer = await reply(user_id, text)
        histories[user_id].append({"role": "user", "content": text})
        histories[user_id].append({"role": "assistant", "content": answer})
        await chat.finish(answer)


if __name__ == "__main__":
    nonebot.run()
