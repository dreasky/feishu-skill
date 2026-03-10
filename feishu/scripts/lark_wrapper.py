import os
import json
import requests
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from lark_oapi.api.drive.v1 import *
from lark_auth import LarkAuth


class LarkError(Exception):
    """Base exception for Lark wrapper errors."""

    def __init__(self, message: str, code: str = "UNKNOWN", recovery: str = ""):
        self.message = message
        self.code = code
        self.recovery = recovery
        super().__init__(message)


class LarkWrapper:
    """飞书API封装类"""

    def __init__(self):
        """初始化 LarkWrapper"""
        self._auth = LarkAuth()
        self._client = self._auth.get_client()
        self._tenant_access_token = self._auth.get_tenant_access_token()
        self.base_url = self._auth.get_base_url()

    # === 消息 API ===

    def send_text(self, chat_id: str, message: str):
        """发送消息"""
        request: CreateMessageRequest = (
            CreateMessageRequest.builder()
            .receive_id_type("chat_id")
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": message}, ensure_ascii=False))
                .build()
            )
            .build()
        )

        # 发起请求
        response: CreateMessageResponse = self._client.im.v1.message.create(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            print(f"❌ 发送失败, chat_id: {chat_id}")
            return

        # 处理业务结果
        print(f"✅ 发送成功, chat_id: {chat_id}")

    # === 群组 API ===

    def list_chat(self):
        """获取用户或机器人所在的群列表"""
        request: ListChatRequest = ListChatRequest.builder().build()
        response: ListChatResponse = self._client.im.v1.chat.list(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.im.v1.chat.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return

        if response.data and response.data.items:
            results = [
                {"name": i.name, "chat_id": i.chat_id} for i in response.data.items
            ]
            print(json.dumps(results, indent=2))

    # === 云文档 API ===

    def root_folder(self):
        """获取我的空间（根文件夹）元数据"""
        url = self.base_url + "/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {self._tenant_access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            print("❌ fail", json.dumps(result, ensure_ascii=False, indent=2))
            return

        data = result.get("data")
        print("✅ success", json.dumps(data, ensure_ascii=False, indent=2))

    def list_file(self):
        """获取文件夹中的文件清单"""
        request: ListFileRequest = ListFileRequest.builder().build()
        response: ListFileResponse = self._client.drive.v1.file.list(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.drive.v1.file.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return

        # 处理业务结果
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    def upload_markdown(self, file_path: str):
        """上传markdown文档"""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file = open(file_path, "rb")
        request: UploadAllMediaRequest = (
            UploadAllMediaRequest.builder()
            .request_body(
                UploadAllMediaRequestBody.builder()
                .file_name(file_name)
                .parent_type("ccm_import_open")
                .size(file_size)
                .extra('{"obj_type":"docx","file_extension":"md"}')
                .file(file)
                .build()
            )
            .build()
        )
        response: UploadAllMediaResponse = self._client.drive.v1.media.upload_all(
            request
        )

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.drive.v1.media.upload_all failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return
        # 处理业务结果
        if response.data is None or response.data.file_token is None:
            print("❌ 错误：上传文件失败, 请重试")
            return
        file_token = response.data.file_token

        print(f"✅ 文件上传成功，file_token: {file_token}，file_name: {file_name}")

    def import_task(
        self,
        file_token: str,
        file_name: str,
        mount_key: str = "GRwZfesLylPqtgd7VgfcF9UXnqh",
    ):
        """创建导入任务"""
        request: CreateImportTaskRequest = (
            CreateImportTaskRequest.builder()
            .request_body(
                ImportTask.builder()
                .file_extension("md")
                .file_token(file_token)
                .type("docx")
                .file_name(file_name)
                .point(
                    ImportTaskMountPoint.builder()
                    .mount_type(1)
                    .mount_key(mount_key)
                    .build()
                )
                .build()
            )
            .build()
        )
        response: CreateImportTaskResponse = self._client.drive.v1.import_task.create(
            request
        )

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.drive.v1.import_task.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return

        # 处理业务结果
        if response.data and response.data.ticket:
            print(f"✅ 导入任务创建成功，ticket: {response.data.ticket}")
        else:
            print("❌ 错误：创建导入任务失败,请重试")

    def get_import_task(self, ticket: str):
        """查询导入任务结果"""
        request: GetImportTaskRequest = (
            GetImportTaskRequest.builder().ticket(ticket).build()
        )

        # 发起请求
        response: GetImportTaskResponse = self._client.drive.v1.import_task.get(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.drive.v1.import_task.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
            )
            return

        # 处理业务结果 - 使用 lark.JSON.marshal 方法
        lark.logger.info(lark.JSON.marshal(response.data, indent=2))

        # 解析任务状态
        if response.data is None or response.data.result is None:
            lark.logger.error(f"返回数据异常")
            return
        result = response.data.result

        if result.job_status is None:
            lark.logger.error(f"返回数据异常")
            return
        job_status = result.job_status
        job_status_map = {0: "导入成功", 1: "初始化", 2: "处理中", 3: "内部错误"}
        status_text = job_status_map.get(
            job_status,
            f"job_status-{job_status}, 详情查阅https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/get",
        )

        print(f"📊 任务状态: {status_text}")
        if hasattr(result, "token") and result.token:
            print(f"📄 文档 Token: {result.token}")
        if hasattr(result, "url") and result.url:
            print(f"🔗 文档 URL: {result.url}")
