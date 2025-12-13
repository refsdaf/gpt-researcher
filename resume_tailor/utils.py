import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableSerializable, Runnable
from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Any, List, Optional
from .config import Config

class MockChatModel(RunnableSerializable):
    """一个模拟的聊天模型，返回上下文感知的响应。"""

    responses: dict = {
            "Analyze the JD": json.dumps({
                "hard_skills": ["Python", "React", "PostgreSQL", "AWS"],
                "soft_skills": ["Scrappy", "Entrepreneurial"],
                "pain_points": "Legacy code is slow, need refactoring while shipping.",
                "culture": "Startup/Modern, fast-paced.",
                "key_responsibilities": "Architect backend, Lead frontend, Mentor juniors.",
                "brand_vibe": "Bold and Minimalist"
            }),
            "Strategic Resume Consultant": json.dumps({
                "target_title": "Senior Full Stack Engineer",
                "section_order": ["summary", "key_achievements", "experience", "skills"],
                "key_achievements": [
                    "Built scalable React app under deadline.",
                    "Refactored Python backend reducing latency by 40%.",
                    "Mentored 3 junior devs to promotion."
                ]
            }),
            "Resume Auditor": json.dumps({
                "gaps_filled": [
                     {
                         "role": "Career Break: Technical Upskilling",
                         "company": "Self-Directed Learning",
                         "dates": "2023-01 - 2023-06",
                         "bullets": ["Completed Advanced Python Certification.", "Built full-stack portfolio project."]
                     }
                ],
                "selected_links": ["github.com/jdoe"]
            }),
            "Design Consultant": json.dumps({
                "file_name": "John_Doe_Senior_Full_Stack_Engineer_StartupInc.pdf",
                "formatting_advice": {
                    "font": "Sans-Serif (e.g., Roboto or Open Sans) for modern vibe.",
                    "accent_color": "#0056b3 (Deep Blue)",
                    "layout_note": "Clean, ample white space."
                }
            }),
            "Rewrite the Professional Summary": "Senior Full Stack Engineer (Python/React) with 5 years experience. Expert in Python and React. Proven track record of architecting scalable systems and refactoring legacy code in fast-paced startup environments.",
            "tailor a specific job entry": json.dumps([
                "**Orchestrated cross-functional collaboration** to build a react app, matching startup speed.",
                "Optimized database queries, solving complex performance bottlenecks.",
                "Managed a team of 3, mentoring junior engineers."
            ]),
            "optimizing the \"Skills\" section": json.dumps(["Python", "React", "PostgreSQL", "AWS", "CI/CD", "Git", "SQL"]),
            "Hiring Manager": json.dumps({
                "six_second_test": {"result": "Pass", "comment": "Headline and top achievements are immediately visible."},
                "so_what_test": {"result": "Pass", "comment": "Bullets clearly address the pain point of legacy code."},
                "missing_keywords": [],
                "final_verdict": "Ready to Submit"
            }),
            "Senior Editor fixing a resume": json.dumps({
                "summary": "Revised Summary with more keywords.",
                "experience": [],
                "skills": []
            }),
            "career coach writing a cover letter": "Dear Hiring Manager,\n\nI am writing to express my interest in the Senior Full Stack Engineer role..."
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

def get_llm(config: Config = None):
    """返回配置好的 LLM 实例，如果没有密钥则返回 Mock。"""
    # 优先使用 config 对象，如果未提供则使用默认环境变量检查
    api_key = config.openai_api_key if config else os.environ.get("OPENAI_API_KEY")

    if api_key:
        model = config.model if config else "gpt-4o"
        return ChatOpenAI(model=model, temperature=0, api_key=api_key)
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
            return "Mock search results: Company values are Innovation and Speed. Interview questions focus on System Design."
        return Tool(name="search", func=mock_search, description="Search the web.")
