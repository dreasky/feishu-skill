import uuid
from pathlib import Path
from pydantic import BaseModel


class GroupState(BaseModel):
    current_uuid: str


class GroupManager:
    """分组管理器，持久化当前分组 UUID"""

    def __init__(self, path: Path = None):
        self._path = path or Path(__file__).parent.parent / "data" / "group_state.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> GroupState:
        if self._path.exists():
            import json
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return GroupState(**data)
        return GroupState(current_uuid=str(uuid.uuid4()))

    def _save(self, state: GroupState) -> None:
        import json
        self._path.write_text(
            json.dumps(state.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_current(self) -> str:
        """获取当前分组 UUID"""
        return self._load().current_uuid

    def new_group(self) -> str:
        """创建新分组，返回新 UUID"""
        state = GroupState(current_uuid=str(uuid.uuid4()))
        self._save(state)
        print(f"📌 开启新分组: {state.current_uuid[:8]}...")
        return state.current_uuid