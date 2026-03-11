import json
import time
from wrapper import *


class LarkFastAPI:
    """飞书便捷API - 对原始api的二次封装, 自定义某些快速功能"""

    def __init__(self):
        """初始化 LarkWrapper"""
        self.cloud_auth_wrapper = CloudAuthWrapper()
        self.cloud_space_wrapper = CloudSpaceWrapper()
        self.group_manage_wrapper = GroupManageWrapper()
        self.message_manage_wrapper = MessageManageWrapper()

    def send_message_custom(self, chat_id: str, message: str):
        """发送消息 - 自定义: 发送至群组, 文本类消息"""
        content = json.dumps({"text": message}, ensure_ascii=False, indent=2)

        self.message_manage_wrapper.send_message(
            receive_id_type="chat_id",
            receive_id=chat_id,
            msg_type="text",
            content=content,
        )

    def upload_markdown(self, file_path: str, file_name: str):
        """上传本地md文件为docx, 并为机器人所在所有群组添加权限"""
        # Ensure .md extension
        if not file_name.endswith(".md"):
            file_name += ".md"

        # 上传素材方式上传文件
        extra = json.dumps(
            {"obj_type": "docx", "file_extension": "md"}, ensure_ascii=False
        )
        upload_media_result = self.cloud_space_wrapper.upload_all_media(
            file_path, file_name, extra
        )

        # 获取机器人云空间根目录信息
        root_folder_result = self.cloud_space_wrapper.root_folder()

        # 创建导入任务
        import_task_ticket = self.cloud_space_wrapper.create_import_task(
            mount_key=root_folder_result.token,
            file_extension="md",
            file_token=upload_media_result.file_token,
            type="docx",
            file_name=file_name,
        )

        # 查询导入任务情况
        time.sleep(2)
        import_task_result = self.cloud_space_wrapper.get_import_task(
            import_task_ticket.ticket
        )

        # 为文件添加权限
        self.batch_create_permission_member_custom(file_token=import_task_result.token)

    def create_permission_member_custom(
        self,
        file_token: str,
        member_id: str,
    ):
        """
        将指定群组, 添加为目标文件(docx)的管理协作者
        """

        return self.cloud_auth_wrapper.create_permission_member(
            member_type="openchat",
            member_id=member_id,
            perm="full_access",
            perm_type="container",
            type="chat",
            file_type="docx",
            file_token=file_token,
        )

    def batch_create_permission_member_custom(self, file_token: str):
        """将机器人所在全部群组, 添加为目标文件(docx)的管理协作者"""
        list_chat = self.group_manage_wrapper.list_chat()

        self.cloud_auth_wrapper.batch_create_permission_member(
            member_type="openchat",
            member_id_list=list_chat.get_chat_id_list(),
            perm="full_access",
            perm_type="container",
            type="chat",
            file_type="docx",
            file_token=file_token,
        )
