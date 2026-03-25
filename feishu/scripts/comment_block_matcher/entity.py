from typing import List
from pydantic import BaseModel


class CommentRef(BaseModel):
    """评论引用"""
    quote: str                       # 评论引用的原文
    comment_id: str                  # 评论ID
    comments: List[str]              # 该评论下的回复列表


class BlockMatch(BaseModel):
    """块匹配结果"""
    block_id: str                    # 块ID（唯一）
    block_content: str               # 块完整文本
    comment_refs: List[CommentRef]   # 该块的评论引用列表


class MatchResult(BaseModel):
    """匹配结果"""
    document_id: str                 # 文档ID
    total_blocks: int                # 匹配的块总数
    total_comments: int              # 评论总数
    matches: List[BlockMatch]        # 匹配结果列表