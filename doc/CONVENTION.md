# 飞书 API Wrapper 开发规范

## 文件结构

```
feishu/scripts/
├── run.py                        # 入口
├── lark_cli.py                   # CLI 命令
├── base/lark_auth.py             # 鉴权（不修改）
└── wrapper/
    ├── __init__.py               # 导出
    ├── base_wrapper.py           # 基类（不添加业务方法）
    ├── wrapper_entity.py         # 实体类
    ├── wrapper_error.py          # 异常类
    └── {module}_wrapper.py       # API 封装
```

---

## 实体类（wrapper_entity.py）

### Wrapper 类（组合模式）

SDK 实体类有 `__getattr__` 冲突，用组合替代继承：

```python
class BlockWrapper:
    def __init__(self, block: Block):
        object.__setattr__(self, "_block", block)

    # 类型注解（不赋值！），仅 IDE 提示
    block_id: Optional[str]
    block_type: Optional[int]

    def __getattr__(self, name: str) -> Any:
        return getattr(self._block, name)

    def is_text_block(self) -> bool:  # 自定义扩展方法
        return self.block_type in BLOCK_TEXT_TYPES
```

### Result 类（Pydantic）

```python
class ListBlocksResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}  # 必须

    document_id: str
    items: List[BlockWrapper]

    @field_serializer("items")
    def serialize_items(self, items: List[BlockWrapper]) -> List[dict]:
        return _serialize_wrapper_items(items, "_block")
```

### 序列化工具

```python
def _serialize_value(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)): return v
    if isinstance(v, list): return [_serialize_value(i) for i in v]
    if hasattr(v, "__dict__"): return {k: _serialize_value(v2) for k, v2 in v.__dict__.items() if v2 is not None} or None
    return str(v)

def _serialize_wrapper_items(items: List[Any], inner_attr: str) -> List[dict]:
    return [{k: _serialize_value(v) for k, v in getattr(i, inner_attr).__dict__.items() if v is not None} for i in items if getattr(i, inner_attr)]

def _serialize_wrapper_item(item: Any, inner_attr: str) -> dict:
    inner = getattr(item, inner_attr)
    return {k: _serialize_value(v) for k, v in inner.__dict__.items() if v is not None} if inner else {}
```

### 命名规则

| 类型    | 格式            | 示例                        |
| ------- | --------------- | --------------------------- |
| Wrapper | `{Entity}Wrapper` | `BlockWrapper`              |
| Result  | `{Action}Result`  | `ListBlocksResult`          |
| 内部属性 | `_{entity}`       | `_block`, `_comment`        |

---

## Wrapper 文件

### 基本结构

```python
class XxxWrapper(BaseWrapper):
    def do_something(self, param: str) -> XxxResult:
        """方法说明\nhttps://open.feishu.cn/document/..."""
        request = XxxRequest.builder().param(param).build()
        response = self._client.xxx.v1.yyy.zzz(request)

        if not response.success():
            raise WrapperError(method="do_something", code=response.code, msg=response.msg,
                log_id=response.get_log_id(), resp=json.loads(response.raw.content or "{}"))

        print(f"✅ do_something success", result.model_dump_json(indent=2))
        return XxxResult(field=response.data.field)
```

### 分页处理

**关键**：SDK 响应通过 `__dict__` 访问，避免 `__getattr__` 问题

```python
all_items = []
page_token = None

while True:
    builder = Request.builder().page_size(500)
    if page_token: builder = builder.page_token(page_token)
    response = self._client.xxx.v1.yyy.list(builder.build())

    if not response.success(): raise WrapperError(...)

    data = response.data.__dict__  # 通过 __dict__ 访问
    items = data.get("items") or []
    all_items.extend([Wrapper(i) for i in items])  # 用 extend 累积

    print(f"📄 Page: {len(items)}, total: {len(all_items)}")

    if not data.get("has_more") or not data.get("page_token"): break
    page_token = data["page_token"]

if save_path: Path(save_path).write_text(result.model_dump_json(indent=2))
print(f"✅ success, total: {len(all_items)}")
return Result(items=all_items)
```

---

## 错误处理

```python
# SDK 失败
if not response.success():
    raise WrapperError(method="x", code=response.code, msg=response.msg,
        log_id=response.get_log_id(), resp=json.loads(response.raw.content or "{}"))

# 数据为空
if response.data is None:
    raise WrapperError(method="x", detail="response.data is null")

# 原始 HTTP 失败
if resp_json.get("code") != 0:
    raise WrapperError(method="x", resp=resp_json)
```

**禁止**：`lark.logger.error()` / `return {}` / `return []` / 字段拼字符串

---

## 关键规则

1. **不继承 SDK 类** → 用 Wrapper 组合
2. **类型注解不赋值** → 否则 `__getattr__` 不触发
3. **Result 必须配 `arbitrary_types_allowed`**
4. **响应通过 `__dict__` 访问**
5. **分页用 `extend` 累积**

---

## SKILL.md 命令格式

```markdown
#### `{命令}` — {说明}

| 参数    | 必填 | 说明 |
| ------- | ---- | ---- |
| `--foo` | 是   | ...  |

​```bash
python scripts/run.py lark_cli.py {命令} --foo "<value>"
​```
```

新增命令后同步更新 `feishu/SKILL.md`。