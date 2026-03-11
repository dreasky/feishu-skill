import argparse
import asyncio
import sys
import os

from wrapper import *
from lark_fast_api import LarkFastAPI


# === 消息 API ===


async def cmd_send_text(args):
    """发送文本消息"""
    fast_api = LarkFastAPI()
    fast_api.send_message_custom(chat_id=args.chat_id, message=args.message)


# === 群组 API ===


async def cmd_list_chat(args):
    """获取群列表"""
    wrapper = GroupManageWrapper()
    wrapper.list_chat()


# === 云文档 API ===


async def cmd_root_folder(args):
    """获取根文件夹元数据"""
    wrapper = CloudSpaceWrapper()
    wrapper.root_folder()


async def cmd_list_file(args):
    """获取文件夹中的文件清单"""
    wrapper = CloudSpaceWrapper()
    wrapper.list_file()


async def cmd_upload_markdown(args):
    """上传markdown文档"""
    file_path = args.file_path
    file_name = args.file_name
    if not file_name:
        # 没有文件名时默认使用上传文件名称
        file_name = os.path.basename(file_path)

    wrapper = LarkFastAPI()
    wrapper.upload_markdown(file_path, file_name)


def main():
    parser = argparse.ArgumentParser(description="feishu CLI - 飞书命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # === 消息 API ===
    p = subparsers.add_parser("send-text", help="发送文本消息")
    p.add_argument("--chat-id", required=True, help="对话ID")
    p.add_argument("--message", required=True, help="消息文本")

    # === 群组 API ===
    subparsers.add_parser("list-chat", help="获取用户或机器人所在的群列表")

    # === 云文档 API ===
    subparsers.add_parser("root-folder", help="获取我的空间（根文件夹）元数据")

    subparsers.add_parser("list-file", help="获取文件夹中的文件清单")

    p = subparsers.add_parser("upload-markdown", help="上传markdown文档")
    p.add_argument("--file-path", required=True, help="markdown文件路径")
    p.add_argument("--file-name", help="上传文件名称")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "send-text": cmd_send_text,
        "list-chat": cmd_list_chat,
        "root-folder": cmd_root_folder,
        "list-file": cmd_list_file,
        "upload-markdown": cmd_upload_markdown,
    }

    try:
        asyncio.run(cmd_map[args.command](args))
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
