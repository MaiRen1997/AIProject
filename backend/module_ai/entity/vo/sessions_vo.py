from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank




class SessionsModel(BaseModel):
    """
    用户会话关联表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='主键ID')
    user_id: str | None = Field(default=None, description='用户ID')
    session_id: str | None = Field(default=None, description='会话ID')
    created_at: datetime | None = Field(default=None, description='创建时间')
    is_active: int | None = Field(default=None, description='是否仍在会话中: 1-是, 0-否')
    is_deleted: int | None = Field(default=None, description='是否删除: 1-是, 0-否')

    @NotBlank(field_name='user_id', message='用户ID不能为空')
    def get_user_id(self) -> str | None:
        return self.user_id

    @NotBlank(field_name='session_id', message='会话ID不能为空')
    def get_session_id(self) -> str | None:
        return self.session_id

    @NotBlank(field_name='created_at', message='创建时间不能为空')
    def get_created_at(self) -> datetime | None:
        return self.created_at


    def validate_fields(self) -> None:
        self.get_user_id()
        self.get_session_id()
        self.get_created_at()




class SessionsQueryModel(SessionsModel):
    """
    用户会话关联不分页查询模型
    """
    pass


class SessionsPageQueryModel(SessionsQueryModel):
    """
    用户会话关联分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class AddSessionsModel(SessionsModel):
    """
    新增用户会话关联模型
    """

    def validate_fields(self) -> None:
        self.get_user_id()
        self.get_session_id()


class DeleteSessionsModel(BaseModel):
    """
    删除用户会话关联模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的主键ID')
