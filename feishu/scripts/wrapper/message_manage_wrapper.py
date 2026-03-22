import json
from pathlib import Path
from lark_oapi.api.im.v1 import (
    CreateMessageRequestBody,
    CreateMessageRequest,
    CreateMessageResponse,
    ListMessageRequest,
    ListMessageResponse,
    GetMessageResourceRequest,
    GetMessageResourceResponse,
)
from .wrapper_entity import *
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class MessageManageWrapper(BaseWrapper):
    """飞书消息 - 消息管理 API 封装
    https://open.feishu.cn/document/server-docs/im-v1/message/intro
    """

    def send_message(
        self,
        receive_id_type: str,
        receive_id: str,
        msg_type: str,
        content: str,
    ) -> SendMessageResult:
        """
        发送消息
        https://open.feishu.cn/document/server-docs/im-v1/message/create
        """
        # 构造消息请求体
        create_message_request_body = (
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type(msg_type)
            .content(content)
            .build()
        )

        # 构造请求对象
        request: CreateMessageRequest = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(create_message_request_body)
            .build()
        )

        # 发起请求
        response: CreateMessageResponse = self._client.im.v1.message.create(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="send_message",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        result = SendMessageResult(
            receive_id_type=receive_id_type, receive_id=receive_id, msg_type=msg_type
        )

        print(f"✅ send_message success", result.model_dump_json(indent=2))
        return result

    def list_messages(
        self,
        container_id_type: str,
        container_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        sort_type: str = "ByCreateTimeAsc",
        page_size: int = 20,
        page_token: Optional[str] = None,
    ) -> ListMessageResult:
        """
        获取会话历史消息
        https://open.feishu.cn/document/server-docs/im-v1/message/list
        """
        builder = (
            ListMessageRequest.builder()
            .container_id_type(container_id_type)
            .container_id(container_id)
            .sort_type(sort_type)
            .page_size(page_size)
        )
        if start_time is not None:
            builder = builder.start_time(start_time)
        if end_time is not None:
            builder = builder.end_time(end_time)
        if page_token is not None:
            builder = builder.page_token(page_token)

        request: ListMessageRequest = builder.build()
        response: ListMessageResponse = self._client.im.v1.message.list(request)

        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="list_messages",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="list_messages", detail="response.data is null")

        items = []
        for msg in (response.data.items or []):
            sender = None
            if msg.sender:
                sender = MessageSender(
                    id=msg.sender.id,
                    id_type=msg.sender.id_type,
                    sender_type=msg.sender.sender_type,
                    tenant_key=msg.sender.tenant_key,
                )
            items.append(MessageItem(
                message_id=msg.message_id,
                msg_type=msg.msg_type,
                create_time=msg.create_time,
                update_time=msg.update_time,
                deleted=msg.deleted,
                updated=msg.updated,
                chat_id=msg.chat_id,
                root_id=msg.root_id,
                parent_id=msg.parent_id,
                thread_id=msg.thread_id,
                upper_message_id=msg.upper_message_id,
                sender=sender,
                content=msg.body.content if msg.body else None,
            ))

        result = ListMessageResult(
            items=items,
            has_more=response.data.has_more or False,
            page_token=response.data.page_token,
        )
        print(f"✅ list_messages success", result.model_dump_json(indent=2))
        return result

    def get_message_resource(
        self,
        message_id: str,
        file_key: str,
        type: str,
        save_dir: str,
    ) -> GetMessageResourceResult:
        """
        获取消息中的资源文件（图片、音频、视频、文件）
        https://open.feishu.cn/document/server-docs/im-v1/message-content/get-2
        """
        request: GetMessageResourceRequest = (
            GetMessageResourceRequest.builder()
            .message_id(message_id)
            .file_key(file_key)
            .type(type)
            .build()
        )
        response: GetMessageResourceResponse = self._client.im.v1.message_resource.get(request)

        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="get_message_resource",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.file is None:
            raise WrapperError(method="get_message_resource", detail="response.file is null")

        save_path = Path(save_dir) / response.file_name
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.file.read())

        result = GetMessageResourceResult(
            file_name=response.file_name,
            file_path=str(save_path),
        )
        print(f"✅ get_message_resource success", result.model_dump_json(indent=2))
        return result

