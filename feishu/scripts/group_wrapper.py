import json
from lark_oapi.api.im.v1 import (
    ListChatRequest,
    ListChatResponse,
)
from lark_entity import LarkError, ListChatResult, ListChatItem
from lark_wrapper import BaseWrapper


class GroupWrapper(BaseWrapper):
    """飞书群组 API 封装类"""

    def list_chat(self) -> ListChatResult:
        """
        获取用户或机器人所在的群列表
        https://open.feishu.cn/document/server-docs/group/chat/list
        """
        request: ListChatRequest = ListChatRequest.builder().build()
        response: ListChatResponse = self._client.im.v1.chat.list(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise LarkError(
                method="list_chat",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise LarkError(method="method_name", detail="response.data is null")

        # 处理业务结果
        items = [
            ListChatItem(name=i.name, chat_id=i.chat_id)
            for i in (response.data.items or [])
            if i.chat_id is not None and i.name is not None
        ]
        result = ListChatResult(items=items)
        print(f"✅ list_chat success", result.model_dump_json(indent=2))
        return result
