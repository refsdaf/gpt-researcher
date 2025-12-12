import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableSerializable, Runnable
from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Any, List, Optional

class MockChatModel(RunnableSerializable):
    """一个模拟的聊天模型，返回上下文感知的响应。"""

    responses: dict = {
            "Analyze the JD": json.dumps({
                "hard_skills": ["Python", "React", "PostgreSQL", "AWS"],
                "soft_skills": ["Scrappy", "Entrepreneurial"],
                "pain_points": "Legacy code is slow, need refactoring while shipping.",
                "culture": "Startup/Modern, fast-paced.",
                "key_responsibilities": "Architect backend, Lead frontend, Mentor juniors."
            }),
            "Rewrite the Professional Summary": "Senior Full Stack Engineer (Python/React) with 5 years experience. Expert in Python and React. Proven track record of architecting scalable systems and refactoring legacy code in fast-paced startup environments.",
            "tailor a specific job entry": json.dumps([
                "**Orchestrated cross-functional collaboration** to build a react app, matching startup speed.",
                "Optimized database queries, solving complex performance bottlenecks.",
                "Managed a team of 3, mentoring junior engineers."
            ]),
            "optimizing the \"Skills\" section": json.dumps(["Python", "React", "PostgreSQL", "AWS", "CI/CD", "Git", "SQL"])
        }

    def invoke(self, input: Any, config: Optional[Any] = None) -> AIMessage:
        # 通过检查输入文本来确定正在使用哪个提示词
        text = str(input)

        response_content = "Mock response"
        for key, val in self.responses.items():
            if key in text or key in str(input):
                response_content = val
                break

        return AIMessage(content=response_content)

def get_llm():
    """返回配置好的 LLM 实例，如果没有密钥则返回 Mock。"""
    if os.environ.get("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o", temperature=0)
    else:
        print("NOTICE: OPENAI_API_KEY not found. Using Mock LLM.")
        return MockChatModel()

def get_search_tool():
    """如果可用则返回搜索工具，否则返回 Mock。"""
    if os.environ.get("TAVILY_API_KEY"):
        return TavilySearchResults()
    else:
        # 用于没有 API 密钥的测试的模拟工具
        def mock_search(query: str):
            return "Mock search results: Company values are Innovation and Speed."
        return Tool(name="search", func=mock_search, description="Search the web.")
