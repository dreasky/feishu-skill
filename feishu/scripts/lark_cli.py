import argparse
import asyncio
import sys
import os

from lark_wrapper import LarkWrapper


def get_wrapper() -> LarkWrapper:
    """获取 LarkWrapper 实例"""
    return LarkWrapper()


# === 消息 API ===


async def cmd_send_text(args):
    """发送文本消息"""
    wrapper = get_wrapper()
    wrapper.send_text(chat_id=args.chat_id, message=args.message)


# === 群组 API ===


async def cmd_list_chat(args):
    """获取群列表"""
    wrapper = get_wrapper()
    wrapper.list_chat()


# === 云文档 API ===


async def cmd_root_folder(args):
    """获取根文件夹元数据"""
    wrapper = get_wrapper()
    wrapper.root_folder()


async def cmd_list_file(args):
    """获取文件夹中的文件清单"""
    wrapper = get_wrapper()
    wrapper.list_file()


async def cmd_upload_markdown(args):
    """上传markdown文档"""
    wrapper = get_wrapper()
    wrapper.upload_markdown(file_path=args.file_path)


async def cmd_import_task(args):
    """创建导入任务"""
    wrapper = get_wrapper()
    # 从 file_token 获取文件名
    file_name = os.path.basename(args.file_path) if hasattr(args, "file_path") else None
    if not file_name:
        # 如果没有 file_path，使用默认名称
        file_name = "imported_document.md"
    wrapper.import_task(file_token=args.file_token, file_name=file_name)


async def cmd_get_import_task(args):
    """查询导入任务结果"""
    wrapper = get_wrapper()
    wrapper.get_import_task(ticket=args.ticket)


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

    p = subparsers.add_parser("import-task", help="创建导入任务")
    p.add_argument("--file-token", required=True, help="要导入文件的token")
    p.add_argument("--file-path", help="原始文件路径（用于获取文件名）")

    p = subparsers.add_parser("get-import-task", help="查询导入任务结果")
    p.add_argument("--ticket", required=True, help="导入任务ID")

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
        "import-task": cmd_import_task,
        "get-import-task": cmd_get_import_task,
    }

    try:
        asyncio.run(cmd_map[args.command](args))
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
