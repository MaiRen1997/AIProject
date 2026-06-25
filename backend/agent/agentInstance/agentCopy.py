"""
使用LangGraph框架的AI Agent实例
集成DeepSeek API，支持工具调用
使用 create_react_agent 简化架构
"""

import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
# from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage

# 加载 .env 文件
load_dotenv()

# 从 .env 文件读取配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE_URL = os.getenv("DEEPSEEK_API_BASE_URL")

# ============= 定义工具 =============
from agent.tools.getReciple import get_sulfuric_acid_standards

# 工具列表 (移除了不存在的工具，保留存在的)
tools = [get_sulfuric_acid_standards]

# ============= 初始化LLM =============
def create_llm():
    """创建LLM实例，使用DeepSeek API"""
    return ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_API_BASE_URL,
        model="deepseek-chat",
        temperature=0.7,
    )

# ============= 创建Agent =============
# 全局 checkpointer 实例，确保跨请求内存持久化
_checkpointer = InMemorySaver()

def create_agent_instance():
    """使用 create_react_agent 创建 Agent"""
    llm = create_llm()
    
    # 定义全能助手系统提示词 (Multi-functional Identity)
    system_modifier_text = (
        "你是一个全能的智能助手，能够高效处理多样化的任务，包括：\n"
        "- 【行政与沟通】：协助用户撰写和发送电子邮件。\n"
        "- 【信息与实时】：获取当前时间、进行互联网信息查询。\n"
        "- 【实验与安全】：指导化学实验操作，并对危险品配比进行严谨的安全评估。\n\n"
        "【行为准则】\n"
        "1. 身份切换：根据用户的需求自动适配角色（如秘书、研究员、实验专家）。\n"
        "2. 安全与严谨：在涉及化学配制等风险操作时，必须调用相关标准工具获取参考，并基于数据进行严谨的逻辑推理。\n"
        "3. 交互体验：回答应清晰、专业，并在复杂操作前提供必要的安全提醒。"
    )

    # 兼容性处理：尝试使用 state_modifier 或 messages_modifier
    try:
        # 最新版 LangGraph 使用 state_modifier
        return create_agent(
            llm, 
            tools, 
            checkpointer=_checkpointer,
            state_modifier=system_modifier_text
        )
    except TypeError:
        try:
            # 较旧版使用 messages_modifier
            return create_agent(
                llm, 
                tools, 
                checkpointer=_checkpointer,
                messages_modifier=system_modifier_text
            )
        except TypeError:
            # 如果都不支持，创建一个基础 Agent
            return create_agent(
                llm, 
                tools, 
                checkpointer=_checkpointer
            )

# 创建全局 Agent 实例
_agent_instance = create_agent_instance()

# ============= 主函数 =============
def run_agent(user_input: str, thread_id: str = "default_thread"):
    """运行Agent"""
    config = {"configurable": {"thread_id": thread_id}}
    
    input_messages = {"messages": [("user", user_input)]}

    print(f"\n用户输入: {user_input}")
    print("-" * 50)

    # 执行Agent
    result = _agent_instance.stream(input_messages, config)

    # 获取最后一条消息（Agent的响应）
    final_response = result["messages"][-1]

    print(f"\nAgent响应: {final_response.content}")
    print("-" * 50)

    return result