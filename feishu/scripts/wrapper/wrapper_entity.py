from typing import List, Optional
from pydantic import BaseModel, field_serializer
from lark_oapi.api.docx.v1 import Block, Text
from lark_oapi.api.drive.v1 import FileComment


class SendMessageResult(BaseModel):
    receive_id_type: str
    receive_id: str
    msg_type: str


class ListChatItem(BaseModel):
    name: str
    chat_id: str


class ListChatResult(BaseModel):
    items: List[ListChatItem]

    def get_chat_id_list(self):
        return [item.chat_id for item in self.items]


class RootFolderResult(BaseModel):
    token: str
    id: str
    user_id: str


class FileItem(BaseModel):
    token: str
    name: str
    type: str


class ListFileResult(BaseModel):
    files: List[FileItem]


class UploadMediaResult(BaseModel):
    file_token: str
    file_name: str


class UploadFileResult(BaseModel):
    file_token: str
    file_name: str


class ImportTaskTicket(BaseModel):
    ticket: str


class ImportTaskResult(BaseModel):
    status_text: str
    token: str
    type: str
    url: str


class PermissionMemberResult(BaseModel):
    member_type: str
    member_id: str
    perm: str


class BatchPermissionMemberResult(BaseModel):
    member_count: int


class MessageSender(BaseModel):
    id: Optional[str]
    id_type: Optional[str]
    sender_type: Optional[str]
    tenant_key: Optional[str]


class MessageItem(BaseModel):
    message_id: Optional[str]
    msg_type: Optional[str]
    create_time: Optional[int]
    update_time: Optional[int]
    deleted: Optional[bool]
    updated: Optional[bool]
    chat_id: Optional[str] = None
    root_id: Optional[str] = None
    parent_id: Optional[str] = None
    thread_id: Optional[str] = None
    upper_message_id: Optional[str] = None
    sender: Optional[MessageSender] = None
    content: Optional[str] = None


class ListMessageResult(BaseModel):
    items: List[MessageItem]
    has_more: bool
    page_token: Optional[str] = None


class GetMessageResourceResult(BaseModel):
    file_name: str
    file_path: str


class GetMessageContentResult(BaseModel):
    items: List[MessageItem]


class GetBotInfoResult(BaseModel):
    open_id: str
    app_name: str
    avatar_url: str
    activate_status: int
    ip_white_list: List[str]


# === 评论相关实体 ===
class FileCommentWrapper:
    """FileComment 包装类，使用组合而非继承"""

    def __init__(self, comment: FileComment):
        object.__setattr__(self, '_comment', comment)

    def __getattr__(self, name):
        return getattr(self._comment, name)

    @property
    def comment_id(self) -> Optional[str]:
        return self._comment.comment_id

    @property
    def quote(self) -> Optional[str]:
        return self._comment.quote

    @property
    def reply_list(self):
        return self._comment.reply_list

    def extract_comment_replies(self) -> List[str]:
        """提取评论的所有回复内容"""
        if not self.reply_list:
            return []

        replies = []
        for reply in self.reply_list.replies or []:
            if not reply.content:
                continue

            for elem in reply.content.elements or []:
                if not elem.text_run:
                    continue
                if not elem.text_run.text:
                    continue

                replies.append(elem.text_run.text)
        return replies


class ListCommentsResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    file_token: str
    total_comments: int
    items: List[FileCommentWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[FileCommentWrapper]) -> List[dict]:
        def serialize_value(v):
            """递归序列化值"""
            if v is None:
                return None
            if isinstance(v, (str, int, float, bool)):
                return v
            if isinstance(v, list):
                return [serialize_value(item) for item in v]
            if hasattr(v, "__dict__"):
                result = {}
                for k2, v2 in v.__dict__.items():
                    if v2 is not None:
                        result[k2] = serialize_value(v2)
                return result if result else None
            return str(v)

        def serialize_item(item: FileCommentWrapper) -> dict:
            result = {}
            if hasattr(item._comment, "__dict__"):
                for k, v in item._comment.__dict__.items():
                    if v is not None:
                        result[k] = serialize_value(v)
            return result

        return [serialize_item(item) for item in items]


# === 文档块相关实体 ===

# 所有文本类 Block 类型（包含 Text 属性）
BLOCK_TEXT_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17]
BLOCK_TEXT_TYPES_TO_ATTR = {
    1: "page",
    2: "text",
    3: "heading1",
    4: "heading2",
    5: "heading3",
    6: "heading4",
    7: "heading5",
    8: "heading6",
    9: "heading7",
    10: "heading8",
    11: "heading9",
    12: "bullet",
    13: "ordered",
    14: "code",
    15: "quote",
    17: "todo",
}
BLOCK_IMAGE_TYPE = 27  # 图片


class BlockWrapper:
    """Block 包装类，使用组合而非继承，避免 SDK Block 类的 __getattr__ 问题"""

    def __init__(self, block: Block):
        object.__setattr__(self, '_block', block)

    def __getattr__(self, name):
        # 转发到内部 block
        return getattr(self._block, name)

    @property
    def block_type(self) -> Optional[int]:
        return self._block.block_type

    @property
    def block_id(self) -> Optional[str]:
        return self._block.block_id

    def is_text_block(self) -> bool:
        return self.block_type in BLOCK_TEXT_TYPES

    def get_text_attr(self) -> Optional[Text]:
        """获取块的 Text 属性"""
        if not self.is_text_block():
            return None

        if not self.block_type:
            return None

        attr_name = BLOCK_TEXT_TYPES_TO_ATTR[self.block_type]
        return getattr(self._block, attr_name, None)

    def extract_block_content(self) -> str:
        """提取文本块的完整文本内容"""
        if not self.is_text_block():
            return ""

        text_attr = self.get_text_attr()
        if not text_attr:
            return ""
        if not text_attr.elements:
            return ""

        parts = [
            elem.text_run.content
            for elem in text_attr.elements
            if elem.text_run and elem.text_run.content
        ]
        return "".join(parts)

    def extract_comment_ids(self) -> List[str]:
        """从块中提取所有 comment_ids"""
        if not self.is_text_block():
            return []

        text_attr = self.get_text_attr()
        if not text_attr:
            return []
        if not text_attr.elements:
            return []

        comment_ids = []
        for elem in text_attr.elements:
            if not elem.text_run:
                continue

            if not elem.text_run.text_element_style:
                continue

            if not elem.text_run.text_element_style.comment_ids:
                continue

            comment_ids.extend(elem.text_run.text_element_style.comment_ids)

        return comment_ids


class ListBlocksResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    document_id: str
    total_blocks: int
    items: List[BlockWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[BlockWrapper]) -> List[dict]:
        def serialize_value(v):
            """递归序列化值"""
            if v is None:
                return None
            if isinstance(v, (str, int, float, bool)):
                return v
            if isinstance(v, list):
                return [serialize_value(item) for item in v]
            if hasattr(v, "__dict__"):
                result = {}
                for k2, v2 in v.__dict__.items():
                    if v2 is not None:
                        result[k2] = serialize_value(v2)
                return result if result else None
            return str(v)

        def serialize_item(item: BlockWrapper) -> dict:
            result = {}
            if hasattr(item._block, "__dict__"):
                for k, v in item._block.__dict__.items():
                    if v is not None:
                        result[k] = serialize_value(v)
            return result

        return [serialize_item(item) for item in items]
