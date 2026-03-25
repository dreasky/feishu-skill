import json
from pathlib import Path
from typing import Optional, List
from lark_oapi.api.docx.v1 import *
from .wrapper_entity import *
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


class DocBlockWrapper(BaseWrapper):
    """飞书云文档 > 文档 > 块 API 封装类"""

    def list_blocks(
        self,
        document_id: str,
        save_path: str,
        document_revision_id: Optional[int] = None,
        user_id_type: Optional[str] = None,
    ) -> ListBlocksResult:
        """
        获取文档所有块（自动分页）并保存到文件
        https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list
        """
        all_items: List[BlockItem] = []
        page_token = None
        page_count = 0

        while True:
            page_count += 1

            # 构建请求
            builder = ListDocumentBlockRequest.builder().document_id(document_id).page_size(500)
            if page_token:
                builder = builder.page_token(page_token)
            if document_revision_id is not None:
                builder = builder.document_revision_id(document_revision_id)
            if user_id_type:
                builder = builder.user_id_type(user_id_type)

            request: ListDocumentBlockRequest = builder.build()
            response: ListDocumentBlockResponse = self._client.docx.v1.document_block.list(request)

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
            for block in response.data.items or []:
                elements = []
                if block.text and block.text.elements:
                    for elem in block.text.elements:
                        text_run = None
                        if elem.text_run:
                            style = None
                            if elem.text_run.text_element_style:
                                style = TextElementStyle(
                                    bold=elem.text_run.text_element_style.bold,
                                    italic=elem.text_run.text_element_style.italic,
                                    strikethrough=elem.text_run.text_element_style.strikethrough,
                                    underline=elem.text_run.text_element_style.underline,
                                    inline_code=elem.text_run.text_element_style.inline_code,
                                )
                            text_run = TextRun(
                                content=elem.text_run.content,
                                text_element_style=style,
                            )
                        elements.append(BlockElement(text_run=text_run))

                text_style = None
                if block.text and block.text.style:
                    text_style = BlockTextStyle(
                        align=block.text.style.align,
                        done=block.text.style.done,
                        folded=block.text.style.folded,
                    )

                all_items.append(
                    BlockItem(
                        block_id=block.block_id,
                        parent_id=block.parent_id,
                        block_type=block.block_type,
                        children=list(block.children or []),
                        elements=elements,
                        text=text_style,
                    )
                )

            print(f"📄 Page {page_count}: {len(response.data.items or [])} blocks, total: {len(all_items)}")

            # 通过 page_token 判断是否有更多分页
            page_token = response.data.page_token
            if not page_token:
                break

        # 保存到文件
        result = ListBlocksResult(
            document_id=document_id,
            total_blocks=len(all_items),
            items=all_items,
        )

        save_file = Path(save_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)
        save_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        print(f"✅ list_blocks success, total: {len(all_items)} blocks, saved to: {save_path}")
        return result