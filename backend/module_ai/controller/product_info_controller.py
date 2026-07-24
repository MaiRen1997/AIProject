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
from module_ai.service.product_info_service import Product_infoService
from module_ai.entity.vo.product_info_vo import DeleteProduct_infoModel, Product_infoModel, Product_infoPageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.response_util import ResponseUtil


product_info_controller = APIRouterPro(
    prefix='/product_info', order_num=50, tags=['产品组件关联'], dependencies=[PreAuthDependency()]
)


@product_info_controller.get(
    '/list',
    summary='获取产品组件关联分页列表接口',
    description='用于获取产品组件关联分页列表',
    response_model=PageResponseModel[Product_infoModel],
    dependencies=[UserInterfaceAuthDependency('product_info:product_info:list')],
)
async def get_product_info_product_info_list(
    request: Request,
product_info_page_query: Annotated[Product_infoPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    product_info_page_query_result = await Product_infoService.get_product_info_list_services(query_db, product_info_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=product_info_page_query_result)


@product_info_controller.post(
    '',
    summary='新增产品组件关联接口',
    description='用于新增产品组件关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('product_info:product_info:add')],
)
@ValidateFields(validate_model='add_product_info')
@Log(title='产品组件关联', business_type=BusinessType.INSERT)
async def add_product_info_product_info(
    request: Request,
    add_product_info: Product_infoModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_product_info_result = await Product_infoService.add_product_info_services(query_db, add_product_info)
    logger.info(add_product_info_result.message)

    return ResponseUtil.success(msg=add_product_info_result.message)


@product_info_controller.put(
    '',
    summary='编辑产品组件关联接口',
    description='用于编辑产品组件关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('product_info:product_info:edit')],
)
@ValidateFields(validate_model='edit_product_info')
@Log(title='产品组件关联', business_type=BusinessType.UPDATE)
async def edit_product_info_product_info(
    request: Request,
    edit_product_info: Product_infoModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_product_info_result = await Product_infoService.edit_product_info_services(query_db, edit_product_info)
    logger.info(edit_product_info_result.message)

    return ResponseUtil.success(msg=edit_product_info_result.message)


@product_info_controller.delete(
    '/{ids}',
    summary='删除产品组件关联接口',
    description='用于删除产品组件关联',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('product_info:product_info:remove')],
)
@Log(title='产品组件关联', business_type=BusinessType.DELETE)
async def delete_product_info_product_info(
    request: Request,
    ids: Annotated[str, Path(description='需要删除的id唯一标识')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_product_info = DeleteProduct_infoModel(ids=ids)
    delete_product_info_result = await Product_infoService.delete_product_info_services(query_db, delete_product_info)
    logger.info(delete_product_info_result.message)

    return ResponseUtil.success(msg=delete_product_info_result.message)


@product_info_controller.get(
    '/{id}',
    summary='获取产品组件关联详情接口',
    description='用于获取指定产品组件关联的详细信息',
    response_model=DataResponseModel[Product_infoModel],
    dependencies=[UserInterfaceAuthDependency('product_info:product_info:query')]
)
async def query_detail_product_info_product_info(
    request: Request,
    id: Annotated[int, Path(description='id唯一标识')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    product_info_detail_result = await Product_infoService.product_info_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=product_info_detail_result)


@product_info_controller.post(
    '/export',
    summary='导出产品组件关联列表接口',
    description='用于导出当前符合查询条件的产品组件关联列表数据',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回产品组件关联列表excel文件',
            'content': {
                'application/octet-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('product_info:product_info:export')],
)
@Log(title='产品组件关联', business_type=BusinessType.EXPORT)
async def export_product_info_product_info_list(
    request: Request,
    product_info_page_query: Annotated[Product_infoPageQueryModel, Form()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取全量数据
    product_info_query_result = await Product_infoService.get_product_info_list_services(query_db, product_info_page_query, is_page=False)
    product_info_export_result = await Product_infoService.export_product_info_list_services(product_info_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(product_info_export_result))
