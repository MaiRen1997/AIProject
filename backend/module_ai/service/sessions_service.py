from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.sessions_dao import SessionsDao
from module_ai.entity.vo.sessions_vo import DeleteSessionsModel, SessionsModel, SessionsPageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil


class SessionsService:
    """
    用户会话关联模块服务层
    """

    @classmethod
    async def get_sessions_list_services(
        cls, query_db: AsyncSession, query_object: SessionsPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取用户会话关联列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 用户会话关联列表信息对象
        """
        sessions_list_result = await SessionsDao.get_sessions_list(query_db, query_object, is_page)

        return sessions_list_result


    @classmethod
    async def add_sessions_services(cls, query_db: AsyncSession, page_object: SessionsModel) -> CrudResponseModel:
        """
        新增用户会话关联信息service

        :param query_db: orm对象
        :param page_object: 新增用户会话关联对象
        :return: 新增用户会话关联校验结果
        """
        sessions_info = await SessionsDao.get_sessions_detail_by_info(query_db, page_object)
        if not sessions_info:
            try:
                await SessionsDao.add_sessions_dao(query_db, page_object)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='新增成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    async def edit_sessions_services(cls, query_db: AsyncSession, page_object: SessionsModel) -> CrudResponseModel:
        """
        编辑用户会话关联信息service

        :param query_db: orm对象
        :param page_object: 编辑用户会话关联对象
        :return: 编辑用户会话关联校验结果
        """
        edit_sessions = page_object.model_dump(exclude_unset=True, exclude={})
        sessions_info = await cls.sessions_detail_services(query_db, page_object.id)
        if sessions_info.id:
            try:
                await SessionsDao.edit_sessions_dao(query_db, edit_sessions)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='用户会话关联不存在')

    @classmethod
    async def delete_sessions_services(cls, query_db: AsyncSession, page_object: DeleteSessionsModel) -> CrudResponseModel:
        """
        删除用户会话关联信息service

        :param query_db: orm对象
        :param page_object: 删除用户会话关联对象
        :return: 删除用户会话关联校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await SessionsDao.delete_sessions_dao(query_db, SessionsModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入主键ID为空')

    @classmethod
    async def sessions_detail_services(cls, query_db: AsyncSession, id: int) -> SessionsModel:
        """
        获取用户会话关联详细信息service

        :param query_db: orm对象
        :param id: 主键ID
        :return: 主键ID对应的信息
        """
        sessions = await SessionsDao.get_sessions_detail_by_id(query_db, id=id)
        result = SessionsModel(**CamelCaseUtil.transform_result(sessions)) if sessions else SessionsModel()

        return result

    @staticmethod
    async def export_sessions_list_services(sessions_list: list) -> bytes:
        """
        导出用户会话关联信息service

        :param sessions_list: 用户会话关联信息列表
        :return: 用户会话关联信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'id': '主键ID',
            'userId': '用户ID',
            'sessionId': '会话ID',
            'createdAt': '创建时间',
            'isActive': '是否仍在会话中: 1-是, 0-否',
            'isDeleted': '是否删除: 1-是, 0-否',
        }
        binary_data = ExcelUtil.export_list2excel(sessions_list, mapping_dict)

        return binary_data
