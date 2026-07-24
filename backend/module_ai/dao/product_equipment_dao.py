from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.product_equipment_do import ProductEquipmentInfo
from module_ai.entity.vo.product_equipment_vo import Product_equipmentModel, Product_equipmentPageQueryModel
from utils.page_util import PageUtil


class Product_equipmentDao:
    """
    产品组件模块数据库操作层
    """

    @classmethod
    async def get_product_equipment_detail_by_id(cls, db: AsyncSession, id: int) -> ProductEquipmentInfo | None:
        """
        根据id唯一标识获取产品组件详细信息

        :param db: orm对象
        :param id: id唯一标识
        :return: 产品组件信息对象
        """
        product_equipment_info = (
            (
                await db.execute(
                    select(ProductEquipmentInfo)
                    .where(
                        ProductEquipmentInfo.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return product_equipment_info

    @classmethod
    async def get_product_equipment_detail_by_info(cls, db: AsyncSession, product_equipment: Product_equipmentModel) -> ProductEquipmentInfo | None:
        """
        根据产品组件参数获取产品组件信息

        :param db: orm对象
        :param product_equipment: 产品组件参数对象
        :return: 产品组件信息对象
        """
        product_equipment_info = (
            (
                await db.execute(
                    select(ProductEquipmentInfo).where(
                    )
                )
            )
            .scalars()
            .first()
        )

        return product_equipment_info

    @classmethod
    async def get_product_equipment_list_by_ids(cls, db: AsyncSession, id_list: list[int]) -> list[ProductEquipmentInfo]:
        """
        根据id列表获取产品组件信息

        :param db: orm对象
        :param id_list: 产品组件id列表
        :return: 产品组件信息列表
        """
        if not id_list:
            return []

        product_equipment_list = (
            (
                await db.execute(
                    select(ProductEquipmentInfo)
                    .where(ProductEquipmentInfo.id.in_(id_list))
                    .order_by(ProductEquipmentInfo.id)
                )
            )
            .scalars()
            .all()
        )

        return list(product_equipment_list)

    @classmethod
    async def get_product_equipment_list(
        cls, db: AsyncSession, query_object: Product_equipmentPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取产品组件列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 产品组件列表信息对象
        """
        query = (
            select(ProductEquipmentInfo)
            .where(
                ProductEquipmentInfo.product_name.like(f'%{query_object.product_name}%') if query_object.product_name else True,
                ProductEquipmentInfo.product_no == query_object.product_no if query_object.product_no else True,
                ProductEquipmentInfo.price_including_tax == query_object.price_including_tax if query_object.price_including_tax else True,
                ProductEquipmentInfo.purchase_price == query_object.purchase_price if query_object.purchase_price else True,
            )
            .order_by(ProductEquipmentInfo.id)
            .distinct()
        )
        product_equipment_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return product_equipment_list

    @classmethod
    async def add_product_equipment_dao(cls, db: AsyncSession, product_equipment: Product_equipmentModel) -> ProductEquipmentInfo:
        """
        新增产品组件数据库操作

        :param db: orm对象
        :param product_equipment: 产品组件对象
        :return:
        """
        db_product_equipment = ProductEquipmentInfo(**product_equipment.model_dump(exclude={}))
        db.add(db_product_equipment)
        await db.flush()

        return db_product_equipment

    @classmethod
    async def edit_product_equipment_dao(cls, db: AsyncSession, product_equipment: dict) -> None:
        """
        编辑产品组件数据库操作

        :param db: orm对象
        :param product_equipment: 需要更新的产品组件字典
        :return:
        """
        await db.execute(update(ProductEquipmentInfo), [product_equipment])

    @classmethod
    async def delete_product_equipment_dao(cls, db: AsyncSession, product_equipment: Product_equipmentModel) -> None:
        """
        删除产品组件数据库操作

        :param db: orm对象
        :param product_equipment: 产品组件对象
        :return:
        """
        await db.execute(delete(ProductEquipmentInfo).where(ProductEquipmentInfo.id.in_([product_equipment.id])))

