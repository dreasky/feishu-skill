from typing import List, Optional
from pydantic import BaseModel


class LarkError(Exception):
    """飞书 API 调用异常，结构化存储错误详情。"""

    def __init__(
        self,
        method: str,
        code: Optional[int] = None,
        msg: Optional[str] = None,
        log_id: Optional[str] = None,
        resp: Optional[dict] = None,
        detail: Optional[str] = None,
    ):
        self.method = method
        self.code = code
        self.msg = msg
        self.log_id = log_id
        self.resp = resp
        self.detail = detail

        parts = [f"❌ {method} failed"]
        if code is not None:
            parts.append(f"code={code}")
        if msg:
            parts.append(f"msg={msg}")
        if log_id:
            parts.append(f"log_id={log_id}")
        if detail:
            parts.append(detail)
        super().__init__(", ".join(parts))


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
