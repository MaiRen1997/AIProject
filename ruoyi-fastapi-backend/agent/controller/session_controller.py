import uuid
from common.router import APIRouterPro
from utils.response_util import ResponseUtil

# 使用项目统一的 APIRouterPro
session_controller = APIRouterPro(prefix="/session", tags=['会话模块'])

@session_controller.get('/generateSessionID', summary='生成会话ID')
async def generate_session_id():
    """
    生成并返回一个新的 UUID 字符串
    """
    new_id = str(uuid.uuid4())
    # 使用项目统一的响应格式返回数据
    return ResponseUtil.success(data=new_id)
