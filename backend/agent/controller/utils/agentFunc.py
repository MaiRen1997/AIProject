import httpx
import os
from utils.log_util import logger
from collections.abc import AsyncIterable
import asyncio
# 将普通字符串封装为异步可迭代对象，便于按块流式输出
def _to_async_iterable(message: str, chunk_size: int = 1) -> AsyncIterable[str]:
    """将普通字符串封装为异步可迭代对象，便于按块流式输出。"""

    async def _gen():
        for idx in range(0, len(message), chunk_size):
            yield message[idx: idx + chunk_size]
            await asyncio.sleep(0)

    return _gen()
# 调用飞书机器人触发警告
async def call_feishu_webhook(chat_req):
    # 注意：飞书 webhook 对 payload 格式有严格要求。这里使用最简单的 text 格式。
    # webhook 地址建议放到环境变量或配置中，避免写死在代码里。
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL") or "https://open.feishu.cn/open-apis/bot/v2/hook/fe239919-994b-4ef1-94a6-560446e10171"
    payload = {
        "msg_type": "text",
        "content": {"text": f"Agent 警告：{chat_req.message[:200]}"}
    }

    # 使用异步 HTTP 客户端，避免在 FastAPI 的 async 视图中阻塞线程
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            logger.info(f"Feishu webhook POST status: {resp.status_code}, body: {resp.text}")
            if resp.status_code >= 400:
                logger.warning("Feishu webhook 返回错误状态，可能未发送成功")
    except Exception as ex:
        logger.error(f"调用 Feishu webhook 失败: {ex}")