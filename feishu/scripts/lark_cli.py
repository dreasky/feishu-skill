import argparse
import asyncio
import sys
from pathlib import Path
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


async def cmd_upload_file(args):
    """上传文件并创建导入任务"""
    file_path = Path(args.file_path)

    wrapper = LarkFastAPI()
    wrapper.upload_file(
        file_path=file_path,
        obj_type=args.obj_type or "docx",
    )


async def cmd_get_import_task(args):
    """查询导入任务结果"""
    wrapper = CloudSpaceWrapper()
    wrapper.get_import_task(args.ticket)


async def cmd_batch_create_permission_member_custom(args):
    """授权文件"""
    wrapper = LarkFastAPI()
    wrapper.batch_create_permission_member_custom(args.file_token)


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
    p.add_argument("--file-name", help="文件名称")

    p = subparsers.add_parser("upload-file", help="上传文件")
    p.add_argument("--file-path", required=True, help="文件路径")
    p.add_argument("--obj-type", help="上传目标类型, 默认docx")

    p = subparsers.add_parser("get-import-task", help="上传文件")
    p.add_argument("--ticket", required=True, help="任务id")

    p = subparsers.add_parser("authorize-file", help="授权文件权限(全量,群组)")
    p.add_argument("--file-token", required=True, help="任务id")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "send-text": cmd_send_text,
        "list-chat": cmd_list_chat,
        "root-folder": cmd_root_folder,
        "list-file": cmd_list_file,
        "upload-file": cmd_upload_file,
        "upload-file": 
        "get-import-task": cmd_get_import_task,
        "authorize-file": cmd_batch_create_permission_member_custom,
    }

    try:
        asyncio.run(cmd_map[args.command](args))
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
