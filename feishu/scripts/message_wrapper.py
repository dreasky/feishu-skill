import json
from lark_oapi.api.im.v1 import (
    CreateMessageRequestBody,
    CreateMessageRequest,
    CreateMessageResponse,
)
from lark_entity import (
    LarkError,
    SendMessageResult,
)
from lark_wrapper import BaseWrapper


class MessageWrapper(BaseWrapper):
    # === 消息 API ===

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
            raise LarkError(
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
