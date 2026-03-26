from typing import List, Optional
from pydantic import BaseModel
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
class FileCommentWrapper(FileComment):

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
    file_token: str
    total_comments: int
    items: List[FileCommentWrapper]


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


class BlockWrapper(Block):

    def is_text_block(self):
        return self.block_type in BLOCK_TEXT_TYPES

    def get_text_attr(self) -> Optional[Text]:
        """获取块的 Text 属性"""
        if not self.is_text_block():
            return None

        if not self.block_type:
            return None

        attr_name = BLOCK_TEXT_TYPES_TO_ATTR[self.block_type]
        return getattr(self, attr_name, None)

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
    document_id: str
    total_blocks: int
    items: List[BlockWrapper]
