import json
from pathlib import Path
from typing import List, Optional, Union
from lark_oapi.api.docx.v1 import *
from .wrapper_entity import (
    ListBlocksResult,
    BlockUnion,
    TextBlockItem,
    Heading1BlockItem,
    Heading2BlockItem,
    Heading3BlockItem,
    Heading4BlockItem,
    Heading5BlockItem,
    Heading6BlockItem,
    Heading7BlockItem,
    Heading8BlockItem,
    Heading9BlockItem,
    ImageBlockItem,
)
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError


# Block 类型常量
BLOCK_TYPE_TEXT = 2
BLOCK_TYPE_HEADING = [3, 4, 5, 6, 7, 8, 9, 10, 11]  # 标题1-9
BLOCK_TYPE_IMAGE = 27

# 标题类映射
HEADING_CLASSES = {
    3: Heading1BlockItem,
    4: Heading2BlockItem,
    5: Heading3BlockItem,
    6: Heading4BlockItem,
    7: Heading5BlockItem,
    8: Heading6BlockItem,
    9: Heading7BlockItem,
    10: Heading8BlockItem,
    11: Heading9BlockItem,
}


class DocBlockWrapper(BaseWrapper):
    """飞书云文档 > 文档 > 块 API 封装类"""

    def _get_heading_attr(self, block_type: int) -> str:
        """获取标题属性名"""
        return f"heading{block_type - 2}"

    def _extract_text_elements(self, elements_obj) -> List[str]:
        """提取文本元素为字符串列表"""
        if not elements_obj:
            return []
        return [
            elem.text_run.content
            for elem in elements_obj
            if elem.text_run and elem.text_run.content
        ]

    def _create_text_block(self, block) -> TextBlockItem:
        """创建文本块"""
        elements = self._extract_text_elements(block.text.elements)
        return TextBlockItem(
            block_id=block.block_id,
            parent_id=block.parent_id,
            elements=elements,
        )

    def _create_heading_block(self, block, block_type: int) -> Union[
        Heading1BlockItem,
        Heading2BlockItem,
        Heading3BlockItem,
        Heading4BlockItem,
        Heading5BlockItem,
        Heading6BlockItem,
        Heading7BlockItem,
        Heading8BlockItem,
        Heading9BlockItem,
    ]:
        """创建标题块"""
        heading_attr = self._get_heading_attr(block_type)
        heading_obj = getattr(block, heading_attr, None)
        elements = self._extract_text_elements(
            heading_obj.elements if heading_obj else None
        )

        heading_class = HEADING_CLASSES[block_type]
        return heading_class(
            block_id=block.block_id,
            parent_id=block.parent_id,
            elements=elements,
        )

    def _create_image_block(self, block) -> ImageBlockItem:
        """创建图片块"""
        caption = None
        if block.image.caption and block.image.caption.content:
            caption = block.image.caption.content
        return ImageBlockItem(
            block_id=block.block_id,
            parent_id=block.parent_id,
            width=block.image.width,
            height=block.image.height,
            token=block.image.token,
            caption=caption,
        )

    def list_blocks(
        self,
        document_id: str,
        save_path: Optional[str] = None,
        document_revision_id: Optional[int] = None,
        user_id_type: Optional[str] = None,
    ) -> ListBlocksResult:
        """
        获取文档所有块（自动分页）并保存到文件
        https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list
        """
        all_items: List[BlockUnion] = []
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
            for block in response.data.items or []:
                block_type = block.block_type

                if block_type == BLOCK_TYPE_TEXT:
                    all_items.append(self._create_text_block(block))

                elif block_type in BLOCK_TYPE_HEADING:
                    all_items.append(self._create_heading_block(block, block_type))

                elif block_type == BLOCK_TYPE_IMAGE:
                    all_items.append(self._create_image_block(block))

            print(
                f"📄 Page {page_count}: {len(response.data.items or [])} blocks, total: {len(all_items)}"
            )

            # 通过 has_more 和 page_token 判断是否有更多分页
            if not response.data.has_more:
                break
            page_token = response.data.page_token
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
