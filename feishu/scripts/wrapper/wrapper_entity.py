from typing import List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field


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


class ReplyTextRun(BaseModel):
    text: Optional[str] = None


class ReplyDocsLink(BaseModel):
    url: Optional[str] = None


class ReplyPerson(BaseModel):
    user_id: Optional[str] = None


class ReplyElement(BaseModel):
    type: Optional[str] = None
    text_run: Optional[ReplyTextRun] = None
    docs_link: Optional[ReplyDocsLink] = None
    person: Optional[ReplyPerson] = None


class ReplyContent(BaseModel):
    elements: List[ReplyElement] = []


class ReplyExtra(BaseModel):
    image_list: List[str] = []


class ReplyItem(BaseModel):
    reply_id: Optional[str] = None
    user_id: Optional[str] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    content: Optional[ReplyContent] = None
    extra: Optional[ReplyExtra] = None


class ReplyList(BaseModel):
    replies: List[ReplyItem] = []


class CommentItem(BaseModel):
    comment_id: Optional[str] = None
    user_id: Optional[str] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    is_solved: Optional[bool] = None
    solved_time: Optional[int] = None
    solver_user_id: Optional[str] = None
    is_whole: Optional[bool] = None
    quote: Optional[str] = None
    reply_list: Optional[ReplyList] = None


class ListCommentsResult(BaseModel):
    file_token: str
    total_comments: int
    items: List[CommentItem]


# === 文档块相关实体 ===
# 1. 基础类
class BlockItem(BaseModel):
    block_id: Optional[str] = None
    parent_id: Optional[str] = None


# 2. 文本块 (Type 2)
class TextBlockItem(BlockItem):
    block_type: Literal[2] = 2
    elements: List[str] = []


# 3. 标题块 (Type 3-11)
class Heading1BlockItem(BlockItem):
    block_type: Literal[3] = 3
    elements: List[str] = []


class Heading2BlockItem(BlockItem):
    block_type: Literal[4] = 4
    elements: List[str] = []


class Heading3BlockItem(BlockItem):
    block_type: Literal[5] = 5
    elements: List[str] = []


class Heading4BlockItem(BlockItem):
    block_type: Literal[6] = 6
    elements: List[str] = []


class Heading5BlockItem(BlockItem):
    block_type: Literal[7] = 7
    elements: List[str] = []


class Heading6BlockItem(BlockItem):
    block_type: Literal[8] = 8
    elements: List[str] = []


class Heading7BlockItem(BlockItem):
    block_type: Literal[9] = 9
    elements: List[str] = []


class Heading8BlockItem(BlockItem):
    block_type: Literal[10] = 10
    elements: List[str] = []


class Heading9BlockItem(BlockItem):
    block_type: Literal[11] = 11
    elements: List[str] = []


# 4. 图片块 (Type 27)
class ImageBlockItem(BlockItem):
    block_type: Literal[27] = 27
    width: Optional[int] = None
    height: Optional[int] = None
    token: Optional[str] = None
    caption: Optional[str] = None


BlockUnion = Annotated[
    Union[
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
    ],
    Field(discriminator="block_type"),
]


class ListBlocksResult(BaseModel):
    document_id: str
    total_blocks: int
    items: List[BlockUnion]
