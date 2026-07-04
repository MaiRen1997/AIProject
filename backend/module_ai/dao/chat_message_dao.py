from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.chat_message_do import ChatMessages
from module_ai.entity.vo.chat_message_vo import Chat_messageModel, Chat_messagePageQueryModel
from utils.page_util import PageUtil


class Chat_messageDao:
    """
    聊天消息模块数据库操作层
    """

    @classmethod
    async def get_chat_message_detail_by_id(cls, db: AsyncSession, id: int) -> ChatMessages | None:
        """
        根据消息ID获取聊天消息详细信息

        :param db: orm对象
        :param id: 消息ID
        :return: 聊天消息信息对象
        """
        chat_message_info = (
            (
                await db.execute(
                    select(ChatMessages)
                    .where(
                        ChatMessages.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return chat_message_info

    @classmethod
    async def get_chat_message_detail_by_info(cls, db: AsyncSession, chat_message: Chat_messageModel) -> ChatMessages | None:
        """
        根据聊天消息参数获取聊天消息信息

        :param db: orm对象
        :param chat_message: 聊天消息参数对象
        :return: 聊天消息信息对象
        """
        chat_message_info = (
            (
                await db.execute(
                    select(ChatMessages).where(
                    )
                )
            )
            .scalars()
            .first()
        )

        return chat_message_info

    @classmethod
    async def get_chat_message_list(
        cls, db: AsyncSession, query_object: Chat_messagePageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取聊天消息列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 聊天消息列表信息对象
        """
        query = (
            select(ChatMessages)
            .where(
                ChatMessages.session_id == query_object.session_id if query_object.session_id else True,
                ChatMessages.message_id == query_object.message_id if query_object.message_id else True,
                ChatMessages.sender_type == query_object.sender_type if query_object.sender_type else True,
                ChatMessages.sender_id == query_object.sender_id if query_object.sender_id else True,
                ChatMessages.sender_name.like(f'%{query_object.sender_name}%') if query_object.sender_name else True,
                ChatMessages.receiver_id == query_object.receiver_id if query_object.receiver_id else True,
                ChatMessages.content == query_object.content if query_object.content else True,
                ChatMessages.extra_data == query_object.extra_data if query_object.extra_data else True,
                ChatMessages.is_read == query_object.is_read if query_object.is_read else True,
                ChatMessages.read_time == query_object.read_time if query_object.read_time else True,
                ChatMessages.is_deleted == query_object.is_deleted if query_object.is_deleted else True,
                ChatMessages.created_at == query_object.created_at if query_object.created_at else True,
                ChatMessages.updated_at == query_object.updated_at if query_object.updated_at else True,
            )
            .order_by(ChatMessages.id)
            .distinct()
        )
        chat_message_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return chat_message_list

    @classmethod
    async def add_chat_message_dao(cls, db: AsyncSession, chat_message: Chat_messageModel) -> ChatMessages:
        """
        新增聊天消息数据库操作

        :param db: orm对象
        :param chat_message: 聊天消息对象
        :return:
        """
        db_chat_message = ChatMessages(**chat_message.model_dump(exclude={}))
        db.add(db_chat_message)
        await db.flush()

        return db_chat_message

    @classmethod
    async def edit_chat_message_dao(cls, db: AsyncSession, chat_message: dict) -> None:
        """
        编辑聊天消息数据库操作

        :param db: orm对象
        :param chat_message: 需要更新的聊天消息字典
        :return:
        """
        await db.execute(update(ChatMessages), [chat_message])

    @classmethod
    async def delete_chat_message_dao(cls, db: AsyncSession, chat_message: Chat_messageModel) -> None:
        """
        删除聊天消息数据库操作

        :param db: orm对象
        :param chat_message: 聊天消息对象
        :return:
        """
        await db.execute(delete(ChatMessages).where(ChatMessages.id.in_([chat_message.id])))

