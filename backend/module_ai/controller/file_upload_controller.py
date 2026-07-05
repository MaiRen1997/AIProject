from typing import Annotated

from fastapi import File, Request, Response, UploadFile

from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DynamicResponseModel
from module_ai.entity.vo.file_upload_vo import AiUploadResponseModel
from module_ai.service.file_upload_service import FileUploadService
from utils.log_util import logger
from utils.response_util import ResponseUtil

file_upload_controller = APIRouterPro(
    prefix='/ai/file', order_num=23, tags=['AI管理-文件上传'], dependencies=[PreAuthDependency()]
)


@file_upload_controller.post(
    '/upload',
    summary='AI文件上传接口',
    description='上传文件并保存到backend/FilesTemp目录',
    response_model=DynamicResponseModel[AiUploadResponseModel],
)
async def upload_ai_file(request: Request, file: Annotated[UploadFile, File(...)]) -> Response:
    upload_result = await FileUploadService.upload_to_files_temp(file)
    logger.info(upload_result.message)

    return ResponseUtil.success(msg=upload_result.message, model_content=upload_result.result)
