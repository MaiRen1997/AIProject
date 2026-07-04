import asyncio
import json
from collections.abc import AsyncIterable

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError
from pydantic.alias_generators import to_camel

from common.router import APIRouterPro
from utils.response_util import ResponseUtil
from agent.agentInstance.agent import run_agent_stream
from agent.entity.vo.agent_vo import AgentChatRequest
from agent.controller.utils.agentFunc import _to_async_iterable
from utils.log_util import logger

agent_controller = APIRouterPro(prefix='/agent', tags=['AI Agent'])

# session_id -> queue(events)
_WS_SESSION_QUEUES: dict[str, asyncio.Queue[dict]] = {}


class AgentWsPushRequest(BaseModel):
    """客服端向指定 WebSocket 会话推送回复内容。"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str
    message: str = Field(validation_alias=AliasChoices('message', 'messages'))
    done: bool = True


async def _event_stream(chat_req: AgentChatRequest, thread_id: str) -> AsyncIterable[dict]:
    """AI 流式事件生成器。"""
    async for chunk in run_agent_stream(chat_req.message, thread_id=thread_id):
        yield {
            'type': 'content',
            'content': chunk,
        }
    yield {
        'type': 'done',
    }


def _get_or_create_session_queue(session_id: str) -> asyncio.Queue[dict]:
    queue = _WS_SESSION_QUEUES.get(session_id)
    if queue is None:
        queue = asyncio.Queue()
        _WS_SESSION_QUEUES[session_id] = queue
    return queue


async def _enqueue_message_events(queue: asyncio.Queue[dict], message: str, done: bool = True) -> None:
    """将文本拆块后写入队列，供 WebSocket 实时下发。"""
    async for chunk in _to_async_iterable(message):
        await queue.put(
            {
                'type': 'content',
                'content': chunk,
            }
        )

    if done:
        await queue.put({'type': 'done'})


@agent_controller.post('/chat/ws/push', summary='客服推送回复到 WebSocket 会话')
async def push_ws_chat_message(push_req: AgentWsPushRequest):
    """另一个客户端调用该接口，将回答数据转发给已连接用户。"""
    queue = _WS_SESSION_QUEUES.get(push_req.session_id)
    if queue is None:
        return ResponseUtil.failure(msg='目标会话未连接或已断开')

    await _enqueue_message_events(queue, push_req.message, done=push_req.done)
    return ResponseUtil.success(msg='消息已推送到会话')


@agent_controller.websocket('/chat/ws')
async def agent_chat_ws(websocket: WebSocket):
    """用户连接后可注册会话；客服通过 /chat/ws/push 推送后，消息实时转发给该用户。"""
    await websocket.accept()
    logger.info('WebSocket 用户会话已连接')

    current_session_id: str | None = None

    try:
        while True:
            # 优先推送客服接口塞入的消息
            if current_session_id:
                queue = _WS_SESSION_QUEUES.get(current_session_id)
                if queue is not None:
                    try:
                        event = queue.get_nowait()
                        await websocket.send_json(event)
                        continue
                    except asyncio.QueueEmpty:
                        pass

            # 同时允许客户端发注册/对话消息
            try:
                raw_text = await asyncio.wait_for(websocket.receive_text(), timeout=0.2)
            except asyncio.TimeoutError:
                continue

            if not raw_text or not raw_text.strip():
                await websocket.send_json({'type': 'error', 'error': 'empty websocket message'})
                continue

            try:
                payload = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_json({'type': 'error', 'error': 'invalid json payload'})
                continue

            if not isinstance(payload, dict):
                await websocket.send_json({'type': 'error', 'error': 'invalid payload type, json object required'})
                continue

            # 兼容 messages 字段
            if 'message' not in payload and 'messages' in payload:
                payload['message'] = payload['messages']

            try:
                chat_req = AgentChatRequest.model_validate(payload)
            except ValidationError as ve:
                await websocket.send_json(
                    {
                        'type': 'error',
                        'error': 'invalid request fields',
                        'hint': 'required field: message; optional: sessionId/session_id, messageType/message_type',
                        'detail': ve.errors(),
                    }
                )
                continue

            session_id = chat_req.session_id or 'default_thread'
            current_session_id = session_id
            _get_or_create_session_queue(session_id)
            await websocket.send_json({'type': 'ready', 'sessionId': session_id})

            # 保留 AI 模式；人工模式等客服 push
            if chat_req.message_type == 1:
                async for event in _event_stream(chat_req, thread_id=session_id):
                    await websocket.send_json(event)
            else:
                await websocket.send_json(
                    {
                        'type': 'info',
                        'message': 'messageType != 1，等待客服通过 /agent/chat/ws/push 推送回复',
                    }
                )

    except WebSocketDisconnect:
        logger.info('WebSocket 用户会话已断开')
    except Exception as e:
        logger.error(f'WebSocket 会话出错: {str(e)}')
        await websocket.send_json({'type': 'error', 'error': str(e)})
        await websocket.close(code=1011)
    finally:
        if current_session_id:
            _WS_SESSION_QUEUES.pop(current_session_id, None)
