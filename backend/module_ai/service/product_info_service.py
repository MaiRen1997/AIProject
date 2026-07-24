from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.product_info_dao import Product_infoDao
from module_ai.entity.vo.product_info_vo import DeleteProduct_infoModel, Product_infoModel, Product_infoPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil


class Product_infoService:
    """
    产品组件关联模块服务层
    """

    @classmethod
    async def get_product_info_list_services(
        cls, query_db: AsyncSession, query_object: Product_infoPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取产品组件关联列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品组件关联列表信息对象
        """
        product_info_list_result = await Product_infoDao.get_product_info_list(query_db, query_object, is_page)

        return product_info_list_result


    @classmethod
    async def add_product_info_services(cls, query_db: AsyncSession, page_object: Product_infoModel) -> CrudResponseModel:
        """
        新增产品组件关联信息service

        :param query_db: orm对象
        :param page_object: 新增产品组件关联对象
        :return: 新增产品组件关联校验结果
        """
        try:
            await Product_infoDao.add_product_info_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_product_info_services(cls, query_db: AsyncSession, page_object: Product_infoModel) -> CrudResponseModel:
        """
        编辑产品组件关联信息service

        :param query_db: orm对象
        :param page_object: 编辑产品组件关联对象
        :return: 编辑产品组件关联校验结果
        """
        edit_product_info = page_object.model_dump(exclude_unset=True, exclude={})
        product_info_info = await cls.product_info_detail_services(query_db, page_object.id)
        if product_info_info.id:
            try:
                await Product_infoDao.edit_product_info_dao(query_db, edit_product_info)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='产品组件关联不存在')

    @classmethod
    async def delete_product_info_services(cls, query_db: AsyncSession, page_object: DeleteProduct_infoModel) -> CrudResponseModel:
        """
        删除产品组件关联信息service

        :param query_db: orm对象
        :param page_object: 删除产品组件关联对象
        :return: 删除产品组件关联校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await Product_infoDao.delete_product_info_dao(query_db, Product_infoModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入id唯一标识为空')

    @classmethod
    async def product_info_detail_services(cls, query_db: AsyncSession, id: int) -> Product_infoModel:
        """
        获取产品组件关联详细信息service

        :param query_db: orm对象
        :param id: id唯一标识
        :return: id唯一标识对应的信息
        """
        product_info = await Product_infoDao.get_product_info_detail_by_id(query_db, id=id)
        result = Product_infoModel(**CamelCaseUtil.transform_result(product_info)) if product_info else Product_infoModel()

        return result

    @staticmethod
    async def export_product_info_list_services(product_info_list: list) -> bytes:
        """
        导出产品组件关联信息service

        :param product_info_list: 产品组件关联信息列表
        :return: 产品组件关联信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'id': 'id唯一标识',
            'productName': '产品名称',
            'productNo': '产品号',
            'equipmentId': '组成组件号',
            'relationEqpId': '强关联组件号(只能是这个配件)',
        }
        binary_data = ExcelUtil.export_list2excel(product_info_list, mapping_dict)

        return binary_data
