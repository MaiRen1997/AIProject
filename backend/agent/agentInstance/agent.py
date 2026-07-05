"""
使用LangGraph框架的AI Agent实例
集成DeepSeek API，支持工具调用
使用 create_react_agent 简化架构
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from utils.log_util import logger
# 加载 .env 文件
BACKEND_ROOT = Path(__file__).resolve().parents[2]
APP_ENV = os.getenv("APP_ENV", "dev")
load_dotenv(BACKEND_ROOT / f".env.{APP_ENV}")
load_dotenv(BACKEND_ROOT / ".env")

# 从 .env 文件读取配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE_URL = os.getenv("DEEPSEEK_API_BASE_URL")

# ============= 定义工具 =============
from agent.tools.getReciple import get_sulfuric_acid_standards

# 工具列表
tools = [get_sulfuric_acid_standards]

# ============= 初始化LLM（启用流式） =============
def create_llm():
    """创建LLM实例，使用DeepSeek API，启用流式输出"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError(
            f"DEEPSEEK_API_KEY is not configured. Expected it in {BACKEND_ROOT / f'.env.{APP_ENV}'} "
            "or the process environment."
        )

    return ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_API_BASE_URL,
        model="deepseek-chat",
        temperature=0.7,
        streaming=True,  # ✅ 关键：启用流式输出
    )

# ============= 创建Agent =============
_checkpointer = InMemorySaver()

def create_agent_instance():
    """使用 create_agent 创建 Agent"""
    llm = create_llm()

    system_modifier_text = (
        "你是一个全能的智能助手，能够高效处理多样化的任务，包括：\n"
        "- 【行政与沟通】：协助用户撰写和发送电子邮件。\n"
        "- 【信息与实时】：获取当前时间、进行互联网信息查询。\n"
        "- 【实验与安全】：指导化学实验操作，并对危险品配比进行严谨的安全评估。\n\n"
        "【行为准则】\n"
        "1. 身份切换：根据用户的需求自动适配角色（如秘书、研究员、实验专家）。\n"
        "2. 安全与严谨：在涉及化学配制等风险操作时，必须调用相关标准工具获取参考，并基于数据进行严谨的逻辑推理。\n"
        "3. 交互体验：回答应清晰、专业，并在复杂操作前提供必要的安全提醒。"
        "3. 回复原则：你应该先判断用户输入的是什么语言，然后将答案，翻译成相应的语言进行回答。"
    )

    try:
        return create_agent(
            llm,
            tools,
            checkpointer=_checkpointer,
            state_modifier=system_modifier_text
        )
    except TypeError:
        try:
            return create_agent(
                llm,
                tools,
                checkpointer=_checkpointer,
                messages_modifier=system_modifier_text
            )
        except TypeError:
            return create_agent(
                llm,
                tools,
                checkpointer=_checkpointer
            )

_agent_instance = create_agent_instance()

# ============= 流式运行函数 =============
def _build_grounded_user_input(user_input: str, rag_context: str | None = None) -> str:
    """将 RAG 检索内容拼接为用户输入，帮助 Agent 基于证据回答。"""
    if not rag_context:
        return user_input

    return (
        "以下是知识库检索结果，请优先基于这些内容回答；若证据不足请明确说明。\n\n"
        f"{rag_context}\n\n"
        "用户问题：\n"
        f"{user_input}"
    )


async def run_agent_stream(user_input: str, thread_id: str = "default_thread", rag_context: str | None = None):
    """
    流式运行Agent，逐步返回输出

    Args:
        user_input: 用户输入
        thread_id: 会话线程ID

    Yields:
        str: 逐步输出的内容块
    """
    config = {"configurable": {"thread_id": thread_id}}
    grounded_input = _build_grounded_user_input(user_input, rag_context)
    input_messages = {"messages": [("user", grounded_input)]}

    print(f"\n用户输入: {user_input}")
    print("-" * 50)

    try:
        # 使用 astream_events 获取更细粒度的流式事件
        async for event in _agent_instance.astream_events(
            input_messages,
            config,
            version="v1"
        ):
            # 监听 LLM 流式输出事件
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield chunk.content
                    print(chunk.content, end="", flush=True)

            # 可选：监听工具调用事件
            elif event["event"] == "on_tool_start":
                logger.info(f"开始调用工具: {event['name']}")

            elif event["event"] == "on_tool_end":
                logger.info(f"工具调用完成: {event['name']}")

        print("\n" + "-" * 50)
        print("流式输出完成")

    except Exception as e:
        error_msg = f"Agent 运行出错: {str(e)}"
        print(error_msg)
        yield f"\n[错误]: {error_msg}\n"


# ============= 保留原有的非流式函数（可选） =============
def run_agent(user_input: str, thread_id: str = "default_thread", rag_context: str | None = None):
    """非流式运行Agent（向后兼容）"""
    config = {"configurable": {"thread_id": thread_id}}
    grounded_input = _build_grounded_user_input(user_input, rag_context)
    input_messages = {"messages": [("user", grounded_input)]}

    print(f"\n用户输入: {user_input}")
    print("-" * 50)

    result = _agent_instance.invoke(input_messages, config)
    final_response = result["messages"][-1]

    print(f"\nAgent响应: {final_response.content}")
    print("-" * 50)

    return result
