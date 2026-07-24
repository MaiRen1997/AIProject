from typing import Annotated

from fastapi import Body, Form, Path, Query, Request, Response
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
from module_ai.service.product_equipment_service import Product_equipmentService
from module_ai.entity.vo.product_equipment_vo import DeleteProduct_equipmentModel, Product_equipmentModel, Product_equipmentPageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.response_util import ResponseUtil


product_equipment_controller = APIRouterPro(
    prefix='/product_equipment', order_num=50, tags=['产品组件'], dependencies=[PreAuthDependency()]
)


@product_equipment_controller.get(
    '/list',
    summary='获取产品组件分页列表接口',
    description='用于获取产品组件分页列表',
    response_model=PageResponseModel[Product_equipmentModel],
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:list')],
)
async def get_product_equipment_product_equipment_list(
    request: Request,
product_equipment_page_query: Annotated[Product_equipmentPageQueryModel, Query()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取分页数据
    product_equipment_page_query_result = await Product_equipmentService.get_product_equipment_list_services(query_db, product_equipment_page_query, is_page=True)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=product_equipment_page_query_result)


@product_equipment_controller.post(
    '',
    summary='新增产品组件接口',
    description='用于新增产品组件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:add')],
)
@ValidateFields(validate_model='add_product_equipment')
@Log(title='产品组件', business_type=BusinessType.INSERT)
async def add_product_equipment_product_equipment(
    request: Request,
    add_product_equipment: Product_equipmentModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    add_product_equipment_result = await Product_equipmentService.add_product_equipment_services(query_db, add_product_equipment)
    logger.info(add_product_equipment_result.message)

    return ResponseUtil.success(msg=add_product_equipment_result.message)


@product_equipment_controller.put(
    '',
    summary='编辑产品组件接口',
    description='用于编辑产品组件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:edit')],
)
@ValidateFields(validate_model='edit_product_equipment')
@Log(title='产品组件', business_type=BusinessType.UPDATE)
async def edit_product_equipment_product_equipment(
    request: Request,
    edit_product_equipment: Product_equipmentModel,
    query_db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    edit_product_equipment_result = await Product_equipmentService.edit_product_equipment_services(query_db, edit_product_equipment)
    logger.info(edit_product_equipment_result.message)

    return ResponseUtil.success(msg=edit_product_equipment_result.message)


@product_equipment_controller.delete(
    '/{ids}',
    summary='删除产品组件接口',
    description='用于删除产品组件',
    response_model=ResponseBaseModel,
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:remove')],
)
@Log(title='产品组件', business_type=BusinessType.DELETE)
async def delete_product_equipment_product_equipment(
    request: Request,
    ids: Annotated[str, Path(description='需要删除的id唯一标识')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    delete_product_equipment = DeleteProduct_equipmentModel(ids=ids)
    delete_product_equipment_result = await Product_equipmentService.delete_product_equipment_services(query_db, delete_product_equipment)
    logger.info(delete_product_equipment_result.message)

    return ResponseUtil.success(msg=delete_product_equipment_result.message)


@product_equipment_controller.get(
    '/{id}',
    summary='获取产品组件详情接口',
    description='用于获取指定产品组件的详细信息',
    response_model=DataResponseModel[Product_equipmentModel],
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:query')]
)
async def query_detail_product_equipment_product_equipment(
    request: Request,
    id: Annotated[int, Path(description='id唯一标识')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    product_equipment_detail_result = await Product_equipmentService.product_equipment_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=product_equipment_detail_result)


@product_equipment_controller.post(
    '/export',
    summary='导出产品组件列表接口',
    description='用于导出当前符合查询条件的产品组件列表数据',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回产品组件列表excel文件',
            'content': {
                'application/octet-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:export')],
)
@Log(title='产品组件', business_type=BusinessType.EXPORT)
async def export_product_equipment_product_equipment_list(
    request: Request,
    product_equipment_page_query: Annotated[Product_equipmentPageQueryModel, Form()],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    # 获取全量数据
    product_equipment_query_result = await Product_equipmentService.get_product_equipment_list_services(query_db, product_equipment_page_query, is_page=False)
    product_equipment_export_result = await Product_equipmentService.export_product_equipment_list_services(product_equipment_query_result)
    logger.info('导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(product_equipment_export_result))


@product_equipment_controller.post(
    '/givePriceChat/export',
    summary='givePriceChat导出报价单接口',
    description='根据输入文本提取产品名称和型号，自动关联配件并导出excel',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回报价excel文件',
            'content': {
                'application/octet-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:export')],
)
@Log(title='产品组件', business_type=BusinessType.EXPORT)
async def export_give_price_chat_excel(
    request: Request,
    user_input: Annotated[str, Form(alias='userInput')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    export_result = await Product_equipmentService.export_give_price_chat_services(query_db, user_input)
    logger.info('givePriceChat导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(export_result))


@product_equipment_controller.post(
    '/givePriceChat/query',
    summary='givePriceChat查询接口',
    description='根据用户输入提取产品名称型号并返回markdown表格',
    response_model=DataResponseModel,
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:list')],
)
async def query_give_price_chat(
    request: Request,
    user_input: Annotated[str, Body(embed=True, alias='userInput')],
    query_db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    result = await Product_equipmentService.query_give_price_chat_services(query_db, user_input)
    logger.info('givePriceChat查询成功')

    return ResponseUtil.success(data=result)


@product_equipment_controller.post(
    '/givePriceChat/markdown/export',
    summary='givePriceChat markdown导出接口',
    description='将markdown表格转换为excel并下载',
    response_class=StreamingResponse,
    responses={
        200: {
            'description': '流式返回报价excel文件',
            'content': {
                'application/octet-stream': {},
            },
        }
    },
    dependencies=[UserInterfaceAuthDependency('product_equipment:product_equipment:export')],
)
@Log(title='产品组件', business_type=BusinessType.EXPORT)
async def export_give_price_chat_markdown_excel(
    request: Request,
    markdown_content: Annotated[str, Form(alias='markdownContent')],
) -> Response:
    export_result = await Product_equipmentService.export_give_price_chat_markdown_services(markdown_content)
    logger.info('givePriceChat markdown导出成功')

    return ResponseUtil.streaming(data=bytes2file_response(export_result))
