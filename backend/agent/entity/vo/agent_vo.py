from pydantic import BaseModel, Field

class AgentChatRequest(BaseModel):
    """
    Agent对话请求模型
    """
    message: str = Field(description='用户输入的内容')
    session_id: str | None = Field(default=None, description='会话ID')
    message_type: int = Field(description='用户请求的数据类型，人工客服还是AI客服，0是人工,1是AI客服', default=1)
