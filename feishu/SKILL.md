---
name: feishu
description: 与飞书集成的技能。当需要与飞书交互时使用此技能。
---

# 飞书集成技能

## 执行规则

**必须**通过 `run.py` 调用，禁止直接执行脚本：

```bash
python scripts/run.py lark_cli.py <command> [options]
```

`run.py` 负责自动管理虚拟环境（创建 `.venv`、安装依赖、激活环境）。

---

## 命令参考

### 消息

| 命令            | 说明             | 参数                                                                                                                                                           |
| --------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `send-text`     | 发送文本消息     | `--chat-id` (必填) `--message` (必填)                                                                                                                          |
| `list-messages` | 获取会话历史消息 | `--container-id-type` (必填) `--container-id` (必填) `--start-time` (可选) `--end-time` (可选) `--sort-type` (可选) `--page-size` (可选) `--page-token` (可选) |

```bash
python scripts/run.py lark_cli.py send-text --chat-id "<chat_id>" --message "<消息内容>"

# 获取群聊历史消息
python scripts/run.py lark_cli.py list-messages --container-id-type chat --container-id "<chat_id>"

# 指定时间范围和排序
python scripts/run.py lark_cli.py list-messages --container-id-type chat --container-id "<chat_id>" --start-time "1608594809" --end-time "1609296809" --sort-type ByCreateTimeDesc --page-size 50
```

---

### 群组

| 命令        | 说明                   | 参数 |
| ----------- | ---------------------- | ---- |
| `list-chat` | 获取机器人所在的群列表 | 无   |

```bash
python scripts/run.py lark_cli.py list-chat
# 返回：群名称 + chat_id
```

---

### 云文档

| 命令              | 说明               | 参数                                                  |
| ----------------- | ------------------ | ----------------------------------------------------- |
| `root-folder`     | 获取根文件夹元数据 | 无                                                    |
| `list-file`       | 获取文件夹文件清单 | 无                                                    |
| `upload-file`     | 上传任意文件       | `--file-path` (必填) `--obj-type` (可选, 默认 `docx`) |
| `get-import-task` | 查询导入任务结果   | `--ticket` (必填)                                     |
| `authorize-file`  | 授权文件权限       | `--file-token` (必填)                                 |

```bash
# 查看根文件夹
python scripts/run.py lark_cli.py root-folder

# 列出文件
python scripts/run.py lark_cli.py list-file

# 上传文件（返回 ticket）
python scripts/run.py lark_cli.py upload-file --file-path "/path/to/file" --obj-type "docx"

# 查询导入任务（用 upload-file 返回的 ticket）
python scripts/run.py lark_cli.py get-import-task --ticket "<ticket>"

# 授权文件（全量群组）
python scripts/run.py lark_cli.py authorize-file --file-token "<file_token>"
```
