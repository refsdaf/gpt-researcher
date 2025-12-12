import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.language_models import FakeListLLM
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableSerializable, Runnable
from langchain_core.tools import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Any, List, Optional

class MockChatModel(RunnableSerializable):
    """A mock chat model that returns context-aware responses."""

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
        # Determine which prompt is being used by checking the input text
        text = str(input)

        response_content = "Mock response"
        for key, val in self.responses.items():
            if key in text or key in str(input):
                response_content = val
                break

        return AIMessage(content=response_content)

def get_llm():
    """Returns a configured LLM instance or a Mock if no key."""
    if os.environ.get("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o", temperature=0)
    else:
        print("NOTICE: OPENAI_API_KEY not found. Using Mock LLM.")
        return MockChatModel()

def get_search_tool():
    """Returns a search tool if available, else a mock."""
    if os.environ.get("TAVILY_API_KEY"):
        return TavilySearchResults()
    else:
        # Mock tool for testing without API key
        def mock_search(query: str):
            return "Mock search results: Company values are Innovation and Speed."
        return Tool(name="search", func=mock_search, description="Search the web.")
