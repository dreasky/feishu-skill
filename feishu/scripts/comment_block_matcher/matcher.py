from pathlib import Path
from typing import Dict, List
from wrapper.wrapper_entity import ListBlocksResult, ListCommentsResult, BlockItem, CommentItem
from .entity import CommentRef, BlockMatch, MatchResult


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

    def _extract_block_content(self, block: BlockItem) -> str:
        """提取块的完整文本内容"""
        parts = []
        for elem in block.elements:
            if elem.text_run and elem.text_run.content:
                parts.append(elem.text_run.content)
        return "".join(parts)

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

    def match(self, match_mode: str = "loose") -> MatchResult:
        """
        执行匹配

        Args:
            match_mode: 匹配模式 "strict" 或 "loose"
        """
        blocks = self.blocks_result.items
        comments = self.comments_result.items

        # 预处理：生成 block_id -> (block, content) 映射
        block_map: Dict[str, tuple] = {}
        for block in blocks:
            if block.block_id:
                content = self._extract_block_content(block)
                block_map[block.block_id] = (block, content)

        # 匹配结果：block_id -> BlockMatch
        match_map: Dict[str, BlockMatch] = {}

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

            # 根据模式匹配
            matched_block_ids = set()

            if match_mode == "strict":
                # 严格模式：quote 必须完全匹配某个 element 的 content
                for block_id, (block, content) in block_map.items():
                    for elem in block.elements:
                        if elem.text_run and elem.text_run.content == quote:
                            matched_block_ids.add(block_id)
                            break
            else:
                # 宽松模式：quote 包含在 block_content 中
                for block_id, (block, content) in block_map.items():
                    if quote in content:
                        matched_block_ids.add(block_id)

            # 将匹配结果加入 match_map
            for block_id in matched_block_ids:
                if block_id not in match_map:
                    _, content = block_map[block_id]
                    match_map[block_id] = BlockMatch(
                        block_id=block_id,
                        block_content=content,
                        comment_refs=[],
                    )
                match_map[block_id].comment_refs.append(comment_ref)

        # 生成最终结果
        matches = list(match_map.values())
        total_comments = sum(len(m.comment_refs) for m in matches)

        return MatchResult(
            document_id=self.document_id,
            match_mode=match_mode,
            total_blocks=len(matches),
            total_comments=total_comments,
            matches=matches,
        )

    def match_and_save(self, output_path: str, match_mode: str = "loose") -> MatchResult:
        """
        执行匹配并保存到文件

        Args:
            output_path: 输出文件路径
            match_mode: 匹配模式 "strict" 或 "loose"
        """
        result = self.match(match_mode)

        # 保存到文件
        save_file = Path(output_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)
        save_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        print(f"✅ match success")
        print(f"   match_mode: {match_mode}")
        print(f"   total_blocks: {result.total_blocks}")
        print(f"   total_comments: {result.total_comments}")
        print(f"   saved to: {output_path}")

        return result