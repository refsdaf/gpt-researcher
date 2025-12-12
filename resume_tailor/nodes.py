import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .state import ResumeTailorState
from .prompts import (
    ANALYZE_JD_PROMPT,
    STRATEGIC_ASSESSMENT_PROMPT,
    GAP_AND_LINK_ANALYSIS_PROMPT,
    FORMATTING_ADVICE_PROMPT,
    TAILOR_SUMMARY_PROMPT,
    TAILOR_EXPERIENCE_PROMPT,
    TAILOR_SKILLS_PROMPT,
    QUALITY_REVIEW_PROMPT
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
    """深入搜索公司文化、面试题和新闻 (Phase 1 Enhanced)。"""
    print("--- Deep Research Phase ---")
    search = get_search_tool()
    jd_preview = state['job_description'][:100]

    # 1. 搜索文化
    culture_query = f"Company culture and values for job description: {jd_preview}..."
    culture_res = search.run(culture_query)

    # 2. 搜索面试题/痛点
    interview_query = f"Common interview questions and challenges for {jd_preview} role..."
    interview_res = search.run(interview_query)

    # 3. 搜索最近新闻/博客
    news_query = f"Recent engineering blog posts or news for {jd_preview} company..."
    news_res = search.run(news_query)

    combined_research = f"Culture: {culture_res}\nInterview/Pain Points: {interview_res}\nNews: {news_res}"

    return {"company_research": combined_research}

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

def process_gaps_and_links(state: ResumeTailorState) -> dict:
    """处理职业空白期和链接选择 (Phase 4)。"""
    print("--- Gap & Link Analysis ---")
    resume = state["resume_data"]
    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    prompt = ChatPromptTemplate.from_template(GAP_AND_LINK_ANALYSIS_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    # 简单的提取用于提示
    exp_context = json.dumps(resume.get("experience", []))
    links_context = json.dumps(resume.get("links", [])) # 假设原始数据可能有 links

    result = chain.invoke({
        "experience": exp_context,
        "links": links_context,
        "keywords": keywords
    })

    return {"gap_analysis": result.get("gaps_filled", [])}

def advise_formatting(state: ResumeTailorState) -> dict:
    """生成格式和文件名建议 (Phase 4)。"""
    print("--- Formatting Advice ---")
    resume = state["resume_data"]
    analysis = state["analysis"]
    target_title = state.get("target_title", "Professional")

    prompt = ChatPromptTemplate.from_template(FORMATTING_ADVICE_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    advice = chain.invoke({
        "name": resume.get("name", "Candidate"), # 假设有名字
        "role": target_title,
        "company": "Target Company", # 理想情况下从 JD 提取
        "culture": analysis.get("culture", "") + " " + analysis.get("brand_vibe", "")
    })

    return {
        "file_name": advice.get("file_name", "resume.pdf"),
        "formatting_advice": advice.get("formatting_advice", {})
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

    current_tailored = state.get("tailored_resume_data") or resume.copy()
    current_tailored["summary"] = new_summary_resp.content

    return {"tailored_resume_data": current_tailored}

def tailor_experience(state: ResumeTailorState) -> dict:
    """定制工作经历并注入填补空白期的条目 (Phase 3B & 4)。"""
    print("--- Tailoring Experience ---")
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    analysis = state["analysis"]
    config = state.get("config", {})
    gaps_filled = state.get("gap_analysis", []) # 从上一步获取的填补条目
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    if "experience" in current_tailored:
        tailored_experience = []
        exp_prompt = ChatPromptTemplate.from_template(TAILOR_EXPERIENCE_PROMPT)
        exp_chain = exp_prompt | llm | JsonOutputParser()

        # 1. 处理现有工作
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

        # 2. 注入空白期填补条目 (简化处理：添加到末尾，或者如果有日期逻辑应该排序)
        # 这里为了演示，我们假设 gaps_filled 是结构化的 experience item
        if gaps_filled:
            print(f"Injecting {len(gaps_filled)} gap filling entries.")
            tailored_experience.extend(gaps_filled)

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

    current_tailored["headline_target_title"] = target_title

    final_ordered_resume = {}
    if "headline_target_title" in current_tailored:
        final_ordered_resume["headline_target_title"] = current_tailored["headline_target_title"]

    for section in section_order:
        if section in current_tailored:
            final_ordered_resume[section] = current_tailored[section]
            if section == "summary" and key_achievements:
                 final_ordered_resume["key_achievements"] = key_achievements

    for k, v in current_tailored.items():
        if k not in final_ordered_resume and k != "key_achievements":
            final_ordered_resume[k] = v

    return {"tailored_resume_data": final_ordered_resume}

def review_resume(state: ResumeTailorState) -> dict:
    """执行最终质量审查 (Phase 6)。"""
    print("--- Quality Assurance Phase ---")
    resume = state["tailored_resume_data"]
    analysis = state["analysis"]

    # 提取用于审查的关键部分
    summary = resume.get("summary", "")
    headline = resume.get("headline_target_title", "")

    # 获取前几个 bullets 作为样本
    top_bullets = []
    if "experience" in resume and resume["experience"]:
        top_bullets = resume["experience"][0].get("bullets", [])[:3]

    prompt = ChatPromptTemplate.from_template(QUALITY_REVIEW_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    report = chain.invoke({
        "keywords": f"{analysis.get('hard_skills', [])}",
        "pain_points": analysis.get("pain_points", ""),
        "headline": headline,
        "summary": summary,
        "top_bullets": top_bullets
    })

    return {"quality_report": report}
