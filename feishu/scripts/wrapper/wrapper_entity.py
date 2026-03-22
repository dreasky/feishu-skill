from typing import List, Optional
from pydantic import BaseModel


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
