from typing import TypedDict, List, Dict, Optional, Any

class ResumeTailorState(TypedDict):
    resume_data: Dict[str, Any]  # 结构化的简历输入
    job_description: str         # 职位描述文本
    analysis: Dict[str, Any]     # 分析 JD 的结果（关键词、文化等）
    company_research: str        # 关于公司的上下文研究（深度：文化、面试题、新闻）

    # 战略规划 (Phase 2)
    target_title: str            # 目标职位名称 (Headline)
    section_order: List[str]     # 简历章节顺序 (e.g., ["summary", "skills", "experience"])
    key_achievements: List[str]  # 选定的关键成就 (Highlights Section)

    # 高级/隐形定制 (Phase 4)
    file_name: str               # 建议的文件名 (e.g., Name_Role_Company.pdf)
    formatting_advice: Dict[str, str] # 格式建议 (字体、颜色、布局)
    gap_analysis: List[Dict[str, Any]] # 职业空白期分析及“技能提升”条目建议

    tailoring_strategy: str      # 代理生成的文本计划 (可选)
    tailored_resume_data: Dict[str, Any] # 最终的结构化简历

    # 质量保证 (Phase 6)
    quality_report: Dict[str, Any] # "6秒测试"和"So What"测试结果

    config: Dict[str, Any]       # 配置（删除无关内容、夸大等）
