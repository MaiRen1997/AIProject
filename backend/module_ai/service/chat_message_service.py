from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_ai.dao.chat_message_dao import Chat_messageDao
from module_ai.entity.vo.chat_message_vo import DeleteChat_messageModel, Chat_messageModel, Chat_messagePageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil


class Chat_messageService:
    """
    聊天消息模块服务层
    """

    @classmethod
    async def get_chat_message_list_services(
        cls, query_db: AsyncSession, query_object: Chat_messagePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取聊天消息列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 聊天消息列表信息对象
        """
        chat_message_list_result = await Chat_messageDao.get_chat_message_list(query_db, query_object, is_page)

        return chat_message_list_result


    @classmethod
    async def add_chat_message_services(cls, query_db: AsyncSession, page_object: Chat_messageModel) -> CrudResponseModel:
        """
        新增聊天消息信息service

        :param query_db: orm对象
        :param page_object: 新增聊天消息对象
        :return: 新增聊天消息校验结果
        """
        try:
            await Chat_messageDao.add_chat_message_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_chat_message_services(cls, query_db: AsyncSession, page_object: Chat_messageModel) -> CrudResponseModel:
        """
        编辑聊天消息信息service

        :param query_db: orm对象
        :param page_object: 编辑聊天消息对象
        :return: 编辑聊天消息校验结果
        """
        edit_chat_message = page_object.model_dump(exclude_unset=True, exclude={})
        chat_message_info = await cls.chat_message_detail_services(query_db, page_object.id)
        if chat_message_info.id:
            try:
                await Chat_messageDao.edit_chat_message_dao(query_db, edit_chat_message)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='聊天消息不存在')

    @classmethod
    async def delete_chat_message_services(cls, query_db: AsyncSession, page_object: DeleteChat_messageModel) -> CrudResponseModel:
        """
        删除聊天消息信息service

        :param query_db: orm对象
        :param page_object: 删除聊天消息对象
        :return: 删除聊天消息校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    await Chat_messageDao.delete_chat_message_dao(query_db, Chat_messageModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入消息ID为空')

    @classmethod
    async def chat_message_detail_services(cls, query_db: AsyncSession, id: int) -> Chat_messageModel:
        """
        获取聊天消息详细信息service

        :param query_db: orm对象
        :param id: 消息ID
        :return: 消息ID对应的信息
        """
        chat_message = await Chat_messageDao.get_chat_message_detail_by_id(query_db, id=id)
        result = Chat_messageModel(**CamelCaseUtil.transform_result(chat_message)) if chat_message else Chat_messageModel()

        return result

    @staticmethod
    async def export_chat_message_list_services(chat_message_list: list) -> bytes:
        """
        导出聊天消息信息service

        :param chat_message_list: 聊天消息信息列表
        :return: 聊天消息信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'id': '消息ID',
            'sessionId': '会话ID',
            'messageId': '消息唯一标识',
            'senderType': '发送者类型: 1-用户, 2-人工客服, 3-AI客服',
            'senderId': '发送者ID',
            'senderName': '发送者昵称',
            'receiverId': '接收者ID',
            'content': '消息内容',
            'extraData': '扩展数据',
            'isRead': '是否已读: 0-未读, 1-已读',
            'readTime': '读取时间',
            'isDeleted': '是否删除: 0-否, 1-是',
            'createdAt': '创建时间',
            'updatedAt': '更新时间',
        }
        binary_data = ExcelUtil.export_list2excel(chat_message_list, mapping_dict)

        return binary_data
