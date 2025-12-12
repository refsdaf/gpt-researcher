import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .state import ResumeTailorState
from .prompts import (
    ANALYZE_JD_PROMPT,
    TAILOR_SUMMARY_PROMPT,
    TAILOR_EXPERIENCE_PROMPT,
    TAILOR_SKILLS_PROMPT
)
from .utils import get_llm, get_search_tool

llm = get_llm()

def analyze_job_posting(state: ResumeTailorState) -> dict:
    """分析职位描述以提取特定的目标信息。"""
    print("--- Analysis Phase ---")
    jd = state["job_description"]

    prompt = ChatPromptTemplate.from_template(ANALYZE_JD_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    analysis = chain.invoke({"job_description": jd})
    return {"analysis": analysis}

def research_company(state: ResumeTailorState) -> dict:
    """如果职位描述中包含公司名称，则搜索公司文化/价值观。"""
    print("--- Research Phase ---")
    # 这是一个简化版本。真正的代理可能会首先提取公司名称。
    # 如果没有显式传递名称，我们只需搜索“公司文化”+ JD 标题的前几个词，
    # 或者依赖于前一步骤的提取结果（如果我们修改状态以保存公司名称）。

    # 目前，我们假设 JD 可能包含公司名称，或者我们仅根据上下文进行广泛搜索。
    # 但通常情况下，用户会提供公司名称，或者名称就在文本中。

    search = get_search_tool()
    query = f"Company culture and values for job description: {state['job_description'][:100]}..."
    results = search.run(query)

    return {"company_research": str(results)}

def tailor_resume(state: ResumeTailorState) -> dict:
    """主要的执行节点。遍历简历的各个部分。"""
    print("--- Tailoring Phase ---")
    resume = state["resume_data"]
    analysis = state["analysis"]
    culture_context = state.get("company_research", "")
    config = state.get("config", {})

    tailored_resume = resume.copy()

    # 1. 定制摘要
    if "summary" in resume:
        summary_prompt = ChatPromptTemplate.from_template(TAILOR_SUMMARY_PROMPT)
        summary_chain = summary_prompt | llm

        # 为提示词准备上下文
        keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

        new_summary = summary_chain.invoke({
            "current_summary": resume["summary"],
            "target_title": analysis.get("key_responsibilities", "Target Role"), # 简化
            "keywords": keywords,
            "pain_points": analysis.get("pain_points", ""),
            "culture": f"{analysis.get('culture', '')}. External Research: {culture_context}"
        })
        tailored_resume["summary"] = new_summary.content

    # 2. 定制工作经历
    if "experience" in resume:
        tailored_experience = []
        exp_prompt = ChatPromptTemplate.from_template(TAILOR_EXPERIENCE_PROMPT)
        exp_chain = exp_prompt | llm | JsonOutputParser() # 期望返回字符串列表

        for job in resume["experience"]:
            # 期望 job 包含 'role', 'company', 'bullets' (列表)
            try:
                # 处理 bullets 可能是字符串或列表的情况
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
                tailored_experience.append(job) # 回退到原始数据

        tailored_resume["experience"] = tailored_experience

    # 3. 定制技能
    if "skills" in resume:
        skills_prompt = ChatPromptTemplate.from_template(TAILOR_SKILLS_PROMPT)
        skills_chain = skills_prompt | llm

        # 确定当前的技能格式（列表或字典）
        current_skills = resume["skills"]
        new_skills_resp = skills_chain.invoke({
            "current_skills": current_skills,
            "keywords": keywords
        })

        # 我们目前只获取文本输出，假设提示词能很好地指导输出。
        # 理想情况下，我们应该将其解析回原始结构。
        # 对于这个概念验证，我们将其存储为字符串，或者如果它是 JSON 则尝试解析。
        try:
            tailored_resume["skills"] = json.loads(new_skills_resp.content)
        except:
            tailored_resume["skills"] = new_skills_resp.content.split("\n")

    return {"tailored_resume_data": tailored_resume}

def format_resume(state: ResumeTailorState) -> dict:
    """最终输出生成（可选）。"""
    # 在完整的应用程序中，这可能会生成 PDF 或 Markdown 字符串。
    # 目前，我们依赖结构化数据作为结果。
    return {}
