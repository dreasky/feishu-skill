# 飞书 API Wrapper 开发规范

## 文件结构

```txt
feishu/scripts/
├── run.py                        # 入口：管理 venv、安装依赖、执行脚本
├── lark_cli.py                   # CLI 命令定义
├── base/
│   └── lark_auth.py              # 鉴权（不修改）
└── wrapper/
    ├── __init__.py               # 导出所有 Wrapper 类
    ├── base_wrapper.py           # BaseWrapper 基类（不添加业务方法）
    ├── wrapper_entity.py         # 所有 Result / Item 实体类
    ├── wrapper_error.py          # WrapperError 异常类
    ├── message_manage_wrapper.py
    ├── group_manage_wrapper.py
    ├── cloud_space_wrapper.py
    ├── cloud_auth_wrapper.py
    └── {module}_wrapper.py       # 新增模块按此命名
```

---

## Wrapper 文件

每个 `*_wrapper.py` 继承 `BaseWrapper`，只包含对应飞书 API 模块的方法。

```python
# wrapper/{module}_wrapper.py
from lark_oapi.api.{service}.{version} import XxxRequest, XxxResponse  # 按需导入，不用 *
from .base_wrapper import BaseWrapper
from .wrapper_entity import XxxResult
from .wrapper_error import WrapperError

class XxxWrapper(BaseWrapper):
    def do_something(self, param: str) -> XxxResult:
        """方法说明\nhttps://open.feishu.cn/document/..."""
        request = XxxRequest.builder().param(param).build()
        response: XxxResponse = self._client.xxx.v1.yyy.zzz(request)

        if not response.success():
            raise WrapperError(
                method="do_something",
                code=response.code, msg=response.msg,
                log_id=response.get_log_id(),
                resp=json.loads(response.raw.content) if response.raw and response.raw.content else {},
            )

        result = XxxResult(field=response.data.field)
        print(f"✅ do_something success", result.model_dump_json(indent=2))
        return result
```

---

## 实体类（wrapper_entity.py）

所有 Result / Item 类统一放在 `wrapper/wrapper_entity.py`，使用 Pydantic `BaseModel`。

命名规则：`{动作}{对象}{类型}`

| 类型     | 示例                                          |
| -------- | --------------------------------------------- |
| 列表子项 | `ListChatItem`, `FileItem`                    |
| 返回值   | `SendMessageResult`, `UploadMediaResult`      |
| 中间数据 | `ImportTaskTicket`                            |

```python
class XxxItem(BaseModel):
    id: str
    name: str

class XxxResult(BaseModel):
    items: List[XxxItem]
    token: Optional[str] = None
```

---

## 错误处理

`WrapperError` 字段：

```python
method: str           # 方法名
code: Optional[int]   # 飞书错误码
msg: Optional[str]    # 飞书错误描述
log_id: Optional[str] # 请求 log_id
resp: Optional[dict]  # 原始响应体
detail: Optional[str] # 补充说明
```

三种场景：

```python
# SDK 响应失败
if not response.success():
    raise WrapperError(method="x", code=response.code, msg=response.msg,
                       log_id=response.get_log_id(), resp=json.loads(response.raw.content))

# 响应数据为空
if response.data is None:
    raise WrapperError(method="x", detail="response.data is null")

# 原始 HTTP 请求失败
if resp_json.get("code") != 0:
    raise WrapperError(method="x", resp=resp_json)
```

禁止：`lark.logger.error(...)` / `return {}` / `return []` / 将字段拼成字符串传入

---

## 成功日志

```python
print(f"✅ method_name success", result.model_dump_json(indent=2))
```

---

## 原始 HTTP 请求（SDK 不支持时）

```python
response = requests.get(url, headers=headers)
response.raise_for_status()
resp_json = response.json()
if resp_json.get("code") != 0:
    raise WrapperError(method="method_name", resp=resp_json)
```

---

## 新增命令到 SKILL.md

新增命令后必须同步更新 `feishu/SKILL.md`。

### 结构层级

```markdown
## 命令参考
### 速查索引          ← 所有命令汇总表
---
### {类别}            ← H3
#### `{命令}` — {说明}  ← H4 命令卡片
```

### 速查索引格式

```markdown
| 类别   | 命令          | 说明         |
| ------ | ------------- | ------------ |
| 消息   | `send-text`   | 发送文本消息 |
```

新增命令在对应类别末尾追加一行，不改变类别顺序。

### 命令卡片格式

```markdown
#### `{命令名}` — {一句话说明}

| 参数    | 必填 | 说明 |
| ------- | ---- | ---- |
| `--foo` | 是   | ...  |
| `--bar` | 否   | ...  |

{补充说明（可选）}

​```bash
python scripts/run.py lark_cli.py {命令名} --foo "<value>"
​```
```

规则：

- 无参数命令省略表格，直接写"无参数。"
- 示例只保留典型用法，多场景用注释区分
- 卡片之间用 `---` 分隔

### 示例

```markdown
#### `upload-file` — 上传任意文件

| 参数          | 必填 | 说明                    |
| ------------- | ---- | ----------------------- |
| `--file-path` | 是   | 本地文件路径            |
| `--obj-type`  | 否   | 文档类型（默认 `docx`） |

返回 ticket，用于后续查询导入任务。

​```bash
python scripts/run.py lark_cli.py upload-file --file-path "/path/to/file"
​```
```
