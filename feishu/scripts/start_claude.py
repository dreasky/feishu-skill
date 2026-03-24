#!/usr/bin/env python
"""
Claude Code 启动脚本
1. 打开新终端窗口并切换到指定工作目录
2. 在新窗口中启动 Claude 并传入初始消息

支持 Windows 和 Linux 系统
"""

import argparse
import os
import subprocess
import sys
import tempfile
from typing import Optional
from pathlib import Path


def find_claude_path() -> str:
    """查找 Claude CLI 路径"""
    if sys.platform == "win32":
        result = subprocess.run(
            ["where", "claude"], capture_output=True, text=True, shell=True
        )
    else:
        result = subprocess.run(["which", "claude"], capture_output=True, text=True)

    if result.returncode == 0:
        return result.stdout.strip().split("\n")[0]
    return "claude"


def get_linux_terminal() -> list:
    """检测可用的 Linux 终端模拟器"""
    terminals = [
        ("gnome-terminal", ["gnome-terminal", "--"]),
        ("konsole", ["konsole", "-e"]),
        ("xfce4-terminal", ["xfce4-terminal", "-e"]),
        ("mate-terminal", ["mate-terminal", "-e"]),
        ("xterm", ["xterm", "-e"]),
    ]

    for name, cmd in terminals:
        result = subprocess.run(["which", name], capture_output=True)
        if result.returncode == 0:
            return cmd

    return ["xterm", "-e"]


def create_temp_script(
    workdir: str,
    claude_path: str,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """创建临时启动脚本，返回脚本路径"""
    workdir = os.path.abspath(workdir)

    # 构建 claude 命令
    claude_cmd = f'"{claude_path}"' if sys.platform == "win32" else claude_path
    if model:
        claude_cmd += f" --model {model}"
    if prompt:
        escaped_prompt = prompt.replace('"', '""' if sys.platform == "win32" else '\\"')
        claude_cmd += f' "{escaped_prompt}"'

    if sys.platform == "win32":
        # Windows: 创建 bat 脚本
        content = f'@echo off\ncd /d "{workdir}"\n{claude_cmd}\n'
        suffix = ".bat"
    else:
        # Linux: 创建 shell 脚本
        content = f'#!/bin/bash\ncd "{workdir}"\n{claude_cmd}\nexec bash\n'
        suffix = ".sh"

    # 创建临时文件
    script_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    script_file.write(content)
    script_file.close()

    # Linux 需要添加执行权限
    if sys.platform != "win32":
        os.chmod(script_file.name, 0o755)

    print(f"工作目录: {workdir}")
    print(f"执行命令: {claude_cmd}")
    print(f"临时脚本: {script_file.name}")
    print("-" * 50)

    return script_file.name


def start_in_new_window(
    workdir: str, prompt: Optional[str] = None, model: Optional[str] = None
):
    """在新窗口中启动 Claude"""
    claude_path = find_claude_path()
    script_path = create_temp_script(workdir, claude_path, prompt, model)

    if sys.platform == "win32":
        # Windows: 使用 start 命令
        subprocess.run(
            f'start "Claude Code - {Path(workdir).name}" cmd /k "{script_path}"',
            shell=True,
        )
    else:
        # Linux: 使用终端模拟器
        terminal_cmd = get_linux_terminal()
        subprocess.Popen(terminal_cmd + [script_path], start_new_session=True)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code 启动脚本（支持 Windows/Linux）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_claude.py -d /path/to/project -p "帮我分析这个项目"
  python start_claude.py -d /path/to/project
  python start_claude.py -p "say hello"
        """,
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("-p", "--prompt", type=str, help="初始消息")
    input_group.add_argument("-f", "--file", type=str, help="从文件读取初始消息")

    parser.add_argument("-d", "--workdir", type=str, help="工作目录")
    parser.add_argument("-m", "--model", type=str, help="指定模型")

    args = parser.parse_args()

    # 获取初始消息
    prompt = None
    if args.prompt:
        prompt = args.prompt
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
        except FileNotFoundError:
            print(f"错误: 文件 '{args.file}' 不存在")
            sys.exit(1)

    workdir = args.workdir or os.getcwd()
    start_in_new_window(workdir=workdir, prompt=prompt, model=args.model)


if __name__ == "__main__":
    main()
