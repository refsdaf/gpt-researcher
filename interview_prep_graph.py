"""面试经验搜索 Agent

基于 LangGraph 实现的面试准备助手，采用 3 阶段流程：
1. 信息探测阶段：并行搜索公司信息，返回 found 标志
2. 兜底搜索阶段：探测失败时搜索行业通用信息
3. 个性化分析阶段：结合面试经验分析简历

特点：
- 探测-兜底模式：先判断是否有真实信息，再决定是否兜底
- 简历分析后置：在获取面试经验后执行，针对性更强
- 条件触发：公司产品仅在(大公司 OR 有JD)时搜索
- 并发控制：解决并行任务的竞态条件，确保报告在所有任务完成后生成
"""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Sequence

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.types import Send, StreamWriter

# External dependencies (assumed to be available in the environment)
try:
    from app.agent.core.llm import get_deepseek_model, get_qwen_search_model
    from app.agent.graphs.shared.baidu_search import BaiduSearchError, fetch_baidu_search
except ImportError:
    # For testing/mocking purposes if modules are missing
    import sys
    if "app.agent.core.llm" not in sys.modules:
        raise

logger = logging.getLogger(__name__)


# ============================================================
# 状态定义
# ============================================================


class InterviewResearchState(MessagesState, total=False):
    """面试经验搜索 Agent 状态"""

    # === 输入字段 ===
    role_name: str  # 必填：职位名称
    company_name: str | None  # 可选：公司名称
    jd_text: str | None  # 可选：职位描述
    resume_text: str | None  # 可选：用户简历
    is_large_company: bool  # 是否为大公司

    # === 探测结果 ===
    company_interview_found: bool  # 是否找到公司面试经验
    company_salary_found: bool  # 是否找到公司薪资

    # === 搜索结果 ===
    interview_experience: str | None  # 面试经验
    salary_info: str | None  # 薪资待遇
    business_info: str | None  # 工商信息
    role_risk_info: str | None  # 岗位避雷
    company_product: str | None  # 公司产品

    # === 分析结果 ===
    resume_analysis: str | None  # 简历分析（含个性化问题预测）

    # === 输出 ===
    final_report: str | None

    # === 内部控制 ===
    # 使用 reducer 累加完成的任务，用于同步并发节点
    completed_tasks: Annotated[list[str], operator.add]
    # 需要等待的任务列表（在初始化时确定）
    pending_tasks: list[str]


# ============================================================
# 辅助函数
# ============================================================


def _extract_keywords_from_jd(jd_text: str) -> list[str]:
    """从 JD 中提取关键词"""
    import re

    tech_patterns = [
        r"Python|Java|Go|C\+\+|JavaScript|TypeScript|Rust|Kotlin|Swift",
        r"React|Vue|Angular|Django|FastAPI|Spring|Node\.js|Flutter",
        r"MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Kafka",
        r"Docker|Kubernetes|AWS|GCP|Azure|Linux",
        r"机器学习|深度学习|NLP|CV|推荐系统|大模型|LLM",
    ]

    keywords = set()
    for pattern in tech_patterns:
        matches = re.findall(pattern, jd_text, re.IGNORECASE)
        keywords.update(matches)

    words = re.split(r"[\s,，。；;、/\-()（）]+", jd_text)
    for w in words:
        w = w.strip()
        if len(w) >= 2 and w not in keywords:
            keywords.add(w)
            if len(keywords) >= 10:
                break

    return list(keywords)[:8]


def _check_all_tasks_completed(state: InterviewResearchState) -> bool:
    """检查是否所有预期任务都已完成"""
    pending = set(state.get("pending_tasks", []))
    completed = set(state.get("completed_tasks", []))
    return pending.issubset(completed)


# ============================================================
# 第一阶段：信息探测节点
# ============================================================


async def probe_company_interview(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """探测公司面试经验"""
    company_name = state.get("company_name")
    role_name = state.get("role_name", "")

    if not company_name:
        return {
            "company_interview_found": False,
            "interview_experience": None,
        }

    writer({"node": "probe_company_interview", "status": "probing"})

    query = f"{company_name} {role_name} 面试经验 面试题"
    try:
        result = await fetch_baidu_search(
            query,
            site_filter="interview",
            instruction="请总结该公司该岗位的面试流程、常见问题和注意事项。如果找不到相关信息，请直接回复「未找到」三个字。",
        )

        if result and "未找到" not in result and len(result.strip()) > 100:
            logger.info(f"找到 {company_name} 面试经验: {len(result)} 字符")
            return {
                "company_interview_found": True,
                "interview_experience": f"【{company_name} 面试经验】\n{result}",
            }
        else:
            logger.info(f"未找到 {company_name} 面试经验")
            return {"company_interview_found": False, "interview_experience": None}

    except BaiduSearchError as e:
        logger.warning(f"公司面试经验搜索失败: {e}")
        return {"company_interview_found": False, "interview_experience": None}


async def probe_company_salary(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """探测公司薪资"""
    company_name = state.get("company_name")
    role_name = state.get("role_name", "")

    if not company_name:
        return {
            "company_salary_found": False,
            "salary_info": None,
        }

    writer({"node": "probe_company_salary", "status": "probing"})

    query = f"{company_name} {role_name} 薪资待遇 年薪"
    try:
        result = await fetch_baidu_search(
            query,
            site_filter="salary",
            instruction="请总结该公司该岗位的薪资范围和职级待遇。如果找不到相关信息，请直接回复「未找到」三个字。",
        )

        if result and "未找到" not in result and len(result.strip()) > 80:
            logger.info(f"找到 {company_name} 薪资信息: {len(result)} 字符")
            return {
                "company_salary_found": True,
                "salary_info": f"【{company_name} 薪资】\n{result}",
            }
        else:
            logger.info(f"未找到 {company_name} 薪资信息")
            return {"company_salary_found": False, "salary_info": None}

    except BaiduSearchError as e:
        logger.warning(f"公司薪资搜索失败: {e}")
        return {"company_salary_found": False, "salary_info": None}


async def search_business_info(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """工商信息搜索"""
    company_name = state.get("company_name")
    if not company_name:
        return {"completed_tasks": ["business_info"]}

    writer({"node": "search_business_info", "status": "searching"})

    llm = get_qwen_search_model()
    prompt = f"""请搜索 {company_name} 公司的工商信息：
1. 公司成立时间、注册资本
2. 法律诉讼（尤其是劳动纠纷）
3. 经营状态风险

如果是小公司找不到信息，请如实说明。控制在150字以内。"""

    try:
        response = await llm.ainvoke(prompt, config=config)
        content = response.content if hasattr(response, "content") else str(response)
        return {"business_info": content, "completed_tasks": ["business_info"]}
    except Exception as e:
        logger.error(f"工商信息搜索失败: {e}")
        return {"business_info": "工商信息搜索失败", "completed_tasks": ["business_info"]}


async def search_role_risk(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """岗位避雷搜索"""
    company_name = state.get("company_name")
    role_name = state.get("role_name", "")
    if not company_name:
        return {"completed_tasks": ["role_risk"]}

    writer({"node": "search_role_risk", "status": "searching"})

    llm = get_qwen_search_model()
    prompt = f"""请搜索 {company_name} {role_name} 岗位的避雷信息：
1. 员工对该岗位/部门的评价
2. 加班情况、工作强度
3. 是否有卡转正、末位淘汰等风险

如果找不到相关信息，请给出该岗位通用的注意事项。控制在150字以内。"""

    try:
        response = await llm.ainvoke(prompt, config=config)
        content = response.content if hasattr(response, "content") else str(response)
        return {"role_risk_info": content, "completed_tasks": ["role_risk"]}
    except Exception as e:
        logger.error(f"岗位避雷搜索失败: {e}")
        return {"role_risk_info": "岗位避雷搜索失败", "completed_tasks": ["role_risk"]}


async def search_company_product(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """公司产品搜索"""
    company_name = state.get("company_name")
    role_name = state.get("role_name", "")
    jd_text = state.get("jd_text")
    is_large = state.get("is_large_company", False)

    if not company_name or (not is_large and not jd_text):
        return {"completed_tasks": ["company_product"]}

    writer({"node": "search_company_product", "status": "searching"})

    llm = get_qwen_search_model()
    prompt = f"""请搜索 {company_name} 公司的产品信息：
1. 主营业务和核心产品
2. {role_name} 岗位可能负责的产品线
3. 近期业务动态

控制在200字以内。"""

    try:
        response = await llm.ainvoke(prompt, config=config)
        content = response.content if hasattr(response, "content") else str(response)
        return {"company_product": content, "completed_tasks": ["company_product"]}
    except Exception as e:
        logger.error(f"公司产品搜索失败: {e}")
        return {"completed_tasks": ["company_product"]}


# ============================================================
# 第二阶段：兜底搜索节点
# ============================================================


async def fallback_industry_interview(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """行业通用面试经验"""
    role_name = state.get("role_name", "")
    jd_text = state.get("jd_text")

    writer({"node": "fallback_industry_interview", "status": "searching"})

    if jd_text:
        keywords = _extract_keywords_from_jd(jd_text)
        skill_part = " ".join(keywords[:3]) if keywords else ""
        query = f"{role_name} {skill_part} 面试经验 高频问题"
    else:
        query = f"{role_name} 面试经验 高频问题 2024"

    try:
        result = await fetch_baidu_search(
            query,
            site_filter="interview",
            instruction="请总结该岗位的高频面试题和答题技巧，用要点形式输出",
        )

        content = f"【{role_name} 行业面试经验】\n{result}" if result else None
        return {"interview_experience": content}
    except BaiduSearchError as e:
        logger.warning(f"行业面试经验搜索失败: {e}")
        llm = get_qwen_search_model()
        prompt = f"""请搜索 {role_name} 岗位的面试经验：
1. 常见面试流程
2. 5个高频面试题
3. 面试注意事项"""
        try:
            response = await llm.ainvoke(prompt, config=config)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            return {"interview_experience": f"【{role_name} 面试指南】\n{content}"}
        except Exception:
            return {"interview_experience": "面试经验搜索失败"}


async def fallback_industry_salary(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """行业平均薪资"""
    role_name = state.get("role_name", "")

    writer({"node": "fallback_industry_salary", "status": "searching"})

    query = f"{role_name} 平均薪资 薪资水平 2024"
    try:
        result = await fetch_baidu_search(
            query,
            site_filter="salary",
            instruction="请总结该岗位的市场平均薪资范围，按工作年限分层说明",
        )

        if result and len(result.strip()) > 50:
            return {"salary_info": f"【{role_name} 行业薪资】\n{result}"}
    except BaiduSearchError as e:
        logger.warning(f"行业薪资搜索失败: {e}")

    llm = get_qwen_search_model()
    prompt = f"""请搜索 {role_name} 岗位的薪资水平：
1. 不同城市的薪资范围
2. 不同工作年限对应的薪资
3. 谈薪建议
控制在150字以内。"""
    try:
        response = await llm.ainvoke(prompt, config=config)
        content = response.content if hasattr(response, "content") else str(response)
        return {"salary_info": f"【{role_name} 行业薪资】\n{content}"}
    except Exception:
        return {"salary_info": "薪资信息搜索失败"}


# ============================================================
# 第三阶段：个性化分析节点
# ============================================================


async def analyze_resume(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """简历分析节点"""
    resume_text = state.get("resume_text")
    if not resume_text:
        return {"completed_tasks": ["resume_analysis"]}

    # 确保面试经验已经获取（无论是公司还是行业）
    interview_exp = state.get("interview_experience", "")
    role_name = state.get("role_name", "")
    jd_text = state.get("jd_text", "")

    writer({"node": "analyze_resume", "status": "analyzing"})

    llm = get_deepseek_model()

    interview_section = ""
    if interview_exp:
        interview_section = f"""
已知该岗位的面试经验：
{interview_exp[:1500]}
"""

    jd_section = ""
    if jd_text:
        jd_section = f"""
职位描述（JD）：
{jd_text}
"""

    prompt = f"""你是一位资深面试官。请结合面试经验和职位要求，分析这份简历。

目标职位：{role_name}
{jd_section}
{interview_section}
简历内容：
{resume_text}

请输出以下内容（简洁的要点形式）：

## 1. 匹配度评估
- 整体匹配度（高/中/低）
- 主要匹配点和缺口

## 2. 针对你简历的预测问题
根据面试经验中的高频问题，结合你的简历经历，预测面试官最可能问你的 5 个问题：
（例如：你简历提到了 XX 项目，面试官可能会问 XX）

## 3. 弱点应对
识别简历中的潜在问题（空窗期、跳槽频繁等），给出应对话术

## 4. 自我介绍建议
给出 30 秒自我介绍模板，强调与岗位匹配的关键点"""

    try:
        response = await llm.ainvoke(prompt, config=config)
        analysis = response.content if hasattr(response, "content") else str(response)
        return {
            "resume_analysis": analysis,
            "completed_tasks": ["resume_analysis"],
        }
    except Exception as e:
        logger.error(f"简历分析失败: {e}")
        return {
            "resume_analysis": f"简历分析失败: {e}",
            "completed_tasks": ["resume_analysis"],
        }


# ============================================================
# 完成标记节点（用于任务分支结束）
# ============================================================


def mark_interview_done(state: InterviewResearchState) -> dict[str, Any]:
    """标记面试经验搜索任务完成"""
    return {"completed_tasks": ["interview_search"]}


def mark_salary_done(state: InterviewResearchState) -> dict[str, Any]:
    """标记薪资搜索任务完成"""
    return {"completed_tasks": ["salary_search"]}


# ============================================================
# 第四阶段：报告生成
# ============================================================


async def generate_report(
    state: InterviewResearchState, config: RunnableConfig, writer: StreamWriter
) -> dict[str, Any]:
    """生成最终面试准备报告"""
    writer({"node": "generate_report", "status": "generating"})

    role_name = state.get("role_name", "未知职位")
    company_name = state.get("company_name", "")
    company_display = company_name if company_name else "通用"

    sections = []

    if state.get("resume_analysis"):
        sections.append(f"## 📋 简历分析与问题预测\n{state['resume_analysis']}")

    if state.get("interview_experience"):
        sections.append(f"## 🎯 面试经验\n{state['interview_experience']}")

    if state.get("company_product"):
        sections.append(f"## 🏢 公司产品与业务\n{state['company_product']}")

    if state.get("salary_info"):
        sections.append(f"## 💰 薪资待遇参考\n{state['salary_info']}")

    if state.get("business_info"):
        sections.append(f"## 📊 工商信息\n{state['business_info']}")

    if state.get("role_risk_info"):
        sections.append(f"## ⚠️ 岗位避雷\n{state['role_risk_info']}")

    report = f"""# {company_display} {role_name} 面试准备指南

{chr(10).join(sections)}

---
*报告生成时间：{__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""

    return {
        "final_report": report,
        "messages": [AIMessage(content=report)],
    }


# ============================================================
# 路由函数
# ============================================================


def route_interview_branch(state: InterviewResearchState) -> str:
    """路由：面试经验 -> 兜底 OR 完成"""
    if state.get("company_interview_found", False):
        return "mark_interview_done"
    return "fallback_industry_interview"


def route_salary_branch(state: InterviewResearchState) -> str:
    """路由：薪资 -> 兜底 OR 完成"""
    if state.get("company_salary_found", False):
        return "mark_salary_done"
    return "fallback_industry_salary"


def route_after_interview_complete(state: InterviewResearchState) -> str:
    """路由：面试经验任务完成 -> 简历分析"""
    # 面试经验搜索完毕后，触发简历分析
    if state.get("resume_text"):
        return "analyze_resume"
    # 如果没有简历，简历分析任务视为直接完成（或跳过）
    # 但为了逻辑统一，我们可以让 analyze_resume 处理空简历的情况并返回 completed
    # 这里我们选择直接去 analyze_resume，它会处理空值
    return "analyze_resume"


def check_global_completion(state: InterviewResearchState) -> str:
    """检查所有任务是否完成 -> 生成报告 OR 等待"""
    # 需要等待的任务：
    # 1. resume_analysis (依赖 interview_search)
    # 2. salary_search
    # 3. business_info
    # 4. role_risk
    # 5. company_product
    #
    # 注意：interview_search 本身不是最终等待项，resume_analysis 才是（或者说它是 interview 链的终点）

    if _check_all_tasks_completed(state):
        return "generate_report"
    return END  # 如果未全部完成，当前分支结束（等待其他分支）


def init_workflow(state: InterviewResearchState) -> dict[str, Any]:
    """初始化工作流，设置待完成任务"""
    pending = []
    company_name = state.get("company_name")
    jd_text = state.get("jd_text")
    is_large = state.get("is_large_company", False)

    # 核心任务
    pending.append("resume_analysis") # 面试链终点
    pending.append("salary_search")   # 薪资链终点

    if company_name:
        pending.append("business_info")
        pending.append("role_risk")
        if is_large or jd_text:
            pending.append("company_product")

    return {"pending_tasks": pending, "completed_tasks": []}


def route_start(state: InterviewResearchState) -> list[Send]:
    """分发初始任务"""
    sends = []
    company_name = state.get("company_name")
    jd_text = state.get("jd_text")
    is_large = state.get("is_large_company", False)

    if company_name:
        sends.append(Send("probe_company_interview", state))
        sends.append(Send("probe_company_salary", state))
        sends.append(Send("search_business_info", state))
        sends.append(Send("search_role_risk", state))
        if is_large or jd_text:
            sends.append(Send("search_company_product", state))
    else:
        sends.append(Send("fallback_industry_interview", state))
        sends.append(Send("fallback_industry_salary", state))

    return sends


# ============================================================
# 构建图
# ============================================================


graph = StateGraph(InterviewResearchState)

# 初始化节点
graph.add_node("init", init_workflow)

# 第一阶段：探测节点
graph.add_node("probe_company_interview", probe_company_interview)
graph.add_node("probe_company_salary", probe_company_salary)
graph.add_node("search_business_info", search_business_info)
graph.add_node("search_role_risk", search_role_risk)
graph.add_node("search_company_product", search_company_product)

# 第二阶段：兜底节点
graph.add_node("fallback_industry_interview", fallback_industry_interview)
graph.add_node("fallback_industry_salary", fallback_industry_salary)

# 标记节点 (用于统一分支结束状态)
graph.add_node("mark_interview_done", mark_interview_done)
graph.add_node("mark_salary_done", mark_salary_done)

# 第三阶段：分析节点
graph.add_node("analyze_resume", analyze_resume)

# 汇聚检查节点
# 我们创建一个 pass-through node 来作为 join point 检查
def join_gate(state: InterviewResearchState) -> dict[str, Any]:
    return {}

graph.add_node("join_gate", join_gate)

# 第四阶段：报告生成
graph.add_node("generate_report", generate_report)


# === 连线 ===

graph.set_entry_point("init")
graph.add_conditional_edges("init", route_start)

# 1. 面试链路
# probe -> (found) -> mark_done -> analyze
# probe -> (not found) -> fallback -> analyze
graph.add_conditional_edges(
    "probe_company_interview",
    route_interview_branch,
    {
        "mark_interview_done": "mark_interview_done",
        "fallback_industry_interview": "fallback_industry_interview"
    }
)

# 行业兜底直接进入简历分析（因为它意味着面试经验搜索结束）
# 但我们需要确保 "interview_search" 任务概念上的完成？
# 其实在我们的设计中，resume_analysis 是面试链的最终等待项。
# 只要 probe -> fallback -> analyze 链路通畅即可。
# 如果 probe 成功 -> mark_interview_done -> analyze?
# 是的。

# 注意：mark_interview_done 只是标记 task complete?
# 不，resume_analysis 才是 pending task。
# 所以我们不需要 "interview_search" task，只需要 resume_analysis task。
# 但是 wait，resume_analysis 依赖 interview_experience。
# 所以我们需要在 interview_experience 准备好后调用 analyze_resume。

# 修改路由：
# probe -> [check] -> fallback -> analyze
# probe -> [check] -> analyze (直接)

# 重新设计 interview 路由
def route_probe_interview(state: InterviewResearchState) -> str:
    if state.get("company_interview_found", False):
        return "analyze_resume"
    return "fallback_industry_interview"

graph.add_conditional_edges(
    "probe_company_interview",
    route_probe_interview,
    {"analyze_resume": "analyze_resume", "fallback_industry_interview": "fallback_industry_interview"}
)

graph.add_edge("fallback_industry_interview", "analyze_resume")

# 2. 薪资链路
# probe -> [check] -> fallback -> mark_done
# probe -> [check] -> mark_done

def route_probe_salary(state: InterviewResearchState) -> str:
    if state.get("company_salary_found", False):
        return "mark_salary_done"
    return "fallback_industry_salary"

graph.add_conditional_edges(
    "probe_company_salary",
    route_probe_salary,
    {"mark_salary_done": "mark_salary_done", "fallback_industry_salary": "fallback_industry_salary"}
)

graph.add_edge("fallback_industry_salary", "mark_salary_done")

# 3. 独立任务完成后的流向
# 所有分支的终点都指向 join_gate

graph.add_edge("analyze_resume", "join_gate") # resume_analysis 完成
graph.add_edge("mark_salary_done", "join_gate") # salary_search 完成
graph.add_edge("search_business_info", "join_gate") # business_info 完成
graph.add_edge("search_role_risk", "join_gate") # role_risk 完成
graph.add_edge("search_company_product", "join_gate") # company_product 完成

# 4. Join Gate 检查
graph.add_conditional_edges(
    "join_gate",
    check_global_completion,
    {"generate_report": "generate_report", END: END}
)

graph.add_edge("generate_report", END)

# 编译图
interview_prep_graph = graph.compile()
interview_prep_graph.name = "interview-prep-graph"
