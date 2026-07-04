from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.sessions_do import UserSessions
from module_ai.entity.vo.sessions_vo import SessionsModel, SessionsPageQueryModel
from utils.page_util import PageUtil


class SessionsDao:
    """
    用户会话关联模块数据库操作层
    """

    @classmethod
    async def get_sessions_detail_by_id(cls, db: AsyncSession, id: int) -> UserSessions | None:
        """
        根据主键ID获取用户会话关联详细信息

        :param db: orm对象
        :param id: 主键ID
        :return: 用户会话关联信息对象
        """
        sessions_info = (
            (
                await db.execute(
                    select(UserSessions)
                    .where(
                        UserSessions.id == id
                    )
                )
            )
            .scalars()
            .first()
        )

        return sessions_info

    @classmethod
    async def get_sessions_detail_by_info(cls, db: AsyncSession, sessions: SessionsModel) -> UserSessions | None:
        """
        根据用户会话关联参数获取用户会话关联信息

        :param db: orm对象
        :param sessions: 用户会话关联参数对象
        :return: 用户会话关联信息对象
        """
        sessions_info = (
            (
                await db.execute(
                    select(UserSessions).where(UserSessions.session_id == sessions.session_id if sessions.session_id else True)
                )
            )
            .scalars()
            .first()
        )

        return sessions_info

    @classmethod
    async def get_sessions_list(
        cls, db: AsyncSession, query_object: SessionsPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """
        根据查询参数获取用户会话关联列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 用户会话关联列表信息对象
        """
        query = (
            select(UserSessions)
            .where(
                UserSessions.user_id == query_object.user_id if query_object.user_id else True,
                UserSessions.session_id == query_object.session_id if query_object.session_id else True,
                UserSessions.created_at == query_object.created_at if query_object.created_at else True,
                UserSessions.is_active == query_object.is_active if query_object.is_active else True,
            )
            .order_by(UserSessions.id)
            .distinct()
        )
        sessions_list: PageModel | list[dict[str, Any]] = await PageUtil.paginate(
            db, query, query_object.page_num, query_object.page_size, is_page
        )

        return sessions_list

    @classmethod
    async def add_sessions_dao(cls, db: AsyncSession, sessions: SessionsModel) -> UserSessions:
        """
        新增用户会话关联数据库操作

        :param db: orm对象
        :param sessions: 用户会话关联对象
        :return:
        """
        db_sessions = UserSessions(**sessions.model_dump(exclude={}))
        db.add(db_sessions)
        await db.flush()

        return db_sessions

    @classmethod
    async def edit_sessions_dao(cls, db: AsyncSession, sessions: dict) -> None:
        """
        编辑用户会话关联数据库操作

        :param db: orm对象
        :param sessions: 需要更新的用户会话关联字典
        :return:
        """
        await db.execute(update(UserSessions), [sessions])

    @classmethod
    async def delete_sessions_dao(cls, db: AsyncSession, sessions: SessionsModel) -> None:
        """
        删除用户会话关联数据库操作

        :param db: orm对象
        :param sessions: 用户会话关联对象
        :return:
        """
        await db.execute(delete(UserSessions).where(UserSessions.id.in_([sessions.id])))

