import json
import lark_oapi as lark
from .folder_library import FolderLibrary
from .group_manager import GroupManager


class FileCollectorBot:
    """飞书文件收集机器人，监听消息并管理文件分组"""

    def __init__(self, app_id: str, app_secret: str, bot_open_id: str):
        self._bot_open_id = bot_open_id
        self._folder_library = FolderLibrary()
        self._group_manager = GroupManager()
        self._ws_client = self._create_ws_client(app_id, app_secret)

    def _create_ws_client(self, app_id: str, app_secret: str) -> lark.ws.Client:
        event_handler = (
            lark.EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(self._on_message_receive)
            .build()
        )
        return lark.ws.Client(
            app_id,
            app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO,
        )

    def _on_message_receive(self, data: lark.im.v1.P2ImMessageReceiveV1) -> None:
        message = data.event.message
        mentions = message.mentions or []
        msg_type = message.message_type

        # 检查是否 @ 机器人
        is_at_bot = any(
            m.id and m.id.open_id == self._bot_open_id
            for m in mentions
        )

        # @ 机器人 -> 开启新分组
        if is_at_bot:
            self._group_manager.new_group()
            return

        # file 类型消息 -> 记录文件
        if msg_type == "file" and message.content:
            self._handle_file_message(message)

    def _handle_file_message(self, message) -> None:
        content = json.loads(message.content)
        file_key = content.get("file_key")
        file_name = content.get("file_name", "")
        if file_key:
            group_uuid = self._group_manager.get_current()
            self._folder_library.add(file_key, file_name, group_uuid)

    def start(self) -> None:
        group_uuid = self._group_manager.get_current()
        print(f"🚀 启动飞书长连接... 当前分组: {group_uuid[:8]}...")
        self._ws_client.start()