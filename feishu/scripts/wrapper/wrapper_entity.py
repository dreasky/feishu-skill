from typing import List, Optional, Any
from pydantic import BaseModel, field_serializer
from lark_oapi.api.docx.v1 import Block, Text
from lark_oapi.api.drive.v1 import FileComment
from lark_oapi.api.im.v1 import Message


# === 通用序列化工具 ===
def _serialize_value(v: Any) -> Any:
    """递归序列化值"""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, list):
        return [_serialize_value(item) for item in v]
    if hasattr(v, "__dict__"):
        result = {}
        for k2, v2 in v.__dict__.items():
            if v2 is not None:
                result[k2] = _serialize_value(v2)
        return result if result else None
    return str(v)


def _serialize_wrapper_items(items: List[Any], inner_attr: str) -> List[dict]:
    """
    序列化 Wrapper 列表

    Args:
        items: Wrapper 对象列表
        inner_attr: 内部 SDK 对象的属性名，如 '_block', '_comment', '_message'
    """
    result_list = []
    for item in items:
        result = {}
        inner_obj = getattr(item, inner_attr, None)
        if inner_obj and hasattr(inner_obj, "__dict__"):
            for k, v in inner_obj.__dict__.items():
                if v is not None:
                    result[k] = _serialize_value(v)
        result_list.append(result)
    return result_list


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


# === 消息相关实体 ===
class MessageWrapper:
    """
    Message 包装类 (组合模式)。

    设计意图：
    1. 使用组合避免继承 SDK 类带来的 __getattr__ 冲突。
    2. 使用 __getattr__ 动态转发所有属性访问。
    3. 使用类型注解欺骗 IDE，提供智能提示，不影响运行时转发逻辑。
    """

    def __init__(self, message: Message):
        object.__setattr__(self, "_message", message)

    # 类型注解（不赋值），仅用于 IDE 智能提示
    message_id: Optional[str]
    msg_type: Optional[str]
    create_time: Optional[int]
    update_time: Optional[int]
    deleted: Optional[bool]
    updated: Optional[bool]
    chat_id: Optional[str]
    root_id: Optional[str]
    parent_id: Optional[str]
    thread_id: Optional[str]
    upper_message_id: Optional[str]
    content: Optional[str]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._message, name)


class ListMessageResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    has_more: bool
    page_token: Optional[str] = None
    items: List[MessageWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[MessageWrapper]) -> List[dict]:
        return _serialize_wrapper_items(items, "_message")


class GetMessageResourceResult(BaseModel):
    file_name: str
    file_path: str


class GetMessageContentResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    items: List[MessageWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[MessageWrapper]) -> List[dict]:
        return _serialize_wrapper_items(items, "_message")


# === 机器人信息实体 ===
class GetBotInfoResult(BaseModel):
    open_id: str
    app_name: str
    avatar_url: str
    activate_status: int
    ip_white_list: List[str]


# === 评论相关实体 ===
class FileCommentWrapper:
    """
    FileComment 包装类 (组合模式)。

    设计意图：
    1. 使用组合避免继承 SDK 类带来的 __getattr__ 冲突。
    2. 使用 __getattr__ 动态转发所有属性访问。
    3. 使用类型注解欺骗 IDE，提供智能提示，不影响运行时转发逻辑。
    """

    def __init__(self, comment: FileComment):
        object.__setattr__(self, "_comment", comment)

    # 类型注解（不赋值），仅用于 IDE 智能提示
    comment_id: Optional[str]
    quote: Optional[str]
    reply_list: Optional[Any]
    content: Optional[Any]
    user_id: Optional[str]
    create_time: Optional[int]
    is_whole: Optional[bool]
    is_solved: Optional[bool]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._comment, name)

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
        return _serialize_wrapper_items(items, "_comment")


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
    """
    Block 包装类 (组合模式)。

    设计意图：
    1. 使用组合避免继承 SDK 类带来的 __getattr__ 冲突。
    2. 使用 __getattr__ 动态转发所有属性访问。
    3. 使用类型注解欺骗 IDE，提供智能提示，不影响运行时转发逻辑。
    """

    def __init__(self, block: Block):
        object.__setattr__(self, "_block", block)

    # 类型注解（不赋值），仅用于 IDE 智能提示
    block_id: Optional[str]
    block_type: Optional[int]
    parent_id: Optional[str]
    children: Optional[List[str]]
    text: Optional[Text]
    heading1: Optional[Text]
    heading2: Optional[Text]
    heading3: Optional[Text]
    heading4: Optional[Text]
    heading5: Optional[Text]
    heading6: Optional[Text]
    heading7: Optional[Text]
    heading8: Optional[Text]
    heading9: Optional[Text]
    bullet: Optional[Text]
    ordered: Optional[Text]
    code: Optional[Text]
    quote: Optional[Text]
    todo: Optional[Text]
    page: Optional[Text]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._block, name)

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
        return _serialize_wrapper_items(items, "_block")
