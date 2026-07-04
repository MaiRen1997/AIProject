from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank




class Chat_messageModel(BaseModel):
    """
    聊天消息表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='消息ID')
    session_id: str | None = Field(default=None, description='会话ID')
    message_id: str | None = Field(default=None, description='消息唯一标识（UUID）')
    sender_type: int | None = Field(default=None, description='发送者类型: 1-用户, 2-人工客服, 3-AI客服')
    sender_id: str | None = Field(default=None, description='发送者ID（user_id或agent_id）')
    sender_name: str | None = Field(default=None, description='发送者昵称')
    receiver_id: str | None = Field(default=None, description='接收者ID')
    content: str | None = Field(default=None, description='消息内容（文本内容或JSON格式的富文本）')
    extra_data: dict | None = Field(default=None, description='扩展数据（JSON格式，存储额外信息）')
    is_read: int | None = Field(default=None, description='是否已读: 0-未读, 1-已读')
    read_time: datetime | None = Field(default=None, description='读取时间')
    is_deleted: int | None = Field(default=None, description='是否删除: 0-否, 1-是（软删除）')
    created_at: datetime | None = Field(default=None, description='创建时间')
    updated_at: datetime | None = Field(default=None, description='更新时间')

    @NotBlank(field_name='id', message='消息ID不能为空')
    def get_id(self) -> int | None:
        return self.id

    @NotBlank(field_name='session_id', message='会话ID不能为空')
    def get_session_id(self) -> str | None:
        return self.session_id

    @NotBlank(field_name='message_id', message='消息唯一标识不能为空')
    def get_message_id(self) -> str | None:
        return self.message_id

    @NotBlank(field_name='sender_type', message='发送者类型: 1-用户, 2-人工客服, 3-AI客服不能为空')
    def get_sender_type(self) -> int | None:
        return self.sender_type

    def get_sender_id(self) -> str | None:
        return self.sender_id

    @NotBlank(field_name='content', message='消息内容不能为空')
    def get_content(self) -> str | None:
        return self.content

    @NotBlank(field_name='created_at', message='创建时间不能为空')
    def get_created_at(self) -> datetime | None:
        return self.created_at

    @NotBlank(field_name='updated_at', message='更新时间不能为空')
    def get_updated_at(self) -> datetime | None:
        return self.updated_at

    def validate_fields(self) -> None:
        self.get_session_id()
        self.get_message_id()
        self.get_sender_type()
        self.get_content()
        self.get_created_at()
        self.get_updated_at()




class Chat_messageQueryModel(Chat_messageModel):
    """
    聊天消息不分页查询模型
    """
    pass


class Chat_messagePageQueryModel(Chat_messageQueryModel):
    """
    聊天消息分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddChat_messageModel(Chat_messageModel):
    """
    新增聊天消息模型
    """

    def validate_fields(self) -> None:
        self.get_session_id()
        self.get_sender_type()
        self.get_content()


class EditChat_messageModel(Chat_messageModel):
    """
    编辑聊天消息模型
    """

    def validate_fields(self) -> None:
        self.get_id()


class DeleteChat_messageModel(BaseModel):
    """
    删除聊天消息模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的消息ID')
