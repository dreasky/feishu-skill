import json
import requests
from pathlib import Path
from lark_oapi.api.drive.v1 import *
from .wrapper_entity import *
from .base_wrapper import BaseWrapper
from .wrapper_error import WrapperError
from typing import List


MAX_FILE_SIZE = 20 * 1024 * 1024


class CloudSpaceWrapper(BaseWrapper):
    """飞书云文档 API 封装类"""

    def root_folder(self) -> RootFolderResult:
        """
        获取我的空间（根文件夹）元数据
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/get-root-folder-meta
        """
        url = self.base_url + "/drive/explorer/v2/root_folder/meta"
        headers = {"Authorization": f"Bearer {self._tenant_access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        resp_json = response.json()

        # 处理失败返回
        if resp_json.get("code") != 0:
            raise WrapperError(method="root_folder", resp=resp_json)

        # 处理业务结果
        data = resp_json.get("data", {})

        result = RootFolderResult(
            token=data.get("token"),
            id=data.get("id"),
            user_id=data.get("user_id"),
        )
        print(f"✅ root_folder success", result.model_dump_json(indent=2))
        return result

    def list_file(self, folder_token: str = "") -> ListFileResult:
        """
        获取文件夹中的文件清单
        https://open.feishu.cn/document/server-docs/docs/drive-v1/folder/list
        """
        request: ListFileRequest = (
            ListFileRequest.builder().folder_token(folder_token).build()
        )
        response: ListFileResponse = self._client.drive.v1.file.list(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="list_file",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="method_name", detail="response.data is null")

        # 处理业务结果
        files = [
            FileItem(token=f.token, name=f.name, type=f.type)
            for f in (response.data.files or [])
            if f.token is not None and f.name is not None and f.type is not None
        ]
        result = ListFileResult(files=files)
        print(f"✅ list_file success", result.model_dump_json(indent=2))
        return result

    def upload_all_media(
        self,
        file_path: Path,
        file_name: str,
        extra: str,
    ) -> UploadMediaResult:
        """
        上传素材
        https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all
        """
        file_size = file_path.stat().st_size

        if file_size > MAX_FILE_SIZE:
            raise WrapperError(
                method="upload_all_media",
                msg=f"File size {file_size} exceeds limit {MAX_FILE_SIZE}",
                detail=f"文件过大: '{file_name}' ({file_size} bytes), 当前限制为 {MAX_FILE_SIZE / 1024 / 1024:.1f}MB, 超过限制的文件请使用分片上传接口",
            )

        with file_path.open("rb") as file:
            request_body = (
                UploadAllMediaRequestBody.builder()
                .file_name(file_name)
                .parent_type("ccm_import_open")
                .size(file_size)
                .extra(extra)
                .file(file)
                .build()
            )
            request: UploadAllMediaRequest = (
                UploadAllMediaRequest.builder().request_body(request_body).build()
            )
            response: UploadAllMediaResponse = self._client.drive.v1.media.upload_all(
                request
            )

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="upload_all_media",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="upload_all_media", detail="response.data is null"
            )

        if response.data.file_token is None:
            raise WrapperError(
                method="upload_all_media", detail="response.data.file_token is null"
            )

        # 处理业务结果
        result = UploadMediaResult(
            file_token=response.data.file_token, file_name=file_name
        )
        print(f"✅ upload_all_media success", result.model_dump_json(indent=2))
        return result

    def create_import_task(
        self,
        mount_key: str,
        file_extension: str,
        file_token: str,
        type: str,
        file_name: str,
    ) -> ImportTaskTicket:
        """
        创建导入任务
        https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/create
        """
        point = (
            ImportTaskMountPoint.builder().mount_type(1).mount_key(mount_key).build()
        )

        import_task = (
            ImportTask.builder()
            .file_extension(file_extension)
            .file_token(file_token)
            .type(type)
            .file_name(file_name)
            .point(point)
            .build()
        )

        request: CreateImportTaskRequest = (
            CreateImportTaskRequest.builder().request_body(import_task).build()
        )
        response: CreateImportTaskResponse = self._client.drive.v1.import_task.create(
            request
        )

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="create_import_task",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(
                method="create_import_task", detail="response.data is null"
            )

        if response.data.ticket is None:
            raise WrapperError(
                method="create_import_task", detail="response.data.ticket is null"
            )

        # 处理业务结果
        result = ImportTaskTicket(ticket=response.data.ticket)
        print(f"✅ create_import_task success", result.model_dump_json(indent=2))
        return result

    def get_import_task(self, ticket: str) -> ImportTaskResult:
        """
        查询导入任务结果
        https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/get
        """
        request: GetImportTaskRequest = (
            GetImportTaskRequest.builder().ticket(ticket).build()
        )
        response: GetImportTaskResponse = self._client.drive.v1.import_task.get(request)

        # 处理失败返回
        if not response.success():
            resp_data = (
                json.loads(response.raw.content)
                if response.raw and response.raw.content
                else {}
            )
            raise WrapperError(
                method="get_import_task",
                code=response.code,
                msg=response.msg,
                log_id=response.get_log_id(),
                resp=resp_data,
            )

        if response.data is None:
            raise WrapperError(method="get_import_task", detail="response.data is null")

        if response.data.result is None:
            raise WrapperError(
                method="get_import_task", detail="response.data.result is null"
            )

        if response.data.result.token is None:
            raise WrapperError(
                method="get_import_task", detail="response.data.result.token is null"
            )

        if response.data.result.type is None:
            raise WrapperError(
                method="get_import_task", detail="response.data.result.type is null"
            )

        if response.data.result.url is None:
            raise WrapperError(
                method="get_import_task", detail="response.data.result.url is null"
            )

        # 处理业务结果
        job_status_map = {0: "导入成功", 1: "初始化", 2: "处理中", 3: "内部错误"}
        if response.data.result.job_status is not None:
            status_text = job_status_map.get(
                response.data.result.job_status,
                f"job_status={response.data.result.job_status}, 查阅https://open.feishu.cn/document/server-docs/docs/drive-v1/import_task/get",
            )
        else:
            status_text = "未知状态"

        result = ImportTaskResult(
            status_text=status_text,
            token=response.data.result.token,
            type=response.data.result.type,
            url=response.data.result.url,
        )
        print(f"✅ get_import_task success", result.model_dump_json(indent=2))
        return result

    def list_comments(
        self,
        file_token: str,
        file_type: str,
        save_path: Optional[str] = None,
        is_whole: Optional[bool] = None,
        is_solved: Optional[bool] = None,
        user_id_type: Optional[str] = None,
    ) -> ListCommentsResult:
        """
        获取云文档所有评论并保存到文件
        https://open.feishu.cn/document/server-docs/docs/CommentAPI/list
        """
        all_items: List[FileCommentWrapper] = []
        page_token = None
        page_count = 0

        while True:
            page_count += 1

            builder = (
                ListFileCommentRequest.builder()
                .file_token(file_token)
                .file_type(file_type)
                .page_size(50)
            )

            if is_whole is not None:
                builder = builder.is_whole(is_whole)
            if is_solved is not None:
                builder = builder.is_solved(is_solved)
            if page_token:
                builder = builder.page_token(page_token)
            if user_id_type:
                builder = builder.user_id_type(user_id_type)

            request: ListFileCommentRequest = builder.build()
            response: ListFileCommentResponse = self._client.drive.v1.file_comment.list(
                request
            )

            if not response.success():
                resp_data = (
                    json.loads(response.raw.content)
                    if response.raw and response.raw.content
                    else {}
                )
                raise WrapperError(
                    method="list_comments",
                    code=response.code,
                    msg=response.msg,
                    log_id=response.get_log_id(),
                    resp=resp_data,
                )

            if response.data is None:
                raise WrapperError(
                    method="list_comments", detail="response.data is null"
                )

            if response.data.items is None:
                raise WrapperError(
                    method="list_comments", detail="response.data.items is null"
                )

            comments = response.data.items or []
            all_items = [
                (c if isinstance(c, FileCommentWrapper) else FileCommentWrapper(c))
                for c in comments
            ]

            print(
                f"📄 Page {page_count}: {len(response.data.items or [])} comments, total: {len(all_items)}"
            )

            # 通过 has_more 和 page_token 判断是否有更多分页
            if not response.data.has_more:
                break
            page_token = response.data.page_token
            if not page_token:
                break

        result = ListCommentsResult(
            file_token=file_token,
            total_comments=len(all_items),
            items=all_items,
        )
        # 保存到文件
        if save_path:
            save_file = Path(save_path)
            save_file.parent.mkdir(parents=True, exist_ok=True)
            save_file.write_text(result.to_json(indent=2), encoding="utf-8")
            print(f"✅ list_comments saved to: {save_path}")

        print(f"✅ list_comments success, total: {len(all_items)} comments")
        return result
