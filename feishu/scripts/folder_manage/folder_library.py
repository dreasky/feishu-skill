import json
from pathlib import Path
from typing import Optional
from .entity import FolderItem, FolderStore, FolderStatus


class FolderLibrary:
    """飞书文件库，按 chat_id 隔离存储，以 file_key 为唯一键"""

    def __init__(self, chat_id: str, base_path: Optional[Path] = None):
        self._chat_id = chat_id
        base = base_path or Path(__file__).parent.parent / "data" / "chats"
        self._path = base / chat_id / "library.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> FolderStore:
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return FolderStore(items={k: FolderItem(**v) for k, v in data.items()})
        return FolderStore()

    def _save(self, store: FolderStore) -> None:
        self._path.write_text(
            json.dumps(
                {k: v.model_dump() for k, v in store.items.items()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def add(
        self,
        file_key: str,
        file_name: str,
        message_id: str,
        file_type: str,
        chat_id: str,
        chat_type: str,
        group_uuid: str,
    ) -> bool:
        """新增记录，已存在则跳过。返回是否实际写入。"""
        store = self._load()
        if file_key in store.items:
            return False
        store.items[file_key] = FolderItem(
            file_key=file_key,
            file_name=file_name,
            message_id=message_id,
            file_type=file_type,
            chat_id=chat_id,
            chat_type=chat_type,
            group_uuid=group_uuid,
        )
        self._save(store)
        print(f"📁 新增文件记录: {file_name} [分组: {group_uuid}]")
        return True

    def get(self, file_key: str) -> Optional[FolderItem]:
        """按 file_key 读取单条记录，不存在返回 None。"""
        return self._load().items.get(file_key)

    def remove(self, file_key: str) -> bool:
        """移除记录，不存在返回 False。"""
        store = self._load()
        if file_key not in store.items:
            return False
        del store.items[file_key]
        self._save(store)
        print(f"🗑️ 已移除文件记录: {file_key}")
        return True

    def search(self, keyword: str) -> list[FolderItem]:
        """按 file_name 模糊搜索。"""
        keyword = keyword.lower()
        return [
            item
            for item in self._load().items.values()
            if keyword in item.file_name.lower()
        ]

    def all(self) -> list[FolderItem]:
        """返回全部记录列表。"""
        return list(self._load().items.values())

    def set_downloaded(self, file_key: str, local_path: str) -> bool:
        """标记为已下载。"""
        from .entity import FolderTask
        store = self._load()
        if file_key not in store.items:
            return False
        store.items[file_key].task = FolderTask(
            status=FolderStatus.DOWNLOADED, local_path=local_path
        )
        self._save(store)
        print(f"⬇️ 已下载: {store.items[file_key].file_name} -> {local_path}")
        return True

    def set_submitted(self, file_key: str) -> bool:
        """标记为已提交。"""
        store = self._load()
        if file_key not in store.items:
            return False
        store.items[file_key].task.status = FolderStatus.SUBMITTED
        self._save(store)
        print(f"🚀 已提交: {store.items[file_key].file_name}")
        return True

    def set_failed(self, file_key: str, error: str) -> bool:
        """标记为处理失败。"""
        from .entity import FolderTask
        store = self._load()
        if file_key not in store.items:
            return False
        store.items[file_key].task = FolderTask(
            status=FolderStatus.FAILED, error=error
        )
        self._save(store)
        print(f"❌ 处理失败: {store.items[file_key].file_name} — {error}")
        return True

    def filter_by_status(self, status: FolderStatus) -> list[FolderItem]:
        """按任务状态筛选。"""
        return [
            item for item in self._load().items.values()
            if item.task.status == status
        ]

    def filter_by_group(self, group_uuid: str) -> list[FolderItem]:
        """按分组 UUID 筛选。"""
        return [
            item for item in self._load().items.values()
            if item.group_uuid == group_uuid
        ]

    def list_groups(self) -> list[str]:
        """返回所有分组 UUID（去重）。"""
        return list({item.group_uuid for item in self._load().items.values()})