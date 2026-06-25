from pydantic import BaseModel, Field

class AgentChatRequest(BaseModel):
    """
    Agent对话请求模型
    """
    message: str = Field(description='用户输入的内容')
    session_id: str | None = Field(default=None, description='会话ID')
