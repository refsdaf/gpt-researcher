from ..utils import get_search_tool

class ResearcherSkill:
    """负责外部信息搜集的技能。"""

    def __init__(self):
        self.search_tool = get_search_tool()

    def deep_research(self, jd_text: str) -> str:
        """执行深度的公司和职位研究。"""
        print("--- [Skill] Conducting Deep Research ---")
        jd_preview = jd_text[:100]

        # 1. 文化
        culture_query = f"Company culture and values for job description: {jd_preview}..."
        culture_res = self.search_tool.run(culture_query)

        # 2. 面试/痛点
        interview_query = f"Common interview questions and challenges for {jd_preview} role..."
        interview_res = self.search_tool.run(interview_query)

        # 3. 新闻
        news_query = f"Recent engineering blog posts or news for {jd_preview} company..."
        news_res = self.search_tool.run(news_query)

        return f"Culture: {culture_res}\nInterview/Pain Points: {interview_res}\nNews: {news_res}"
