# CodeMate QQ 代码审查 Agent

一个可通过 QQ 和命令行使用的中文代码审查 Agent。它能读取工作目录中的代码文件，调用 LLM 分析潜在问题，并给出修改建议。

## 作业要求对应

| 作业要求 | 本项目实现 |
| --- | --- |
| Agent 循环 | `agent.py` 实现“输入 → 推理 → 工具调用 → 输出”循环 |
| 至少一种工具 | `tools.py` 提供受目录边界限制的 `read_file` |
| 命令行或简单界面 | `cli.py` 命令行入口，`qq_bot.py` QQ 入口 |
| 上下文记忆 | QQ 入口为每位用户保留最近 6 轮对话 |
| 错误处理与重试 | `llm.py` 对网络与 5xx 错误重试 3 次 |
| 项目文档 | 本 README、`Design.md` 和 `DEMO.md` |

## 第一次运行

1. 在这个目录安装依赖：`python -m pip install -r requirements.txt`
2. 将 `.env.example` 复制为 `.env`，并填写 `LLM_API_KEY`。
3. 启动机器人：`python qq_bot.py`
4. 在 NapCat 的 **OneBot 11 → 反向 WebSocket** 新增连接，地址填：

   `ws://127.0.0.1:8091/onebot/v11/ws`

   不填写 Access Token。保存并启用后，NapCat 日志出现 WebSocket 已连接即代表接入成功。

5. 私聊机器人，或在群里 @ 机器人并发送消息。

## 使用方式

普通聊天可以直接发消息。审查代码时，发送：

```text
审查 examples/buggy.py
```

或：

```text
解释代码 examples/buggy.py
```

机器人只能读取工作目录内的 UTF-8 文本。默认工作目录是启动机器人的项目目录，可在 `.env` 增加 `CODE_AGENT_WORKSPACE=你的代码文件夹` 修改。

命令行入口：

```powershell
python cli.py "审查 examples/buggy.py"
```

## 只改这几个地方

- 想换模型或服务商：改 `.env` 的 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`。
- 想换人设：改 `qq_bot.py` 顶部的 `PERSONA`。
- 想让它认主人：在 `.env` 填 `BOT_OWNER_QQ`。

## 测试

```powershell
python -m unittest discover -s tests -v
```

密钥只放在自己的 `.env`，不要复制到聊天记录、截图或代码仓库。
