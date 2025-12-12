import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .state import ResumeTailorState
from .prompts import (
    ANALYZE_JD_PROMPT,
    STRATEGIC_ASSESSMENT_PROMPT,
    TAILOR_SUMMARY_PROMPT,
    TAILOR_EXPERIENCE_PROMPT,
    TAILOR_SKILLS_PROMPT
)
from .utils import get_llm, get_search_tool

llm = get_llm()

def analyze_job_posting(state: ResumeTailorState) -> dict:
    """分析职位描述以提取特定的目标信息 (Phase 1)。"""
    print("--- Analysis Phase ---")
    jd = state["job_description"]

    prompt = ChatPromptTemplate.from_template(ANALYZE_JD_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    analysis = chain.invoke({"job_description": jd})
    return {"analysis": analysis}

def research_company(state: ResumeTailorState) -> dict:
    """搜索公司文化/价值观 (Phase 1)。"""
    print("--- Research Phase ---")
    search = get_search_tool()
    query = f"Company culture and values for job description: {state['job_description'][:100]}..."
    results = search.run(query)
    return {"company_research": str(results)}

def strategize(state: ResumeTailorState) -> dict:
    """战略评估：确定标题、章节顺序和关键成就 (Phase 2)。"""
    print("--- Strategic Planning Phase ---")
    resume = state["resume_data"]
    analysis = state["analysis"]

    # 提取一些简要的简历上下文用于规划
    exp_overview = []
    if "experience" in resume:
        for job in resume["experience"][:2]: # 只看最近的两份工作
            exp_overview.append(f"{job.get('role')} at {job.get('company')}")

    prompt = ChatPromptTemplate.from_template(STRATEGIC_ASSESSMENT_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    strategy = chain.invoke({
        "analysis": json.dumps(analysis),
        "current_summary": resume.get("summary", ""),
        "experience_overview": "; ".join(exp_overview)
    })

    return {
        "target_title": strategy.get("target_title", "Professional"),
        "section_order": strategy.get("section_order", ["summary", "experience", "skills", "education"]),
        "key_achievements": strategy.get("key_achievements", [])
    }

def tailor_header_summary(state: ResumeTailorState) -> dict:
    """定制摘要和头部信息 (Phase 3A & 2.1)。"""
    print("--- Tailoring Summary ---")
    resume = state["resume_data"]
    analysis = state["analysis"]
    target_title = state.get("target_title", "Professional")
    culture_context = state.get("company_research", "")

    if "summary" not in resume:
        return {}

    prompt = ChatPromptTemplate.from_template(TAILOR_SUMMARY_PROMPT)
    chain = prompt | llm

    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    new_summary_resp = chain.invoke({
        "current_summary": resume["summary"],
        "target_title": target_title,
        "keywords": keywords,
        "pain_points": analysis.get("pain_points", ""),
        "culture": f"{analysis.get('culture', '')}. External Research: {culture_context}"
    })

    # 我们将把更新后的摘要暂时存储在 tailored_resume_data 中
    # 注意：这是一个累积更新过程，我们需要确保 tailored_resume_data 已初始化
    current_tailored = state.get("tailored_resume_data") or resume.copy()
    current_tailored["summary"] = new_summary_resp.content

    return {"tailored_resume_data": current_tailored}

def tailor_experience(state: ResumeTailorState) -> dict:
    """定制工作经历 (Phase 3B)。"""
    print("--- Tailoring Experience ---")
    # 获取当前的 tailored 数据（包含更新后的摘要），如果为空则从原始数据开始
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    analysis = state["analysis"]
    config = state.get("config", {})
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    if "experience" in current_tailored:
        tailored_experience = []
        exp_prompt = ChatPromptTemplate.from_template(TAILOR_EXPERIENCE_PROMPT)
        exp_chain = exp_prompt | llm | JsonOutputParser()

        for job in current_tailored["experience"]:
            try:
                current_bullets = job.get("bullets", [])
                if isinstance(current_bullets, str):
                    current_bullets = [current_bullets]

                new_bullets = exp_chain.invoke({
                    "role": job.get("role", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "current_bullets": current_bullets,
                    "keywords": keywords,
                    "pain_points": analysis.get("pain_points", ""),
                    "remove_irrelevant": config.get("remove_irrelevant", False),
                    "exaggerate": config.get("exaggerate", False)
                })

                job_copy = job.copy()
                job_copy["bullets"] = new_bullets
                tailored_experience.append(job_copy)
            except Exception as e:
                print(f"Error tailoring job {job.get('role')}: {e}")
                tailored_experience.append(job)

        current_tailored["experience"] = tailored_experience

    return {"tailored_resume_data": current_tailored}

def tailor_skills(state: ResumeTailorState) -> dict:
    """定制技能部分 (Phase 3C)。"""
    print("--- Tailoring Skills ---")
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    if "skills" in current_tailored:
        skills_prompt = ChatPromptTemplate.from_template(TAILOR_SKILLS_PROMPT)
        skills_chain = skills_prompt | llm

        new_skills_resp = skills_chain.invoke({
            "current_skills": current_tailored["skills"],
            "keywords": keywords
        })

        try:
            current_tailored["skills"] = json.loads(new_skills_resp.content)
        except:
            current_tailored["skills"] = new_skills_resp.content.split("\n")

    return {"tailored_resume_data": current_tailored}

def reorder_sections(state: ResumeTailorState) -> dict:
    """重新排序章节并插入关键成就 (Phase 2)。"""
    print("--- Finalizing Structure ---")
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    section_order = state.get("section_order", [])
    key_achievements = state.get("key_achievements", [])
    target_title = state.get("target_title", "")

    # 1. 注入目标职位标题
    current_tailored["headline_target_title"] = target_title

    # 2. 注入关键成就 (Selected Highlights)
    if key_achievements:
        current_tailored["key_achievements"] = key_achievements

    # 3. 重新排序顶级键
    # 我们创建一个新的有序字典
    final_ordered_resume = {}

    # 总是把 headline 放在最前面
    if "headline_target_title" in current_tailored:
        final_ordered_resume["headline_target_title"] = current_tailored["headline_target_title"]

    # 总是把 key_achievements 放在 summary 之后或顶部附近
    # 如果 order 列表里没有 key_achievements，我们手动插入

    for section in section_order:
        if section in current_tailored:
            final_ordered_resume[section] = current_tailored[section]

            # 在 summary 之后插入 achievements
            if section == "summary" and "key_achievements" in current_tailored:
                 final_ordered_resume["key_achievements"] = current_tailored["key_achievements"]

    # 复制任何未在 order 中指定但存在的剩余字段
    for k, v in current_tailored.items():
        if k not in final_ordered_resume and k != "key_achievements":
            final_ordered_resume[k] = v

    return {"tailored_resume_data": final_ordered_resume}
