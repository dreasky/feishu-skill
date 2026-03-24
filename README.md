# 飞书技能项目

## 概述

与飞书平台交互的skill，替代mcp方案，可灵活自定义

## 功能

* 为claude code等ai工具接入飞书交互
* 使用skill的方式调用飞书[服务端API](https://open.feishu.cn/document/home/index)

## 安装使用

```bash
npx skills add https://github.com/dreasky/feishu-skill --skill feishu
```

---

## Claude Code 启动器

在新终端窗口中启动 Claude CLI，支持自定义工作目录和初始消息。

### CLI 使用

```bash
cd feishu/scripts

# 启动 Claude（默认 acceptEdits 权限模式）
python start_claude.py -d /path/to/project -p "帮我分析这个项目"

# 从文件读取初始消息
python start_claude.py -d /path/to/project -f prompt.txt

# 指定模型
python start_claude.py -d /path/to/project -p "say hello" -m claude-opus-4-6

# 指定权限模式
python start_claude.py -d /path/to/project -p "帮我重构" --permission-mode plan
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-d, --workdir` | 工作目录 |
| `-p, --prompt` | 初始消息 |
| `-f, --file` | 从文件读取初始消息 |
| `-m, --model` | 指定模型 |
| `--permission-mode` | 权限模式（默认: acceptEdits） |

### 权限模式

| 模式 | 说明 |
|------|------|
| `acceptEdits` | 自动接受文件编辑（默认） |
| `bypassPermissions` | 跳过所有权限检查（慎用） |
| `default` | 每次操作都询问确认 |
| `dontAsk` | 不主动询问，需明确授权 |
| `plan` | 先制定计划再执行 |
| `auto` | Claude 自行判断 |

### 代码调用

```python
from claude_launcher import ClaudeLauncher

# 创建启动器
launcher = ClaudeLauncher(workdir="/path/to/project")

# 启动 Claude
launcher.launch(
    prompt="帮我分析这个项目",
    model="claude-sonnet-4-6",
    permission_mode="acceptEdits"
)

# 在当前窗口启动
launcher.launch(prompt="say hello", new_window=False)
```

### 跨平台支持

* **Windows**: 使用 `start` 命令打开新 cmd 窗口
* **Linux**: 自动检测终端模拟器（gnome-terminal、konsole、xfce4-terminal、mate-terminal、xterm）

---

## 贡献

欢迎通过提交问题和拉取请求来为这个项目做出贡献。

## 许可证

本项目根据 MIT 许可证授权。
