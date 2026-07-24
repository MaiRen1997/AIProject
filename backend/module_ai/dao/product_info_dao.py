from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.product_info_do import ProductModelInfo
from module_ai.entity.vo.product_info_vo import Product_infoModel, Product_infoPageQueryModel
from utils.page_util import PageUtil


class Product_infoDao:
    """
    产品组件关联模块数据库操作层
    """

    @classmethod
    async def get_product_info_detail_by_id(cls, db: AsyncSession, id: int) -> ProductModelInfo | None:
        """
        根据id唯一标识获取产品组件关联详细信息

        :param db: orm对象
        :param id: id唯一标识
        :return: 产品组件关联信息对象
        """
        product_info_info = (
            (
                await db.execute(
                    select(ProductModelInfo)
                    .where(
                        ProductModelInfo.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return product_info_info

    @classmethod
    async def get_product_info_detail_by_info(cls, db: AsyncSession, product_info: Product_infoModel) -> ProductModelInfo | None:
        """
        根据产品组件关联参数获取产品组件关联信息

        :param db: orm对象
        :param product_info: 产品组件关联参数对象
        :return: 产品组件关联信息对象
        """
        product_info_info = (
            (
                await db.execute(
                    select(ProductModelInfo).where(
                    )
                )
            )
            .scalars()
            .first()
        )

        return product_info_info

    @classmethod
    async def get_product_info_list(
        cls, db: AsyncSession, query_object: Product_infoPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取产品组件关联列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品组件关联列表信息对象
        """
        query = (
            select(ProductModelInfo)
            .where(
                ProductModelInfo.product_name.like(f'%{query_object.product_name}%') if query_object.product_name else True,
                ProductModelInfo.product_no == query_object.product_no if query_object.product_no else True,
                ProductModelInfo.equipment_id == query_object.equipment_id if query_object.equipment_id else True,
                ProductModelInfo.relation_eqp_id == query_object.relation_eqp_id if query_object.relation_eqp_id else True,
            )
            .order_by(ProductModelInfo.id)
            .distinct()
        )
        product_info_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return product_info_list

    @classmethod
    async def add_product_info_dao(cls, db: AsyncSession, product_info: Product_infoModel) -> ProductModelInfo:
        """
        新增产品组件关联数据库操作

        :param db: orm对象
        :param product_info: 产品组件关联对象
        :return:
        """
        db_product_info = ProductModelInfo(**product_info.model_dump(exclude={}))
        db.add(db_product_info)
        await db.flush()

        return db_product_info

    @classmethod
    async def edit_product_info_dao(cls, db: AsyncSession, product_info: dict) -> None:
        """
        编辑产品组件关联数据库操作

        :param db: orm对象
        :param product_info: 需要更新的产品组件关联字典
        :return:
        """
        await db.execute(update(ProductModelInfo), [product_info])

    @classmethod
    async def delete_product_info_dao(cls, db: AsyncSession, product_info: Product_infoModel) -> None:
        """
        删除产品组件关联数据库操作

        :param db: orm对象
        :param product_info: 产品组件关联对象
        :return:
        """
        await db.execute(delete(ProductModelInfo).where(ProductModelInfo.id.in_([product_info.id])))

