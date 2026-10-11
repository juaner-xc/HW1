"""代码 Agent 的本地文件读取工具。"""
from __future__ import annotations

from pathlib import Path


class ToolError(ValueError):
    pass


class CodeTools:
    """只允许读取工作目录内的文本代码，防止路径越界和超大文件。"""

    def __init__(self, workspace: Path, max_chars: int = 40_000) -> None:
        self.workspace = workspace.resolve()
        self.max_chars = max_chars

    def schema(self) -> list[dict[str, object]]:
        return [
            {
                "name": "read_file",
                "description": "读取工作目录内的一个代码或文本文件。",
                "arguments": {"path": "相对于工作目录的文件路径"},
            }
        ]

    def call(self, name: str, arguments: dict[str, object]) -> str:
        if name != "read_file":
            raise ToolError(f"不支持的工具：{name}")
        raw_path = str(arguments.get("path") or "").strip()
        if not raw_path:
            raise ToolError("read_file 缺少 path 参数")

        target = (self.workspace / raw_path).resolve()
        if target != self.workspace and self.workspace not in target.parents:
            raise ToolError("文件路径越出工作目录")
        if not target.is_file():
            raise ToolError(f"文件不存在：{raw_path}")
        if target.stat().st_size > self.max_chars * 3:
            raise ToolError("文件过大，限制为约 40 KB 文本")

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ToolError("只支持 UTF-8 文本文件") from exc
        return content[: self.max_chars]
