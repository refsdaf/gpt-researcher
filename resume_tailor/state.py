from typing import TypedDict, List, Dict, Optional, Any

class ResumeTailorState(TypedDict):
    resume_data: Dict[str, Any]  # 结构化的简历输入
    job_description: str         # 职位描述文本
    analysis: Dict[str, Any]     # 分析 JD 的结果（关键词、文化等）
    company_research: str        # 关于公司的上下文研究
    tailoring_strategy: str      # 代理生成的计划
    tailored_resume_data: Dict[str, Any] # 最终的结构化简历
    config: Dict[str, Any]       # 配置（删除无关内容、夸大等）
