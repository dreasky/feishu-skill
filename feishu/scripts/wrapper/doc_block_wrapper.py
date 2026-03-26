import json
from pathlib import Path
from typing import List, Optional
from lark_oapi.api.docx.v1 import *
from .wrapper_entity import ListBlocksResult, BlockWrapper
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError

# 块过滤列表：文本 Block、标题 1-9 Block、图片 Block
BLOCK_FILTER_LIST = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 27]


class DocBlockWrapper(BaseWrapper):
    """飞书云文档 > 文档 > 块 API 封装类"""

    def list_blocks(
        self,
        document_id: str,
        save_path: Optional[str] = None,
        document_revision_id: Optional[int] = None,
        user_id_type: Optional[str] = None,
        is_filter: bool = False,
    ) -> ListBlocksResult:
        """
        获取文档所有块（自动分页）并保存到文件
        https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list
        """
        all_items: List[BlockWrapper] = []
        page_token = None
        page_count = 0

        while True:
            page_count += 1

            # 构建请求
            builder = (
                ListDocumentBlockRequest.builder()
                .document_id(document_id)
                .page_size(500)
            )
            if page_token:
                builder = builder.page_token(page_token)
            if document_revision_id is not None:
                builder = builder.document_revision_id(document_revision_id)
            if user_id_type:
                builder = builder.user_id_type(user_id_type)

            request: ListDocumentBlockRequest = builder.build()
            response: ListDocumentBlockResponse = (
                self._client.docx.v1.document_block.list(request)
            )

            if not response.success():
                resp_data = (
                    json.loads(response.raw.content)
                    if response.raw and response.raw.content
                    else {}
                )
                raise WrapperError(
                    method="list_blocks",
                    code=response.code,
                    msg=response.msg,
                    log_id=response.get_log_id(),
                    resp=resp_data,
                )

            if response.data is None:
                raise WrapperError(method="list_blocks", detail="response.data is null")

            # 解析块列表
            # SDK 的 ListDocumentBlockResponseBody 有 __getattr__ 会转发到 Block，导致直接访问 items 失败
            # 需要通过 __dict__ 直接访问
            data_dict = response.data.__dict__
            blocks = data_dict.get("items") or []
            has_more = data_dict.get("has_more") or False
            next_page_token = data_dict.get("page_token")
            if is_filter:
                page_items = [
                    BlockWrapper(b) for b in blocks if b.block_type in BLOCK_FILTER_LIST
                ]
            else:
                page_items = [BlockWrapper(b) for b in blocks]
            all_items.extend(page_items)

            print(
                f"📄 Page {page_count}: {len(blocks or [])} blocks, total: {len(all_items)}"
            )

            # 通过 has_more 和 page_token 判断是否有更多分页
            if not has_more:
                break
            page_token = next_page_token
            if not page_token:
                break

        result = ListBlocksResult(
            document_id=document_id,
            total_blocks=len(all_items),
            items=all_items,
        )

        # 保存到文件
        if save_path:
            save_file = Path(save_path)
            save_file.parent.mkdir(parents=True, exist_ok=True)
            save_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            print(f"✅ list_blocks saved to: {save_path}")

        print(f"✅ list_blocks success, total: {len(all_items)} blocks")
        return result
