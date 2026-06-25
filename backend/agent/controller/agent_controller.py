import json
import httpx
import os
from fastapi import Request
from fastapi.responses import StreamingResponse
from common.router import APIRouterPro
from utils.response_util import ResponseUtil
from agent.agentInstance.agent import run_agent_stream  # 导入流式函数
from agent.entity.vo.agent_vo import AgentChatRequest
from utils.log_util import logger

agent_controller = APIRouterPro(prefix='/agent', tags=['AI Agent'])


def _format_sse(data) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n"


@agent_controller.post('/chat/stream', summary='Agent 对话接口')
async def agent_chat(request: Request, chat_req: AgentChatRequest):
    """
    Agent 对话接口，接收用户输入并返回流式 AI 响应
    """
    logger.info(f"收到 Agent 对话请求: {chat_req.message}")
    # 调用飞书机器人触发警告
    # 注意：飞书 webhook 对 payload 格式有严格要求。这里使用最简单的 text 格式。
    # webhook 地址建议放到环境变量或配置中，避免写死在代码里。
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL") or "https://open.feishu.cn/open-apis/bot/v2/hook/fe239919-994b-4ef1-94a6-560446e10171"
    payload = {
        "msg_type": "text",
        "content": {"text": f"Agent 警告：{chat_req.message[:200]}"}
    }

    # 使用异步 HTTP 客户端，避免在 FastAPI 的 async 视图中阻塞线程
    # try:
    #     async with httpx.AsyncClient(timeout=10.0) as client:
    #         resp = await client.post(webhook_url, json=payload)
    #         logger.info(f"Feishu webhook POST status: {resp.status_code}, body: {resp.text}")
    #         if resp.status_code >= 400:
    #             logger.warning("Feishu webhook 返回错误状态，可能未发送成功")
    # except Exception as ex:
    #     logger.error(f"调用 Feishu webhook 失败: {ex}")
    thread_id = chat_req.session_id or "default_thread"

    async def generate_stream():
        """生成流式响应"""
        try:
            async for chunk in run_agent_stream(chat_req.message, thread_id=thread_id):
                # 使用 Server-Sent Events 格式
                yield _format_sse({
                    "type": "content",
                    "content": chunk,
                })

            # 发送结束标记
            yield _format_sse({
                "type": "done",
            })

        except Exception as e:
            logger.error(f"Agent 流式运行出错: {str(e)}")
            yield _format_sse({
                "type": "error",
                "error": str(e),
            })

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",  # SSE 格式
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


# 可选：保留非流式接口
@agent_controller.post('/chat/sync', summary='Agent 对话接口（同步）')
async def agent_chat_sync(chat_req: AgentChatRequest):
    """
    同步对话接口（非流式），返回完整响应
    """
    from agent.agentInstance.agent import run_agent

    logger.info(f"收到同步 Agent 对话请求: {chat_req.message}")

    thread_id = chat_req.session_id or "default_thread"

    try:
        result = run_agent(chat_req.message, thread_id=thread_id)
        final_response = result["messages"][-1]
        ai_content = final_response.content

        logger.info(f"Agent 响应成功: {ai_content[:50]}...")
        return ResponseUtil.success(data=ai_content)

    except Exception as e:
        logger.error(f"Agent 运行出错: {str(e)}")
        return ResponseUtil.error(msg=f"Agent 运行出错: {str(e)}")
