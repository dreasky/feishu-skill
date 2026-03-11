from typing import List
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
