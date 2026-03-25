"""
评论块匹配 CLI 脚本

用法:
    python scripts/run.py comment_handle.py match \
        --document-id "xxx" \
        --file-type "docx" \
        --output-dir "./output"
"""

import argparse
import sys
from wrapper import DocBlockWrapper, CloudSpaceWrapper
from comment_block_matcher import CommentBlockMatcher


def cmd_match(args):
    """匹配文档块与评论"""
    # 获取块数据
    block_wrapper = DocBlockWrapper()
    blocks_result = block_wrapper.list_blocks(
        document_id=args.document_id, save_path=f"{args.output_dir}/blocks.json"
    )

    # 获取评论数据（非全文评论）
    comment_wrapper = CloudSpaceWrapper()
    comments_result = comment_wrapper.list_comments(
        file_token=args.document_id,
        file_type=args.file_type,
        is_whole=False,
        save_path=f"{args.output_dir}/comments.json",
    )

    # 匹配并保存
    matcher = CommentBlockMatcher(
        blocks_result=blocks_result,
        comments_result=comments_result,
        document_id=args.document_id,
    )
    matcher.match_and_save(output_dir=args.output_dir)


def main():
    parser = argparse.ArgumentParser(description="评论块匹配工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # match 命令
    p = subparsers.add_parser("match", help="匹配文档块与评论")
    p.add_argument("--document-id", required=True, help="文档ID")
    p.add_argument(
        "--file-type",
        required=True,
        help="文档类型: doc / docx / sheet / file / slides",
    )
    p.add_argument("--output-dir", required=True, help="输出目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "match": cmd_match,
    }

    try:
        cmd_map[args.command](args)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())