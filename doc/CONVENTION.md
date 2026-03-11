# 给 AI Agent 的飞书 Wrapper 开发规范

## 文件结构

```text
feishu/scripts/
├── lark_wrapper.py          # BaseWrapper 基类（不添加业务方法）
├── lark_entity.py           # 所有实体类（Result / Item / Error）
├── lark_auth.py             # 鉴权（不修改）
├── message_wrapper.py       # 消息 API
├── group_wrapper.py         # 群组 API
├── cloud_document_wrapper.py # 云文档 API
└── {module}_wrapper.py      # 新增模块按此命名
```

## 新增 Wrapper 文件

每个 `*_wrapper.py` 继承 `BaseWrapper`，只包含对应飞书服务端 API 模块的方法。

```python
# {module}_wrapper.py
import json
from lark_oapi.api.{service}.{version} import (
    XxxRequest,
    XxxResponse,
    # 只导入本文件用到的类，不用 *
)
from lark_wrapper import BaseWrapper
from lark_entity import LarkError, XxxResult


class XxxWrapper(BaseWrapper):
    """飞书 Xxx API 封装类"""

    def do_something(self, param: str) -> XxxResult:
        """
        方法说明
        https://open.feishu.cn/document/...（官方文档链接）
        """
        # 构造请求
        request: XxxRequest = XxxRequest.builder().param(param).build()

        # 发起请求
        response: XxxResponse = self._client.xxx.v1.yyy.zzz(request)

        # 处理失败返回
        if not response.success():
            raise LarkError(
                method="do_something",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=json.loads(response.raw.content),
            )

        # 处理业务结果
        result = XxxResult(field=response.data.field)
        print(f"✅ do_something success", result.model_dump_json(indent=2))
        return result
```

## 新增实体类（lark_entity.py）

所有 Result / Item 类统一放在 `lark_entity.py`，使用 Pydantic `BaseModel`。

```python
# lark_entity.py
class XxxItem(BaseModel):
    """列表子项，字段全部必填"""
    id: str
    name: str

class XxxResult(BaseModel):
    """方法返回值，可选字段用 Optional"""
    items: List[XxxItem]
    token: Optional[str] = None
```

命名规则：

| 场景 | 命名示例 |
|------|----------|
| 列表子项 | `ListChatItem`, `FileItem` |
| 方法返回值 | `SendMessageResult`, `ListChatResult`, `UploadMediaResult` |
| 中间数据（如 ticket） | `ImportTaskTicket` |

## 错误处理规范

`LarkError` 将错误详情拆分为独立字段，便于上层捕获后按需处理：

```python
class LarkError(Exception):
    method: str           # 方法名，如 "send_message"
    code: Optional[int]   # 飞书错误码
    msg: Optional[str]    # 飞书错误描述
    log_id: Optional[str] # 请求 log_id，用于排查
    resp: Optional[dict]  # 原始响应体（已解析为 dict）
    detail: Optional[str] # 补充说明，如"返回结果为空"
```

三种场景的用法：

```python
# 1. SDK 响应失败
if not response.success():
    resp_data = (
        json.loads(response.raw.content)
        if response.raw and response.raw.content
        else {}
    )
    raise LarkError(
        method="method_name",
        code=response.code,
        msg=response.msg,
        log_id=response.get_log_id(),
        resp=resp_data,
    )

# 2. 响应数据为空
if response.data is None:
    raise LarkError(method="method_name", detail="response.data is null")

if response.data.xxx is None:
    raise LarkError(method="method_name", detail="response.data.xxx is null")

# 3. 原始 HTTP 请求失败（SDK 不支持的接口）
if resp_json.get("code") != 0:
    raise LarkError(method="method_name", resp=resp_json)
```

禁止：

- `lark.logger.error(...)`
- `return {}` / `return []`
- 将所有字段拼接成一个字符串传给 `LarkError`

## 成功日志规范

```python
# 方法名 + model_dump_json(indent=2)
print(f"✅ method_name success", result.model_dump_json(indent=2))
```

## 使用原始 HTTP 请求的方法（如 root_folder）

当 lark_oapi SDK 不支持某接口时，使用 `requests` 直接调用：

```python
response = requests.get(url, headers=headers)
response.raise_for_status()
resp_json = response.json()

if resp_json.get("code") != 0:
    raise LarkError(method="method_name", resp=resp_json)
```
