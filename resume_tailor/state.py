from typing import TypedDict, List, Dict, Optional, Any

class ResumeTailorState(TypedDict):
    resume_data: Dict[str, Any]  # 结构化的简历输入
    job_description: str         # 职位描述文本
    analysis: Dict[str, Any]     # 分析 JD 的结果（关键词、文化等）
    company_research: str        # 关于公司的上下文研究

    # 战略规划 (Phase 2)
    target_title: str            # 目标职位名称 (Headline)
    section_order: List[str]     # 简历章节顺序 (e.g., ["summary", "skills", "experience"])
    key_achievements: List[str]  # 选定的关键成就 (Highlights Section)

    tailoring_strategy: str      # 代理生成的文本计划 (可选)
    tailored_resume_data: Dict[str, Any] # 最终的结构化简历
    config: Dict[str, Any]       # 配置（删除无关内容、夸大等）
