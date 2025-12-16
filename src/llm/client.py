import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 自动加载 .env 文件
load_dotenv()


def get_llm():
    """获取配置好的 Qwen (通义千问) 客户端"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("❌ 未找到 DASHSCOPE_API_KEY，请检查 .env 文件")

    return ChatOpenAI(
        # 推荐用 qwen-plus 或 qwen-max，写代码能力更强
        model=os.getenv("LLM_MODEL", "qwen-plus"),
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.1  # 低温模式，保证代码生成的准确性
    )
