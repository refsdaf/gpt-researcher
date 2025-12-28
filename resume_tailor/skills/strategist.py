from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from ..state import ResumeTailorState
from ..prompts import (
    ANALYZE_JD_PROMPT,
    STRATEGIC_ASSESSMENT_PROMPT,
    GAP_AND_LINK_ANALYSIS_PROMPT
)

class StrategistSkill:
    """负责分析、规划和战略评估的技能。"""

    def __init__(self, llm):
        self.llm = llm

    def analyze_jd(self, jd_text: str) -> dict:
        """分析 JD 提取关键词和痛点。"""
        print("--- [Skill] Analyzing Job Description ---")
        prompt = ChatPromptTemplate.from_template(ANALYZE_JD_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()
        return chain.invoke({"job_description": jd_text})

    def strategize(self, resume: dict, analysis: dict) -> dict:
        """制定简历结构和关键成就。"""
        print("--- [Skill] Developing Strategy ---")
        # 提取简要上下文
        exp_overview = []
        if "experience" in resume:
            for job in resume["experience"][:2]:
                exp_overview.append(f"{job.get('role')} at {job.get('company')}")

        prompt = ChatPromptTemplate.from_template(STRATEGIC_ASSESSMENT_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()

        strategy = chain.invoke({
            "analysis": json.dumps(analysis),
            "current_summary": resume.get("summary", ""),
            "experience_overview": "; ".join(exp_overview)
        })
        return strategy

    def analyze_gaps_and_links(self, resume: dict, keywords: str) -> dict:
        """分析空白期和筛选链接。"""
        print("--- [Skill] Analyzing Gaps & Links ---")
        prompt = ChatPromptTemplate.from_template(GAP_AND_LINK_ANALYSIS_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()

        return chain.invoke({
            "experience": json.dumps(resume.get("experience", [])),
            "links": json.dumps(resume.get("links", [])),
            "keywords": keywords
        })
