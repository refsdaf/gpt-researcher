from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from ..prompts import (
    FORMATTING_ADVICE_PROMPT,
    QUALITY_REVIEW_PROMPT,
    REVISION_PROMPT
)

class ReviewerSkill:
    """负责格式建议、质量审查和修正的技能。"""

    def __init__(self, llm):
        self.llm = llm

    def advise_formatting(self, name: str, role: str, company: str, culture: str) -> dict:
        """提供格式建议。"""
        print("--- [Skill] Advising Formatting ---")
        prompt = ChatPromptTemplate.from_template(FORMATTING_ADVICE_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()
        return chain.invoke({
            "name": name,
            "role": role,
            "company": company,
            "culture": culture
        })

    def review_resume(self, resume: dict, keywords: str, pain_points: str) -> dict:
        """执行质量审查 (6秒测试 & So What 测试)。"""
        print("--- [Skill] Reviewing Resume ---")
        top_bullets = []
        if "experience" in resume and resume["experience"]:
            top_bullets = resume["experience"][0].get("bullets", [])[:3]

        prompt = ChatPromptTemplate.from_template(QUALITY_REVIEW_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()

        return chain.invoke({
            "keywords": keywords,
            "pain_points": pain_points,
            "headline": resume.get("headline_target_title", ""),
            "summary": resume.get("summary", ""),
            "top_bullets": top_bullets
        })

    def revise_resume(self, resume: dict, report: dict) -> dict:
        """根据报告修正简历。"""
        print("--- [Skill] Revising Resume ---")
        prompt = ChatPromptTemplate.from_template(REVISION_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()

        return chain.invoke({
            "quality_report": json.dumps(report),
            "resume_data": json.dumps(resume)
        })
