from langgraph.graph import StateGraph, END
from .state import ResumeTailorState
from .nodes import (
    analyze_job_posting,
    research_company,
    strategize,
    tailor_header_summary,
    tailor_experience,
    tailor_skills,
    reorder_sections
)

def create_resume_tailor_graph():
    workflow = StateGraph(ResumeTailorState)

    # 添加节点
    workflow.add_node("analyze_jd", analyze_job_posting)
    workflow.add_node("research_company", research_company)
    workflow.add_node("strategize", strategize)
    workflow.add_node("tailor_header_summary", tailor_header_summary)
    workflow.add_node("tailor_experience", tailor_experience)
    workflow.add_node("tailor_skills", tailor_skills)
    workflow.add_node("reorder_sections", reorder_sections)

    # 添加边 (定义顺序工作流)
    workflow.set_entry_point("analyze_jd")
    workflow.add_edge("analyze_jd", "research_company")
    workflow.add_edge("research_company", "strategize")
    workflow.add_edge("strategize", "tailor_header_summary")
    workflow.add_edge("tailor_header_summary", "tailor_experience")
    workflow.add_edge("tailor_experience", "tailor_skills")
    workflow.add_edge("tailor_skills", "reorder_sections")
    workflow.add_edge("reorder_sections", END)

    return workflow.compile()
