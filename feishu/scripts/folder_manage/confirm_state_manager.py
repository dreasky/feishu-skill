from pathlib import Path
from typing import Optional
import json
from .entity import ConfirmState


class ConfirmStateManager:
    """确认状态管理器，按 chat_id 管理"""

    def __init__(self, base_path: Optional[Path] = None):
        self._base_path = base_path or Path(__file__).parent.parent / "data"
        self._states: dict[str, ConfirmState] = {}

    def set_waiting(self, chat_id: str, group_uuid: str, file_count: int) -> None:
        """设置等待确认状态"""
        self._states[chat_id] = ConfirmState(
            group_uuid=group_uuid, file_count=file_count
        )

    def get_waiting(self, chat_id: str) -> Optional[ConfirmState]:
        """获取等待确认状态"""
        return self._states.get(chat_id)

    def clear_waiting(self, chat_id: str) -> None:
        """清除等待确认状态"""
        self._states.pop(chat_id, None)

    def is_waiting(self, chat_id: str) -> bool:
        """是否在等待确认"""
        return chat_id in self._states