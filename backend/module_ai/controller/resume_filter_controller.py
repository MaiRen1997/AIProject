from typing import Annotated

from fastapi import File, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.pre_auth import PreAuthDependency
from common.router import APIRouterPro
from common.vo import DataResponseModel
from module_ai.entity.vo.resume_filter_vo import (
    InterviewInviteRequestModel,
    InterviewInviteResultModel,
    ResumeOcrResultModel,
    ResumeScoreRequestModel,
    ResumeScoreResultModel,
)
from module_ai.service.resume_filter_service import ResumeFilterService
from utils.log_util import logger
from utils.response_util import ResponseUtil

resume_filter_controller = APIRouterPro(
    prefix='/ai/resume-filter', order_num=26, tags=['AI管理-简历筛选'], dependencies=[PreAuthDependency()]
)


@resume_filter_controller.post(
    '/ocr',
    summary='上传简历并进行OCR识别',
    description='保存文件到backend/FileTemp/resumeFile后调用免费OCR接口识别文本',
    response_model=DataResponseModel[ResumeOcrResultModel],
)
async def upload_resume_and_ocr(
    request: Request,
    file: Annotated[UploadFile, File(...)],
) -> Response:
    result = await ResumeFilterService.upload_and_ocr_resume_services(file)
    logger.info(f'简历OCR完成: {result.saved_file_name}')
    return ResponseUtil.success(data=result)


@resume_filter_controller.post(
    '/score',
    summary='简历匹配评分',
    description='根据简历文本与招聘标准加权规则，调用大模型计算匹配分值',
    response_model=DataResponseModel[ResumeScoreResultModel],
)
async def score_resume_match(
    request: Request,
    body: ResumeScoreRequestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ResumeFilterService.score_resume_services(query_db, body)
    logger.info(f'简历评分完成，score={result.score}')
    return ResponseUtil.success(data=result)


@resume_filter_controller.post(
    '/invite',
    summary='发送面试邀约',
    description='校验候选人与岗位信息后，申请腾讯会议链接并生成邀约文案',
    response_model=DataResponseModel[InterviewInviteResultModel],
)
async def send_interview_invite(
    request: Request,
    body: InterviewInviteRequestModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await ResumeFilterService.send_interview_invite_services(query_db, body)
    logger.info(f'面试邀约生成成功，meeting_time={result.meeting_time}')
    return ResponseUtil.success(data=result)
