# 一分钟演示脚本

1. 展示 `README.md` 和目录结构，说明项目是 QQ 代码审查 Agent。
2. 启动 `python qq_bot.py`，展示 OneBot 已连接。
3. 在 QQ 发送：`审查 examples/buggy.py`。
4. 展示机器人先读取文件，再指出空列表会触发除零错误，并建议加空列表判断。
5. 运行 `python -m unittest discover -s tests -v`，展示工具越界限制和 Agent 工具调用测试通过。
