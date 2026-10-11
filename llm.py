"""OpenAI 兼容模型客户端，集中处理超时与重试。"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx


class ModelError(RuntimeError):
    """模型服务不可用或返回异常时抛出。"""


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 45) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key or "填入" in self.api_key:
            raise ModelError("尚未配置有效的 LLM_API_KEY")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions", json=payload, headers=headers
                    )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"].get("content", "").strip()
                if not content:
                    raise ModelError("模型返回了空内容")
                return content
            except httpx.HTTPStatusError as exc:
                # 认证、模型名和余额等 4xx 问题不会因重试而恢复。
                if exc.response.status_code < 500:
                    raise ModelError(f"模型服务返回 HTTP {exc.response.status_code}") from exc
                last_error = exc
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                last_error = exc
            if attempt < 2:
                await asyncio.sleep(2**attempt)

        raise ModelError(f"模型请求失败，已重试 3 次：{last_error}")
