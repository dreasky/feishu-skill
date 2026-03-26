from pathlib import Path
from typing import Dict, List, Set, Tuple
from wrapper.wrapper_entity import (
    ListBlocksResult,
    ListCommentsResult,
    FileCommentWrapper,
)
from .entity import CommentRef, BlockMatch, MatchResult, MatchFailedResult


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

    def match(self) -> Tuple[MatchResult, MatchFailedResult]:
        """执行匹配，返回匹配结果和失败结果"""
        blocks = self.blocks_result.items
        comments = self.comments_result.items

        # 构建 comment_id -> FileComment 映射
        comment_map: Dict[str, FileCommentWrapper] = {}
        for comment in comments:
            if comment.comment_id:
                comment_map[comment.comment_id] = comment

        # 遍历块，提取 comment_ids 并匹配
        match_map: Dict[str, BlockMatch] = {}
        matched_comment_ids: Set[str] = set()

        for block in blocks:
            if not block.block_id:
                continue

            # 提取块中的 comment_ids（去重）
            block_comment_ids = list(set(block.extract_comment_ids()))
            if not block_comment_ids:
                continue

            # 匹配评论
            matched_refs: List[CommentRef] = []
            for comment_id in block_comment_ids:
                if comment_id not in comment_map:
                    continue

                comment = comment_map[comment_id]
                matched_comment_ids.add(comment_id)

                replies = comment.extract_comment_replies()
                matched_refs.append(
                    CommentRef(
                        quote=comment.quote or "",
                        comment_id=comment_id,
                        comments=replies,
                    )
                )

            if matched_refs:
                content = block.extract_block_content()
                match_map[block.block_id] = BlockMatch(
                    block_id=block.block_id,
                    block_content=content,
                    comment_refs=matched_refs,
                )

        # 未匹配的评论
        failed_refs: List[CommentRef] = []
        for comment in comments:
            if comment.comment_id and comment.comment_id not in matched_comment_ids:
                replies = comment.extract_comment_replies()
                failed_refs.append(
                    CommentRef(
                        quote=comment.quote or "",
                        comment_id=comment.comment_id,
                        comments=replies,
                    )
                )

        # 生成结果
        matches = list(match_map.values())

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
