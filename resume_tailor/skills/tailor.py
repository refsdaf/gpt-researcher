from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from ..prompts import (
    TAILOR_SUMMARY_PROMPT,
    TAILOR_EXPERIENCE_PROMPT,
    TAILOR_SKILLS_PROMPT,
    COVER_LETTER_PROMPT
)

class TailorSkill:
    """负责具体的文本重写和定制的技能。"""

    def __init__(self, llm):
        self.llm = llm

    def tailor_summary(self, summary: str, target_title: str, keywords: str, pain_points: str, culture: str) -> str:
        """重写摘要。"""
        print("--- [Skill] Tailoring Summary ---")
        prompt = ChatPromptTemplate.from_template(TAILOR_SUMMARY_PROMPT)
        chain = prompt | self.llm
        result = chain.invoke({
            "current_summary": summary,
            "target_title": target_title,
            "keywords": keywords,
            "pain_points": pain_points,
            "culture": culture
        })
        return result.content

    def tailor_experience(self, experience_list: list, keywords: str, pain_points: str, config: dict) -> list:
        """重写工作经历。"""
        print("--- [Skill] Tailoring Experience ---")
        prompt = ChatPromptTemplate.from_template(TAILOR_EXPERIENCE_PROMPT)
        chain = prompt | self.llm | JsonOutputParser()

        tailored_list = []
        for job in experience_list:
            try:
                current_bullets = job.get("bullets", [])
                if isinstance(current_bullets, str):
                    current_bullets = [current_bullets]

                new_bullets = chain.invoke({
                    "role": job.get("role", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "current_bullets": current_bullets,
                    "keywords": keywords,
                    "pain_points": pain_points,
                    "remove_irrelevant": config.get("remove_irrelevant", False),
                    "exaggerate": config.get("exaggerate", False),
                    "style_mode": config.get("style_mode", "standard")
                })

                job_copy = job.copy()
                job_copy["bullets"] = new_bullets
                tailored_list.append(job_copy)
            except Exception as e:
                print(f"Error tailoring job {job.get('role')}: {e}")
                tailored_list.append(job)
        return tailored_list

    def tailor_skills(self, current_skills: list, keywords: str) -> list:
        """重写技能部分。"""
        print("--- [Skill] Tailoring Skills ---")
        prompt = ChatPromptTemplate.from_template(TAILOR_SKILLS_PROMPT)
        chain = prompt | self.llm

        resp = chain.invoke({
            "current_skills": current_skills,
            "keywords": keywords
        })

        try:
            return json.loads(resp.content)
        except:
            return resp.content.split("\n")

    def write_cover_letter(self, name: str, role: str, company: str, culture: str, summary: str, achievements: list) -> str:
        """撰写求职信。"""
        print("--- [Skill] Writing Cover Letter ---")
        prompt = ChatPromptTemplate.from_template(COVER_LETTER_PROMPT)
        chain = prompt | self.llm

        resp = chain.invoke({
            "name": name,
            "role": role,
            "company": company,
            "culture_context": culture,
            "summary": summary,
            "key_achievements": "\n- ".join(achievements)
        })
        return resp.content
