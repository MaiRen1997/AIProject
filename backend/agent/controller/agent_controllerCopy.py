from fastapi import Request
from common.router import APIRouterPro
from utils.response_util import ResponseUtil
from agent.agentInstance.agent import run_agent
from agent.entity.vo.agent_vo import AgentChatRequest
from utils.log_util import logger

agent_controller = APIRouterPro(prefix='/agent', tags=['AI Agent'])


@agent_controller.post('/chat', summary='Agent 对话接口')
async def agent_chat(request: Request, chat_req: AgentChatRequest):
    """
    Agent 对话接口，接收用户输入并返回 AI 响应
    """
    logger.info(f"收到 Agent 对话请求: {chat_req.message}")

    # 调用 Agent 运行函数
    # 使用传入的 session_id 或者默认值
    thread_id = chat_req.session_id or "default_thread"

    try:
        result = run_agent(chat_req.message, thread_id=thread_id)

        # 获取最后一条消息作为 AI 的响应内容
        final_response = result["messages"][-1]
        ai_content = final_response.content

        logger.info(f"Agent 响应成功: {ai_content[:50]}...")

        return ResponseUtil.success(data=ai_content)
    except Exception as e:
        logger.error(f"Agent 运行出错: {str(e)}")
        return ResponseUtil.error(msg=f"Agent 运行出错: {str(e)}")