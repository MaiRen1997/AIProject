import json
from datetime import datetime
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from agent.agentInstance.agent import run_agent_stream
from common.router import APIRouterPro
from config.database import AsyncSessionLocal
from module_ai.entity.vo.chat_message_vo import Chat_messageModel
from module_ai.service.chat_message_service import Chat_messageService
from module_ai.service.file_embedding_service import FileEmbeddingService
from utils.log_util import logger
from utils.response_util import ResponseUtil

agent_controller = APIRouterPro(prefix='/agent', tags=['Multi User Chat'])

# session_id -> user_id -> websocket
_CHAT_ROOMS: dict[str, dict[str, WebSocket]] = {}


class ChatClientConnectRequest(BaseModel):
    """客户端接入参数。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str | None = None
    user_id: str | None = None


class ChatSendRequest(BaseModel):
    """通过 HTTP 向房间广播消息。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    session_id: str
    sender_id: str
    content: str


async def _build_rag_context(question: str) -> str | None:
    """先检索 RAG，再将结果作为上下文提供给 AI。"""

    try:
        rag_result = await FileEmbeddingService.query_and_generate(question)
    except Exception as e:
        logger.warning(f'RAG query failed, fallback to plain AI response: {e}')
        return None

    if rag_result.matched_count <= 0:
        return None

    snippets: list[str] = []
    for idx, hit in enumerate(rag_result.hits[:5], start=1):
        snippets.append(
            f'[{idx}] file: {hit.file_name}, chunk: {hit.chunk_index}, score: {hit.score:.4f}\n{hit.content}'
        )

    joined_snippets = '\n\n'.join(snippets)
    return f'RAG summary:\n{rag_result.answer}\n\nRAG matched chunks:\n{joined_snippets}'


async def _run_ai_as_third_participant(session_id: str, user_message: str) -> None:
    """将 AI 作为第三聊天者接入会话并流式广播回复。"""

    rag_context = await _build_rag_context(user_message)
    ai_chunks: list[str] = []
    stream_id = uuid4().hex

    async for chunk in run_agent_stream(user_message, thread_id=session_id, rag_context=rag_context):
        if not chunk:
            continue
        ai_chunks.append(chunk)
        await _broadcast_to_room(
            session_id,
            {
                'type': 'content',
                'sessionId': session_id,
                'senderId': 'ai-assistant',
                'senderType': 3,
                'streamId': stream_id,
                'content': chunk,
            },
        )

    final_content = ''.join(ai_chunks).strip()
    if not final_content:
        final_content = '抱歉，我暂时没有生成有效回复。'
        await _broadcast_to_room(
            session_id,
            {
                'type': 'content',
                'sessionId': session_id,
                'senderId': 'ai-assistant',
                'senderType': 3,
                'streamId': stream_id,
                'content': final_content,
            },
        )

    await _save_ai_reply_to_db(session_id=session_id, content=final_content)

    await _broadcast_to_room(
        session_id,
        {
            'type': 'done',
            'sessionId': session_id,
            'senderId': 'ai-assistant',
            'senderType': 3,
            'streamId': stream_id,
        },
    )


async def _save_ai_reply_to_db(session_id: str, content: str) -> None:
    """将 AI 回复落库为 senderType=3。"""

    if not session_id:
        logger.warning('Skip AI message persistence because session_id is empty')
        return

    if not content or not content.strip():
        logger.warning(f'Skip AI message persistence because content is empty, session={session_id}')
        return

    now = datetime.now()
    ai_message = Chat_messageModel(
        sessionId=session_id,
        messageId=str(uuid4()),
        senderType=3,
        senderId='ai-assistant',
        senderName='AI客服',
        content=content,
        isRead=0,
        createdAt=now,
        updatedAt=now,
    )

    async with AsyncSessionLocal() as query_db:
        await Chat_messageService.add_chat_message_services(query_db, ai_message)


async def trigger_ai_reply_for_chat_message(session_id: str, sender_type: int, content: str, is_ai_response: int = 1) -> None:
    """供 /chat_message 调用：仅当用户消息(senderType=1)且 isAIResponse=1 时触发 AI+RAG。"""

    if sender_type != 1:
        return

    if int(is_ai_response or 0) != 1:
        return

    try:
        await _run_ai_as_third_participant(session_id=session_id, user_message=content)
    except Exception as e:
        logger.error(f'AI third participant failed: session={session_id}, error={e}')
        await _broadcast_to_room(
            session_id,
            {
                'type': 'error',
                'sessionId': session_id,
                'senderId': 'ai-assistant',
                'senderType': 3,
                'error': 'AI service unavailable',
            },
        )


def _list_room_users(session_id: str) -> list[str]:
    room = _CHAT_ROOMS.get(session_id, {})
    return list(room.keys())


def _register_user(session_id: str, user_id: str, websocket: WebSocket) -> None:
    room = _CHAT_ROOMS.setdefault(session_id, {})
    room[user_id] = websocket


def _unregister_user(session_id: str, user_id: str) -> None:
    room = _CHAT_ROOMS.get(session_id)
    if room is None:
        return

    room.pop(user_id, None)
    if not room:
        _CHAT_ROOMS.pop(session_id, None)


async def _broadcast_to_room(session_id: str, event: dict, exclude_user_id: str | None = None) -> None:
    room = _CHAT_ROOMS.get(session_id)
    if not room:
        return

    disconnected_users: list[str] = []
    for uid, ws in room.items():
        if exclude_user_id and uid == exclude_user_id:
            continue
        try:
            await ws.send_json(event)
        except Exception:
            disconnected_users.append(uid)

    for uid in disconnected_users:
        _unregister_user(session_id, uid)


async def _chatroom_ws_handler(websocket: WebSocket, session_id: str, user_id: str, endpoint_name: str) -> None:
    await websocket.accept()
    _register_user(session_id, user_id, websocket)
    logger.info(f'{endpoint_name} connected: session={session_id}, user={user_id}')

    await websocket.send_json(
        {
            'type': 'connected',
            'sessionId': session_id,
            'userId': user_id,
            'onlineUsers': _list_room_users(session_id),
        }
    )
    await _broadcast_to_room(
        session_id,
        {
            'type': 'user_joined',
            'sessionId': session_id,
            'userId': user_id,
            'onlineUsers': _list_room_users(session_id),
        },
        exclude_user_id=user_id,
    )

    try:
        while True:
            raw_text = await websocket.receive_text()
            if not raw_text.strip():
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

            message_type = payload.get('type', 'message')
            if message_type == 'ping':
                await websocket.send_json({'type': 'pong'})
                continue

            content = str(payload.get('content', '')).strip()
            if not content:
                await websocket.send_json({'type': 'error', 'error': 'content is required'})
                continue

            await _broadcast_to_room(
                session_id,
                {
                    'type': 'message',
                    'sessionId': session_id,
                    'senderId': user_id,
                    'content': content,
                },
            )
    except WebSocketDisconnect:
        logger.info(f'{endpoint_name} disconnected: session={session_id}, user={user_id}')
    except Exception as e:
        logger.error(f'{endpoint_name} error: session={session_id}, user={user_id}, error={e}')
        await websocket.close(code=1011)
    finally:
        _unregister_user(session_id, user_id)
        await _broadcast_to_room(
            session_id,
            {
                'type': 'user_left',
                'sessionId': session_id,
                'userId': user_id,
                'onlineUsers': _list_room_users(session_id),
            },
        )


@agent_controller.websocket('/chat/server/ws/{session_id}/{user_id}')
async def chat_server_ws(websocket: WebSocket, session_id: str, user_id: str):
    """WebSocket 服务端 API：聊天室主连接入口。"""

    await _chatroom_ws_handler(websocket, session_id, user_id, endpoint_name='chat_server_ws')


@agent_controller.websocket('/chat/client/ws/{session_id}/{user_id}')
async def chat_client_ws(websocket: WebSocket, session_id: str, user_id: str):
    """WebSocket 客户端 API：为客户端提供独立接入地址。"""

    await _chatroom_ws_handler(websocket, session_id, user_id, endpoint_name='chat_client_ws')


@agent_controller.post('/chat/client/connect', summary='创建客户端连接参数')
async def create_chat_client_connect_info(req: ChatClientConnectRequest):
    """生成客户端连接参数，供前端建立 WebSocket 连接。"""

    session_id = req.session_id or 'session-default'
    user_id = req.user_id or f'user-{uuid4().hex[:8]}'
    return ResponseUtil.success(
        msg='ok',
        data={
            'sessionId': session_id,
            'userId': user_id,
            'serverWsPath': f'/agent/chat/server/ws/{session_id}/{user_id}',
            'clientWsPath': f'/agent/chat/client/ws/{session_id}/{user_id}',
        },
    )


@agent_controller.post('/chat/client/send', summary='客户端通过 HTTP 广播消息')
async def chat_client_send_message(req: ChatSendRequest):
    """当客户端不便直连 WebSocket 时，可调用该接口向房间广播。"""

    if req.session_id not in _CHAT_ROOMS:
        return ResponseUtil.failure(msg='session not found or no online users')

    await _broadcast_to_room(
        req.session_id,
        {
            'type': 'message',
            'sessionId': req.session_id,
            'senderId': req.sender_id,
            'content': req.content,
            'source': 'http-client-api',
        },
    )
    return ResponseUtil.success(msg='message broadcast success')


@agent_controller.get('/chat/client/sessions/{session_id}/users', summary='查看会话在线用户')
async def get_chat_room_online_users(session_id: str):
    """查询房间在线用户列表。"""

    return ResponseUtil.success(data={'sessionId': session_id, 'onlineUsers': _list_room_users(session_id)})
