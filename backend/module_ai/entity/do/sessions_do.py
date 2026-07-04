from sqlalchemy import DateTime, SmallInteger, Column, BigInteger, String

from config.database import Base


class UserSessions(Base):
    """
    用户会话关联表
    """

    __tablename__ = 'user_sessions'
    __table_args__ = {'comment': '用户会话关联表'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, comment='主键ID')
    user_id = Column(String(32), nullable=False, comment='用户ID')
    session_id = Column(String(64), nullable=False, comment='会话ID')
    created_at = Column(DateTime, nullable=False, comment='创建时间')
    is_active = Column(SmallInteger, nullable=True, comment='是否仍在会话中: 1-是, 0-否')



