from datetime import datetime
import uuid
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
from module_ai.service.chat_message_service import Chat_messageService
from module_ai.entity.vo.chat_message_vo import (
    AddChat_messageModel,
    EditChat_messageModel,
    DeleteChat_messageModel,
    Chat_messageModel,
    Chat_messagePageQueryModel,
)
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.response_util import ResponseUtil


chat_message_controller = APIRouterPro(
    prefix='/chat_message', order_num=50, tags=['聊天消息'], dependencies=[PreAuthDependency()]
)


@chat_message_controller.get(
    '/list',
    summary='获取聊天消息分页列表接口',
    description='用于获取聊天消息分页列表',
    response_model=PageResponseModel[Chat_messageModel],
    dependencies=[UserInterfaceAuthDependency('chat_message:chat_message:list')],
)
async def get_chat_message_chat_message_list(
    request: Request,
chat_message_page_query: Annotated[Chat_messagePageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    chat_message_page_query_result = await Chat_messageService.get_chat_message_list_services(query_db, chat_message_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=chat_message_page_query_result)


@chat_message_controller.post(
    '',
    summary='新增聊天消息接口',
    description='用于新增聊天消息',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('chat_message:chat_message:add')],
)
@ValidateFields(validate_model='add_chat_message')
@Log(title='聊天消息', business_type=BusinessType.INSERT)
async def add_chat_message_chat_message(
    request: Request,
    add_chat_message: AddChat_messageModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    current_time = datetime.now()
    add_chat_message.message_id = str(uuid.uuid4())
    add_chat_message.created_at = current_time
    add_chat_message.updated_at = current_time
    add_chat_message_result = await Chat_messageService.add_chat_message_services(query_db, add_chat_message)
    logger.info(add_chat_message_result.message)

    return ResponseUtil.success(msg=add_chat_message_result.message)


@chat_message_controller.put(
    '',
    summary='编辑聊天消息接口',
    description='用于编辑聊天消息',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('chat_message:chat_message:edit')],
)
@ValidateFields(validate_model='edit_chat_message')
@Log(title='聊天消息', business_type=BusinessType.UPDATE)
async def edit_chat_message_chat_message(
    request: Request,
    edit_chat_message: EditChat_messageModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_chat_message.updated_at = datetime.now()
    edit_chat_message_result = await Chat_messageService.edit_chat_message_services(query_db, edit_chat_message)
    logger.info(edit_chat_message_result.message)

    return ResponseUtil.success(msg=edit_chat_message_result.message)


@chat_message_controller.delete(
    '/{ids}',
    summary='删除聊天消息接口',
    description='用于删除聊天消息',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('chat_message:chat_message:remove')],
)
@Log(title='聊天消息', business_type=BusinessType.DELETE)
async def delete_chat_message_chat_message(
    request: Request,
    ids: Annotated[str, Path(description='需要删除的消息ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_chat_message = DeleteChat_messageModel(ids=ids)
    delete_chat_message_result = await Chat_messageService.delete_chat_message_services(query_db, delete_chat_message)
    logger.info(delete_chat_message_result.message)

    return ResponseUtil.success(msg=delete_chat_message_result.message)


@chat_message_controller.get(
    '/{id}',
    summary='获取聊天消息详情接口',
    description='用于获取指定聊天消息的详细信息',
    response_model=DataResponseModel[Chat_messageModel],
    dependencies=[UserInterfaceAuthDependency('chat_message:chat_message:query')]
)
async def query_detail_chat_message_chat_message(
    request: Request,
    id: Annotated[int, Path(description='消息ID')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    chat_message_detail_result = await Chat_messageService.chat_message_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=chat_message_detail_result)


@chat_message_controller.post(
    '/export',
    summary='导出聊天消息列表接口',
    description='用于导出当前符合查询条件的聊天消息列表数据',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回聊天消息列表excel文件',
            'content': {
                'application/octet-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('chat_message:chat_message:export')],
)
@Log(title='聊天消息', business_type=BusinessType.EXPORT)
async def export_chat_message_chat_message_list(
    request: Request,
    chat_message_page_query: Annotated[Chat_messagePageQueryModel, Form()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取全量数据
    chat_message_query_result = await Chat_messageService.get_chat_message_list_services(query_db, chat_message_page_query, is_page=False)
    chat_message_export_result = await Chat_messageService.export_chat_message_list_services(chat_message_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(chat_message_export_result))
