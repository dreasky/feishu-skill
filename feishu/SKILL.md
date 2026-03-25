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

## 命令速查索引

| 类别   | 命令                   | 说明                   |
| ------ | ---------------------- | ---------------------- |
| 消息   | `send-text`            | 发送文本消息           |
| 消息   | `list-messages`        | 获取会话历史消息       |
| 消息   | `get-message-content`  | 获取指定消息的内容     |
| 消息   | `get-message-resource` | 获取消息中的资源文件   |
| 群组   | `list-chat`            | 获取机器人所在的群列表 |
| 机器人 | `get-bot-info`         | 获取机器人信息         |
| 云文档 | `root-folder`          | 获取根文件夹元数据     |
| 云文档 | `list-file`            | 获取文件夹文件清单     |
| 云文档 | `upload-file`          | 上传任意文件           |
| 云文档 | `get-import-task`      | 查询导入任务结果       |
| 云文档 | `authorize-file`       | 授权文件权限           |
| 云文档 | `list-comment-block`   | 获取云文档所有评论块   |

---

## 消息

### `send-text` — 发送文本消息

| 参数        | 必填 | 说明     |
| ----------- | ---- | -------- |
| `--chat-id` | 是   | 会话 ID  |
| `--message` | 是   | 消息内容 |

```bash
python scripts/run.py lark_cli.py send-text --chat-id "<chat_id>" --message "<消息内容>"
```

---

### `list-messages` — 获取会话历史消息

| 参数                  | 必填 | 说明                              |
| --------------------- | ---- | --------------------------------- |
| `--container-id-type` | 是   | 容器类型（如 `chat`）             |
| `--container-id`      | 是   | 容器 ID                           |
| `--start-time`        | 否   | 起始时间戳                        |
| `--end-time`          | 否   | 结束时间戳                        |
| `--sort-type`         | 否   | 排序方式（如 `ByCreateTimeDesc`） |
| `--page-size`         | 否   | 每页数量                          |
| `--page-token`        | 否   | 翻页 token                        |

```bash
# 获取群聊历史消息
python scripts/run.py lark_cli.py list-messages --container-id-type chat --container-id "<chat_id>"

# 指定时间范围和排序
python scripts/run.py lark_cli.py list-messages --container-id-type chat --container-id "<chat_id>" --start-time "1608594809" --end-time "1609296809" --sort-type ByCreateTimeDesc --page-size 50
```

---

### `get-message-content` — 获取指定消息的内容

| 参数             | 必填 | 说明                                                               |
| ---------------- | ---- | ------------------------------------------------------------------ |
| `--message-id`   | 是   | 消息 ID                                                            |
| `--user-id-type` | 否   | 用户 ID 类型（`open_id` / `union_id` / `user_id`，默认 `open_id`） |

```bash
python scripts/run.py lark_cli.py get-message-content --message-id "<message_id>"
```

---

### `get-message-resource` — 获取消息中的资源文件

| 参数           | 必填 | 说明                         |
| -------------- | ---- | ---------------------------- |
| `--message-id` | 是   | 消息 ID                      |
| `--file-key`   | 是   | 资源 key                     |
| `--type`       | 是   | 资源类型（`image` / `file`） |
| `--save-dir`   | 是   | 保存目录                     |

```bash
# 下载图片
python scripts/run.py lark_cli.py get-message-resource --message-id "<message_id>" --file-key "<file_key>" --type image --save-dir "/tmp/downloads"

# 下载文件/音频/视频
python scripts/run.py lark_cli.py get-message-resource --message-id "<message_id>" --file-key "<file_key>" --type file --save-dir "/tmp/downloads"
```

---

## 群组

### `list-chat` — 获取机器人所在的群列表

无参数。返回群名称 + chat_id。

```bash
python scripts/run.py lark_cli.py list-chat
```

---

## 机器人

### `get-bot-info` — 获取机器人信息

无参数。返回机器人名称、open_id、头像、启用状态。

```bash
python scripts/run.py lark_cli.py get-bot-info
```

---

## 云文档

### `root-folder` — 获取根文件夹元数据

无参数。

```bash
python scripts/run.py lark_cli.py root-folder
```

---

### `list-file` — 获取文件夹文件清单

无参数。

```bash
python scripts/run.py lark_cli.py list-file
```

---

### `upload-file` — 上传任意文件

| 参数          | 必填 | 说明                    |
| ------------- | ---- | ----------------------- |
| `--file-path` | 是   | 本地文件路径            |
| `--obj-type`  | 否   | 文档类型（默认 `docx`） |

返回 ticket，用于后续查询导入任务。

```bash
python scripts/run.py lark_cli.py upload-file --file-path "/path/to/file" --obj-type "docx"
```

---

### `get-import-task` — 查询上传文件结果

| 参数       | 必填 | 说明                        |
| ---------- | ---- | --------------------------- |
| `--ticket` | 是   | `upload-file` 返回的 ticket |

```bash
python scripts/run.py lark_cli.py get-import-task --ticket "<ticket>"
```

---

### `authorize-file` — 授权文件权限

| 参数           | 必填 | 说明       |
| -------------- | ---- | ---------- |
| `--file-token` | 是   | 文件 token |

授权范围：全量群组。

```bash
python scripts/run.py lark_cli.py authorize-file --file-token "<file_token>"
```

### `list-comment-block` — 获取云文档所有评论块

| 参数            | 必填 | 说明                                         |
| --------------- | ---- | -------------------------------------------- |
| `--document-id` | 是   | 云文档 ID                                    |
| `--file-type`   | 是   | 文档类型: doc / docx / sheet / file / slides |
| `--output-path` | 是   | 输出文件路径                                 |

获取所有评论块，保存到指定路径。

```bash
python scripts/run.py comment_handle.py match --document-id "<document_id>" --file-type "docx" --output-path "/path/to/file.json"
```
