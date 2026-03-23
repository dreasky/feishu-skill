import uuid
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class FolderStatus(str, Enum):
    PENDING = "待处理"
    DOWNLOADED = "已下载"
    SUBMITTED = "已提交"
    FAILED = "处理失败"


class FolderTask(BaseModel):
    status: FolderStatus = FolderStatus.PENDING
    local_path: Optional[str] = None
    error: Optional[str] = None


class FolderItem(BaseModel):
    file_key: str
    file_name: str
    chat_id: str
    chat_type: str
    group_uuid: str
    task: FolderTask = FolderTask()


class FolderStore(BaseModel):
    items: dict[str, FolderItem] = {}


class GroupState(BaseModel):
    current_uuid: str


class ConfirmState(BaseModel):
    group_uuid: str      # 等待确认的分组
    file_count: int      # 文件数量