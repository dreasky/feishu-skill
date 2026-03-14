---
name: feishu
description: 与飞书集成的技能。当需要与飞书交互时使用此技能。
---

# 飞书集成技能

## 关键：始终使用 run.py 包装器

绝对不要直接调用脚本。始终使用 `python scripts/run.py [script]` :

```bash
# ✅ CORRECT - Always use run.py:
python scripts/run.py lark_cli.py [command] [options]

# ❌ WRONG - Never call directly:
python scripts/lark_cli.py [command] [options]  # Fails without venv!
```

`run.py` 包装器会自动：

1. 创建 `.venv` 虚拟环境（如果不存在）
2. 安装所有依赖
3. 激活环境
4. 正确执行脚本

## 命令速查表

| 命令              | 说明          | 必需参数                 |
| ----------------- | ------------- | ------------------------ |
| `send-text`       | 发送文本消息  | `--chat-id`, `--message` |
| `list-chat`       | 获取群聊列表  | 无                       |
| `root-folder`     | 获取根文件夹  | 无                       |
| `list-file`       | 获取文件清单  | 无                       |
| `upload-markdown` | 上传 Markdown | `--file-path`            |

## 功能列表

### 发送文本消息

```bash
python scripts/run.py lark_cli.py send-text --chat-id "聊天ID" --message "消息内容"
```

### 获取群聊列表

```bash
python scripts/run.py lark_cli.py list-chat
```

返回机器人所在的所有群聊信息（名称和 chat_id）。

### 云文档操作

**获取根文件夹元数据：**

```bash
python scripts/run.py lark_cli.py root-folder
```

**获取文件夹中的文件清单：**

```bash
python scripts/run.py lark_cli.py list-file
```

**上传 Markdown 文档到飞书：**

```bash
python scripts/run.py lark_cli.py upload-markdown --file-path "/path/to/document.md" --file-name "文件名称"
```
