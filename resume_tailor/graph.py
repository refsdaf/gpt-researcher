from langgraph.graph import StateGraph, END
from .state import ResumeTailorState
from .nodes import (
    analyze_job_posting,
    research_company,
    strategize,
    process_gaps_and_links,
    advise_formatting,
    tailor_header_summary,
    tailor_experience,
    tailor_skills,
    reorder_sections,
    review_resume
)

def create_resume_tailor_graph():
    workflow = StateGraph(ResumeTailorState)

    # 添加节点
    workflow.add_node("analyze_jd", analyze_job_posting)
    workflow.add_node("research_company", research_company)
    workflow.add_node("strategize", strategize)
    workflow.add_node("process_gaps_and_links", process_gaps_and_links)
    workflow.add_node("tailor_header_summary", tailor_header_summary)
    workflow.add_node("tailor_experience", tailor_experience)
    workflow.add_node("tailor_skills", tailor_skills)
    workflow.add_node("reorder_sections", reorder_sections)
    workflow.add_node("advise_formatting", advise_formatting) # 并行或串行
    workflow.add_node("review_resume", review_resume)

    # 添加边 (顺序工作流)
    workflow.set_entry_point("analyze_jd")
    workflow.add_edge("analyze_jd", "research_company")
    workflow.add_edge("research_company", "strategize")
    workflow.add_edge("strategize", "process_gaps_and_links")
    workflow.add_edge("process_gaps_and_links", "tailor_header_summary")
    workflow.add_edge("tailor_header_summary", "tailor_experience")
    workflow.add_edge("tailor_experience", "tailor_skills")
    workflow.add_edge("tailor_skills", "reorder_sections")
    workflow.add_edge("reorder_sections", "advise_formatting")
    workflow.add_edge("advise_formatting", "review_resume")
    workflow.add_edge("review_resume", END)

    return workflow.compile()
