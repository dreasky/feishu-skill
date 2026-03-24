#!/usr/bin/env python
"""
Claude Code 启动脚本（CLI 入口）
"""

import argparse
import sys

from claude_launcher import ClaudeLauncher

PERMISSION_MODES = [
    "acceptEdits",
    "bypassPermissions",
    "default",
    "dontAsk",
    "plan",
    "auto",
]


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code 启动脚本（支持 Windows/Linux）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_claude.py -d /path/to/project -p "帮我分析这个项目"
  python start_claude.py -d /path/to/project
  python start_claude.py -p "say hello"

权限模式说明:
  acceptEdits      - 自动接受文件编辑（默认）
  bypassPermissions - 跳过所有权限检查（慎用）
  default          - 每次操作都询问确认
  dontAsk          - 不主动询问，需明确授权
  plan             - 先制定计划再执行
  auto             - Claude 自行判断
        """,
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("-p", "--prompt", type=str, help="初始消息")
    input_group.add_argument("-f", "--file", type=str, help="从文件读取初始消息")

    parser.add_argument("-d", "--workdir", type=str, help="工作目录")
    parser.add_argument("-m", "--model", type=str, help="指定模型")
    parser.add_argument(
        "--permission-mode",
        choices=PERMISSION_MODES,
        default="acceptEdits",
        help="权限模式（默认: acceptEdits）",
    )

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

    # 创建启动器并启动
    launcher = ClaudeLauncher(workdir=args.workdir)
    success = launcher.launch(
        prompt=prompt,
        model=args.model,
        permission_mode=args.permission_mode,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()