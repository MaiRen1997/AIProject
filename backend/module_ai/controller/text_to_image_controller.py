from typing import Annotated

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_ai.entity.vo.text_to_image_vo import TextToImageRequestModel, TextToImageResultModel
from module_ai.service.text_to_image_service import TextToImageService
from utils.log_util import logger
from utils.response_util import ResponseUtil

text_to_image_controller = APIRouterPro(
    prefix='/ai/generate-img', order_num=25, tags=['AI管理-文生图'], dependencies=[PreAuthDependency()]
)


@text_to_image_controller.post(
    '/text-to-image',
    summary='文字描述生成图片',
    description='调用支持图片生成的多模态模型，根据提示词返回一张图片',
    response_model=DataResponseModel[TextToImageResultModel],
)
async def generate_text_to_image(
    request: Request,
    body: TextToImageRequestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await TextToImageService.generate_image_services(query_db, body)
    logger.info(f'文生图成功，model_id={body.model_id}')
    return ResponseUtil.success(data=result)
