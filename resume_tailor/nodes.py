import json
from .state import ResumeTailorState
from .utils import get_llm
from .config import Config
from .skills.strategist import StrategistSkill
from .skills.researcher import ResearcherSkill
from .skills.tailor import TailorSkill
from .skills.reviewer import ReviewerSkill

# 初始化全局配置和 LLM
# 在实际应用中，可能会使用依赖注入或在 Graph Context 中传递
config = Config()
llm = get_llm(config)

# 初始化技能模块
strategist = StrategistSkill(llm)
researcher = ResearcherSkill()
tailor = TailorSkill(llm)
reviewer = ReviewerSkill(llm)

def analyze_job_posting(state: ResumeTailorState) -> dict:
    """分析职位描述以提取特定的目标信息 (Phase 1)。"""
    return {"analysis": strategist.analyze_jd(state["job_description"])}

def research_company(state: ResumeTailorState) -> dict:
    """深入搜索公司文化、面试题和新闻 (Phase 1 Enhanced)。"""
    return {"company_research": researcher.deep_research(state["job_description"])}

def strategize(state: ResumeTailorState) -> dict:
    """战略评估：确定标题、章节顺序和关键成就 (Phase 2)。"""
    strategy = strategist.strategize(state["resume_data"], state["analysis"])
    return {
        "target_title": strategy.get("target_title", "Professional"),
        "section_order": strategy.get("section_order", ["summary", "experience", "skills", "education"]),
        "key_achievements": strategy.get("key_achievements", [])
    }

def process_gaps_and_links(state: ResumeTailorState) -> dict:
    """处理职业空白期和链接选择 (Phase 4)。"""
    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"
    result = strategist.analyze_gaps_and_links(state["resume_data"], keywords)
    return {"gap_analysis": result.get("gaps_filled", [])}

def advise_formatting(state: ResumeTailorState) -> dict:
    """生成格式和文件名建议 (Phase 4)。"""
    resume = state["resume_data"]
    analysis = state["analysis"]
    target_title = state.get("target_title", "Professional")
    culture = analysis.get("culture", "") + " " + analysis.get("brand_vibe", "")

    advice = reviewer.advise_formatting(
        resume.get("name", "Candidate"),
        target_title,
        "Target Company",
        culture
    )
    return {
        "file_name": advice.get("file_name", "resume.pdf"),
        "formatting_advice": advice.get("formatting_advice", {})
    }

def tailor_header_summary(state: ResumeTailorState) -> dict:
    """定制摘要和头部信息 (Phase 3A & 2.1)。"""
    resume = state["resume_data"]
    if "summary" not in resume:
        return {}

    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"
    culture_context = state.get("company_research", "")
    full_culture = f"{analysis.get('culture', '')}. External Research: {culture_context}"

    new_summary = tailor.tailor_summary(
        resume["summary"],
        state.get("target_title", "Professional"),
        keywords,
        analysis.get("pain_points", ""),
        full_culture
    )

    current_tailored = state.get("tailored_resume_data") or resume.copy()
    current_tailored["summary"] = new_summary
    return {"tailored_resume_data": current_tailored}

def tailor_experience(state: ResumeTailorState) -> dict:
    """定制工作经历并注入填补空白期的条目 (Phase 3B & 4)。"""
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    # 获取运行时配置或默认配置
    run_config = state.get("config", {})

    if "experience" in current_tailored:
        tailored_list = tailor.tailor_experience(
            current_tailored["experience"],
            keywords,
            analysis.get("pain_points", ""),
            run_config
        )

        # 注入空白期
        gaps_filled = state.get("gap_analysis", [])
        if gaps_filled:
            tailored_list.extend(gaps_filled)

        current_tailored["experience"] = tailored_list

    return {"tailored_resume_data": current_tailored}

def tailor_skills(state: ResumeTailorState) -> dict:
    """定制技能部分 (Phase 3C)。"""
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

    if "skills" in current_tailored:
        current_tailored["skills"] = tailor.tailor_skills(
            current_tailored["skills"],
            keywords
        )

    return {"tailored_resume_data": current_tailored}

def reorder_sections(state: ResumeTailorState) -> dict:
    """重新排序章节并插入关键成就 (Phase 2)。"""
    current_tailored = state.get("tailored_resume_data") or state["resume_data"].copy()
    section_order = state.get("section_order", [])
    key_achievements = state.get("key_achievements", [])

    current_tailored["headline_target_title"] = state.get("target_title", "")

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
    analysis = state["analysis"]
    keywords = f"{analysis.get('hard_skills', [])}"
    return {"quality_report": reviewer.review_resume(
        state["tailored_resume_data"],
        keywords,
        analysis.get("pain_points", "")
    )}

def revise_resume(state: ResumeTailorState) -> dict:
    """根据审查反馈修正简历 (Phase 6 Iteration)。"""
    updated_resume = reviewer.revise_resume(
        state["tailored_resume_data"],
        state["quality_report"]
    )
    return {
        "tailored_resume_data": updated_resume,
        "revision_count": state.get("revision_count", 0) + 1
    }

def write_cover_letter(state: ResumeTailorState) -> dict:
    """生成求职信 (Phase 7)。"""
    resume = state["tailored_resume_data"]
    culture_context = state.get("company_research", "")

    letter = tailor.write_cover_letter(
        resume.get("name", "Candidate"),
        state.get("target_title", "Professional"),
        "Target Company",
        culture_context,
        resume.get("summary", ""),
        state.get("key_achievements", [])
    )

    return {"cover_letter": letter}

def should_revise(state: ResumeTailorState) -> str:
    """条件边：决定是修正还是继续。"""
    report = state.get("quality_report", {})
    count = state.get("revision_count", 0)
    max_revisions = 1

    if report.get("final_verdict") == "Needs Revision" and count < max_revisions:
        print(f"Verdict: Needs Revision. Attempt {count + 1}")
        return "revise"

    print("Verdict: Ready or Max Revisions Reached.")
    return "finalize"
