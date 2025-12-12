from langgraph.graph import StateGraph, END
from .state import ResumeTailorState
from .nodes import analyze_job_posting, research_company, tailor_resume

def create_resume_tailor_graph():
    workflow = StateGraph(ResumeTailorState)

    # 添加节点
    workflow.add_node("analyze_jd", analyze_job_posting)
    workflow.add_node("research_company", research_company)
    workflow.add_node("tailor_resume", tailor_resume)

    # 添加边
    workflow.set_entry_point("analyze_jd")
    workflow.add_edge("analyze_jd", "research_company")
    workflow.add_edge("research_company", "tailor_resume")
    workflow.add_edge("tailor_resume", END)

    return workflow.compile()
