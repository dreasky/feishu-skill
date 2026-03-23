import json
import lark_oapi as lark
from pathlib import Path
from typing import Optional
from .folder_library import FolderLibrary
from .group_manager import GroupManager
from .confirm_state_manager import ConfirmStateManager
from .entity import ConfirmState


class FileCollectorBot:
    """飞书文件收集机器人，监听消息并管理文件分组（按会话隔离）"""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        bot_open_id: str,
        base_path: Optional[Path] = None,
    ):
        self._bot_open_id = bot_open_id
        self._base_path = base_path
        self._libraries: dict[str, FolderLibrary] = {}
        self._group_managers: dict[str, GroupManager] = {}
        self._confirm_states = ConfirmStateManager()
        self._message_wrapper = None  # 延迟初始化，避免循环导入
        self._ws_client = self._create_ws_client(app_id, app_secret)

    def _get_message_wrapper(self):
        """延迟初始化 MessageManageWrapper"""
        if self._message_wrapper is None:
            from wrapper import MessageManageWrapper
            self._message_wrapper = MessageManageWrapper()
        return self._message_wrapper

    def _get_library(self, chat_id: str) -> FolderLibrary:
        if chat_id not in self._libraries:
            self._libraries[chat_id] = FolderLibrary(chat_id, self._base_path)
        return self._libraries[chat_id]

    def _get_group_manager(self, chat_id: str) -> GroupManager:
        if chat_id not in self._group_managers:
            self._group_managers[chat_id] = GroupManager(chat_id, self._base_path)
        return self._group_managers[chat_id]

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
        chat_id = message.chat_id
        chat_type = message.chat_type

        # 检查是否 @ 机器人
        is_at_bot = any(
            m.id and m.id.open_id == self._bot_open_id
            for m in mentions
        )

        # @ 机器人 -> 检查文件并发送确认
        if is_at_bot:
            self._handle_at_bot(chat_id)
            return

        # 文本消息 -> 处理确认/取消
        if msg_type == "text" and self._confirm_states.is_waiting(chat_id):
            self._handle_confirm_message(message, chat_id)
            return

        # file 类型消息 -> 记录文件
        if msg_type == "file" and message.content:
            self._handle_file_message(message, chat_id, chat_type)

    def _handle_at_bot(self, chat_id: str) -> None:
        """处理 @ 机器人"""
        library = self._get_library(chat_id)
        group_manager = self._get_group_manager(chat_id)

        # 获取当前分组的文件列表
        group_uuid = group_manager.get_current()
        files = library.filter_by_group(group_uuid)

        if not files:
            # 没有文件，直接开启新分组
            group_manager.new_group()
            return

        # 有文件，发送确认消息
        self._send_confirm_message(chat_id, group_uuid, files)
        self._confirm_states.set_waiting(chat_id, group_uuid, len(files))

    def _send_confirm_message(
        self, chat_id: str, group_uuid: str, files: list
    ) -> None:
        """发送确认消息"""
        file_list = "\n".join([f"  - {f.file_name}" for f in files])
        content = json.dumps(
            {
                "text": f"📦 收到 {len(files)} 个文件：\n{file_list}\n\n"
                f"请回复 yes 确认处理，或回复 no 取消并重新上传。"
            },
            ensure_ascii=False,
        )
        try:
            self._get_message_wrapper().send_message(
                receive_id_type="chat_id",
                receive_id=chat_id,
                msg_type="text",
                content=content,
            )
        except Exception as e:
            print(f"❌ 发送确认消息失败: {e}")

    def _handle_confirm_message(self, message, chat_id: str) -> None:
        """处理确认/取消消息"""
        content = json.loads(message.content)
        text = content.get("text", "").strip().lower()

        state = self._confirm_states.get_waiting(chat_id)
        if not state:
            return

        self._confirm_states.clear_waiting(chat_id)

        if text == "yes":
            self._handle_confirm_yes(chat_id, state)
        elif text == "no":
            self._handle_confirm_no(chat_id, state)
        else:
            # 无效回复，重新设置等待状态
            self._confirm_states.set_waiting(
                chat_id, state.group_uuid, state.file_count
            )

    def _handle_confirm_yes(self, chat_id: str, state: ConfirmState) -> None:
        """确认处理"""
        # TODO: 调用 Claude 接口
        self._send_text_message(chat_id, "✅ 已确认，正在处理...")
        # 开启新分组
        self._get_group_manager(chat_id).new_group()

    def _handle_confirm_no(self, chat_id: str, state: ConfirmState) -> None:
        """取消处理"""
        library = self._get_library(chat_id)
        # 移除该分组的所有文件
        files = library.filter_by_group(state.group_uuid)
        for f in files:
            library.remove(f.file_key)
        self._send_text_message(
            chat_id, "❌ 已取消，请重新上传文件后再 @ 我。"
        )
        # 开启新分组
        self._get_group_manager(chat_id).new_group()

    def _send_text_message(self, chat_id: str, text: str) -> None:
        """发送文本消息"""
        content = json.dumps({"text": text}, ensure_ascii=False)
        try:
            self._get_message_wrapper().send_message(
                receive_id_type="chat_id",
                receive_id=chat_id,
                msg_type="text",
                content=content,
            )
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")

    def _handle_file_message(self, message, chat_id: str, chat_type: str) -> None:
        content = json.loads(message.content)
        file_key = content.get("file_key")
        file_name = content.get("file_name", "")
        if file_key:
            group_uuid = self._get_group_manager(chat_id).get_current()
            self._get_library(chat_id).add(
                file_key, file_name, chat_id, chat_type, group_uuid
            )

    def start(self) -> None:
        print("🚀 启动飞书长连接...")
        self._ws_client.start()