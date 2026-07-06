from datetime import datetime
from typing import Annotated

from fastapi import Form, Path, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession

from common.annotation.log_annotation import Log
from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.enums import BusinessType
from common.router import APIRouterPro
from common.vo import DataResponseModel, PageResponseModel, ResponseBaseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_ai.service.sessions_service import SessionsService
from module_ai.entity.vo.sessions_vo import AddSessionsModel, DeleteSessionsModel, SessionsModel, SessionsPageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.response_util import ResponseUtil


sessions_controller = APIRouterPro(
    prefix='/sessions', order_num=50, tags=['用户会话关联'], dependencies=[PreAuthDependency()]
)


@sessions_controller.get(
    '/list',
    summary='获取用户会话关联分页列表接口',
    description='用于获取用户会话关联分页列表',
    response_model=PageResponseModel[SessionsModel],
    dependencies=[UserInterfaceAuthDependency(['sessions:sessions:list', 'ai:chat:list'])],
)
async def get_sessions_sessions_list(
    request: Request,
sessions_page_query: Annotated[SessionsPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    sessions_page_query_result = await SessionsService.get_sessions_list_services(query_db, sessions_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=sessions_page_query_result)


@sessions_controller.post(
    '',
    summary='新增用户会话关联接口',
    description='用于新增用户会话关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('sessions:sessions:add')],
)
@ValidateFields(validate_model='add_sessions')
@Log(title='用户会话关联', business_type=BusinessType.INSERT)
async def add_sessions_sessions(
    request: Request,
    add_sessions: AddSessionsModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_sessions.created_at = datetime.now()
    add_sessions_result = await SessionsService.add_sessions_services(query_db, add_sessions)
    logger.info(add_sessions_result.message)

    return ResponseUtil.success(msg=add_sessions_result.message)


@sessions_controller.put(
    '',
    summary='编辑用户会话关联接口',
    description='用于编辑用户会话关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('sessions:sessions:edit')],
)
@ValidateFields(validate_model='edit_sessions')
@Log(title='用户会话关联', business_type=BusinessType.UPDATE)
async def edit_sessions_sessions(
    request: Request,
    edit_sessions: SessionsModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_sessions_result = await SessionsService.edit_sessions_services(query_db, edit_sessions)
    logger.info(edit_sessions_result.message)

    return ResponseUtil.success(msg=edit_sessions_result.message)


@sessions_controller.delete(
    '/{ids}',
    summary='删除用户会话关联接口',
    description='用于删除用户会话关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('sessions:sessions:remove')],
)
@Log(title='用户会话关联', business_type=BusinessType.DELETE)
async def delete_sessions_sessions(
    request: Request,
    ids: Annotated[str, Path(description='需要删除的主键ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_sessions = DeleteSessionsModel(ids=ids)
    delete_sessions_result = await SessionsService.delete_sessions_services(query_db, delete_sessions)
    logger.info(delete_sessions_result.message)

    return ResponseUtil.success(msg=delete_sessions_result.message)


@sessions_controller.get(
    '/{id}',
    summary='获取用户会话关联详情接口',
    description='用于获取指定用户会话关联的详细信息',
    response_model=DataResponseModel[SessionsModel],
    dependencies=[UserInterfaceAuthDependency('sessions:sessions:query')]
)
async def query_detail_sessions_sessions(
    request: Request,
    id: Annotated[int, Path(description='主键ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    sessions_detail_result = await SessionsService.sessions_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=sessions_detail_result)


@sessions_controller.post(
    '/export',
    summary='导出用户会话关联列表接口',
    description='用于导出当前符合查询条件的用户会话关联列表数据',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回用户会话关联列表excel文件',
            'content': {
                'application/octet-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('sessions:sessions:export')],
)
@Log(title='用户会话关联', business_type=BusinessType.EXPORT)
async def export_sessions_sessions_list(
    request: Request,
    sessions_page_query: Annotated[SessionsPageQueryModel, Form()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取全量数据
    sessions_query_result = await SessionsService.get_sessions_list_services(query_db, sessions_page_query, is_page=False)
    sessions_export_result = await SessionsService.export_sessions_list_services(sessions_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(sessions_export_result))
