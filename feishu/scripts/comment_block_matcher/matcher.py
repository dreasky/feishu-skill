from pathlib import Path
from typing import Dict, List, Set, Tuple, Union
from wrapper.wrapper_entity import (
    ListBlocksResult,
    ListCommentsResult,
    BlockItem,
    TextBlockItem,
    Heading1BlockItem,
    Heading2BlockItem,
    Heading3BlockItem,
    Heading4BlockItem,
    Heading5BlockItem,
    Heading6BlockItem,
    Heading7BlockItem,
    Heading8BlockItem,
    Heading9BlockItem,
    ImageBlockItem,
    CommentItem,
)
from .entity import CommentRef, BlockMatch, MatchResult, MatchFailedResult


# 长文本阈值，超过此长度使用模糊匹配
LONG_TEXT_THRESHOLD = 50

# Block 类型常量
BLOCK_TYPE_TEXT = 2
BLOCK_TYPE_HEADING = [3, 4, 5, 6, 7, 8, 9, 10, 11]  # 标题1-9
BLOCK_TYPE_IMAGE = 27

# 文本块类型（包含 elements 字段的块）
TextBlockUnion = Union[
    TextBlockItem,
    Heading1BlockItem,
    Heading2BlockItem,
    Heading3BlockItem,
    Heading4BlockItem,
    Heading5BlockItem,
    Heading6BlockItem,
    Heading7BlockItem,
    Heading8BlockItem,
    Heading9BlockItem,
]


def normalize_text(text: str) -> str:
    """标准化文本，去除首尾空白和标点符号"""
    text = text.strip()
    # 去除末尾常见标点
    while text and text[-1] in "。！？，、；：" "''）】》":
        text = text[:-1].strip()
    while text and text[0] in "（【《" "''":
        text = text[1:].strip()
    return text


class CommentBlockMatcher:
    """评论与文档块匹配器"""

    def __init__(
        self,
        blocks_result: ListBlocksResult,
        comments_result: ListCommentsResult,
        document_id: str,
    ):
        self.blocks_result = blocks_result
        self.comments_result = comments_result
        self.document_id = document_id

    def _extract_block_content(self, block: TextBlockUnion) -> str:
        """提取文本块的完整文本内容"""
        return "".join(block.elements)

    def _extract_comment_replies(self, comment: CommentItem) -> List[str]:
        """提取评论的所有回复内容"""
        replies = []
        if comment.reply_list:
            for reply in comment.reply_list.replies:
                if reply.content:
                    for elem in reply.content.elements:
                        if elem.text_run and elem.text_run.text:
                            replies.append(elem.text_run.text)
        return replies

    def _is_text_block(self, block: BlockItem) -> bool:
        """判断是否为文本类块"""
        return isinstance(block, TextBlockItem) or any(
            isinstance(block, cls)
            for cls in [
                Heading1BlockItem,
                Heading2BlockItem,
                Heading3BlockItem,
                Heading4BlockItem,
                Heading5BlockItem,
                Heading6BlockItem,
                Heading7BlockItem,
                Heading8BlockItem,
                Heading9BlockItem,
            ]
        )

    def _is_heading_block(self, block: BlockItem) -> bool:
        """判断是否为标题类块"""
        return any(
            isinstance(block, cls)
            for cls in [
                Heading1BlockItem,
                Heading2BlockItem,
                Heading3BlockItem,
                Heading4BlockItem,
                Heading5BlockItem,
                Heading6BlockItem,
                Heading7BlockItem,
                Heading8BlockItem,
                Heading9BlockItem,
            ]
        )

    def match(self) -> Tuple[MatchResult, MatchFailedResult]:
        """执行匹配，返回匹配结果和失败结果"""
        blocks = self.blocks_result.items
        comments = self.comments_result.items

        # 预处理：生成 block_id -> (block, content) 映射（仅文本类块）
        block_map: Dict[str, Tuple[TextBlockUnion, str]] = {}
        for block in blocks:
            if block.block_id and self._is_text_block(block):
                content = self._extract_block_content(block)  # type: ignore
                block_map[block.block_id] = (block, content)  # type: ignore

        # 匹配结果：block_id -> BlockMatch
        match_map: Dict[str, BlockMatch] = {}
        # 失败列表
        failed_refs: List[CommentRef] = []

        # 遍历评论进行匹配
        for comment in comments:
            quote = comment.quote or ""
            comment_id = comment.comment_id or ""

            if not quote or not comment_id:
                continue

            replies = self._extract_comment_replies(comment)
            comment_ref = CommentRef(
                quote=quote,
                comment_id=comment_id,
                comments=replies,
            )

            # 匹配逻辑
            matched_block_ids: Set[str] = set()

            for block_id, (block, content) in block_map.items():
                if len(quote) >= LONG_TEXT_THRESHOLD or self._is_text_block(block):
                    # 长文本或标题：模糊匹配，直接包含即可
                    if quote in content:
                        matched_block_ids.add(block_id)
                else:
                    # 短文本：标准化后匹配 element
                    normalized_quote = normalize_text(quote)
                    for elem in block.elements:
                        normalized_content = normalize_text(elem)
                        if normalized_quote == normalized_content:
                            matched_block_ids.add(block_id)

            # 将匹配结果加入 match_map 或失败列表
            if matched_block_ids:
                for block_id in matched_block_ids:
                    if block_id not in match_map:
                        _, content = block_map[block_id]
                        match_map[block_id] = BlockMatch(
                            block_id=block_id,
                            block_content=content,
                            comment_refs=[],
                        )
                    match_map[block_id].comment_refs.append(comment_ref)
            else:
                failed_refs.append(comment_ref)

        # 生成最终结果
        matches = list(match_map.values())

        # 统计唯一的评论数（避免一个评论匹配多个块时重复计数）
        matched_comment_ids: Set[str] = set()
        for m in matches:
            for ref in m.comment_refs:
                matched_comment_ids.add(ref.comment_id)

        match_result = MatchResult(
            document_id=self.document_id,
            total_blocks=len(matches),
            total_comments=len(matched_comment_ids),
            matches=matches,
        )

        failed_result = MatchFailedResult(
            document_id=self.document_id,
            total_failed=len(failed_refs),
            items=failed_refs,
        )

        return match_result, failed_result

    def match_and_save(self, output_dir: str) -> Tuple[MatchResult, MatchFailedResult]:
        """
        执行匹配并保存到文件

        Args:
            output_dir: 输出目录
        """
        match_result, failed_result = self.match()

        # 保存目录
        save_dir = Path(output_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # 保存匹配结果
        match_file = save_dir / "matches.json"
        match_file.write_text(match_result.model_dump_json(indent=2), encoding="utf-8")

        # 保存失败结果
        failed_file = save_dir / "match_failed.json"
        failed_file.write_text(
            failed_result.model_dump_json(indent=2), encoding="utf-8"
        )

        print(f"✅ match success")
        print(f"   total_blocks: {match_result.total_blocks}")
        print(f"   total_comments: {match_result.total_comments}")
        print(f"   total_failed: {failed_result.total_failed}")
        print(
            f"   total_all: {match_result.total_comments + failed_result.total_failed}"
        )
        print(f"   saved to: {output_dir}")

        return match_result, failed_result
