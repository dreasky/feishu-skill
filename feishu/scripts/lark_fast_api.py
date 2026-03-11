import json
import time
from lark_entity import *
from message_wrapper import MessageWrapper
from group_wrapper import GroupWrapper
from cloud_document_wrapper import CloudDocumentWrapper


class LarkFastAPI:
    """飞书便捷API - 对原始api的二次封装, 自定义某些快速功能"""

    def __init__(self):
        """初始化 LarkWrapper"""
        self.message_wrapper = MessageWrapper()
        self.group_wrapper = GroupWrapper()
        self.cloud_document_wrapper = CloudDocumentWrapper()

    # === 消息 API ===

    def send_message_custom(self, chat_id: str, message: str) -> SendMessageResult:
        """发送消息 - 自定义: 发送至群组, 文本类消息"""
        content = json.dumps({"text": message}, ensure_ascii=False, indent=2)

        return self.message_wrapper.send_message(
            receive_id_type="chat_id",
            receive_id=chat_id,
            msg_type="text",
            content=content,
        )

    # === 群组 API ===

    # === 云文档 API ===

    def upload_markdown(self, file_path: str, file_name: str):
        """上传本地md文件为docx, 并为机器人所在所有群组添加权限"""
        # Ensure .md extension
        if not file_name.endswith(".md"):
            file_name += ".md"

        # 上传素材方式上传文件
        extra = json.dumps(
            {"obj_type": "docx", "file_extension": "md"}, ensure_ascii=False
        )
        upload_media_result = self.cloud_document_wrapper.upload_all_media(
            file_path, file_name, extra
        )

        # 创建导入任务
        import_task_ticket = self.create_import_task_custom(
            upload_media_result.file_token, file_name
        )

        # 查询导入任务情况
        time.sleep(2)
        import_task_result = self.cloud_document_wrapper.get_import_task(
            import_task_ticket.ticket
        )

        # 为文件添加权限
        self.batch_create_permission_member_custom(file_token=import_task_result.token)

    def create_import_task_custom(
        self, file_token: str, file_name: str
    ) -> ImportTaskTicket:
        """创建导入任务 - 自定义: 挂载根文件夹, 源文件格式md, 目标文件格式:docx"""

        root_folder_result = self.cloud_document_wrapper.root_folder()

        return self.cloud_document_wrapper.create_import_task(
            mount_key=root_folder_result.token,
            file_extension="md",
            file_token=file_token,
            type="docx",
            file_name=file_name,
        )

    def create_permission_member_custom(
        self,
        file_token: str,
        member_id: str,
    ) -> PermissionMemberResult:
        """
        将指定群组, 添加为目标文件(docx)的管理协作者
        """

        return self.cloud_document_wrapper.create_permission_member(
            member_type="openchat",
            member_id=member_id,
            perm="full_access",
            perm_type="container",
            type="chat",
            file_type="docx",
            file_token=file_token,
        )

    def batch_create_permission_member_custom(
        self, file_token: str
    ) -> BatchPermissionMemberResult:
        """将机器人所在全部群组 , 添加为目标文件(docx)的管理协作者"""
        list_chat = self.group_wrapper.list_chat()

        return self.cloud_document_wrapper.batch_create_permission_member(
            member_type="openchat",
            member_id_list=list_chat.get_chat_id_list(),
            perm="full_access",
            perm_type="container",
            type="chat",
            file_type="docx",
            file_token=file_token,
        )
