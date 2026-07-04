from sqlalchemy import SmallInteger, BigInteger, DateTime, String, Text, JSON, Column

from config.database import Base


class ChatMessages(Base):
    """
    聊天消息表
    """

    __tablename__ = 'chat_messages'
    __table_args__ = {'comment': '聊天消息表'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, comment='消息ID')
    session_id = Column(String(64), nullable=False, comment='会话ID')
    message_id = Column(String(64), nullable=False, comment='消息唯一标识（UUID）')
    sender_type = Column(SmallInteger, nullable=False, comment='发送者类型: 1-用户, 2-人工客服, 3-AI客服')
    sender_id = Column(String(32), nullable=True, comment='发送者ID（user_id或agent_id）')
    sender_name = Column(String(100), nullable=True, comment='发送者昵称')
    receiver_id = Column(String(32), nullable=True, comment='接收者ID')
    content = Column(Text, nullable=False, comment='消息内容（文本内容或JSON格式的富文本）')
    extra_data = Column(JSON, nullable=True, comment='扩展数据（JSON格式，存储额外信息）')
    is_read = Column(SmallInteger, nullable=True, comment='是否已读: 0-未读, 1-已读')
    read_time = Column(DateTime, nullable=True, comment='读取时间')
    is_deleted = Column(SmallInteger, nullable=True, comment='是否删除: 0-否, 1-是（软删除）')
    created_at = Column(DateTime, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, nullable=False, comment='更新时间')



