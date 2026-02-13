# 面试准备 Agent 优化方案 (基于 GPT Researcher 深度分析)

本文档基于对 `gpt_researcher` 核心架构与提示词设计的深度分析，为 `InterviewPrepAgent` 提供生产级优化建议。

## 1. 核心设计理念对比

| 特性 | GPT Researcher | 当前 InterviewPrepAgent | 优化建议 |
| :--- | :--- | :--- | :--- |
| **提示词工程** | 结构化、动态上下文、角色沉浸、防御性指令 | 较为简单、直接 | 引入 `PromptFamily` 模式，针对不同任务（如简历分析 vs 职位分析）定制高鲁棒性提示词。 |
| **架构设计** | 模块化 Skills (Browser, Writer, Curator) | 单文件 Graph | 将功能拆分为 `skills/` 模块，Graph 仅负责编排。 |
| **上下文管理** | 累积式上下文、Token 优化、来源追踪 | 简单的字符串拼接 | 引入结构化 `ContextManager`，支持来源溯源和引用。 |
| **可靠性** | 多重兜底、自适应策略 (Fast/Deep) | 基础兜底 | 增强兜底逻辑，引入自我反思/检查机制。 |

## 2. 提示词设计优化 (Prompt Engineering)

参考 `gpt_researcher/prompts.py`，建议重构提示词系统。

### 2.1 结构化角色与任务定义

**当前问题**：提示词较为扁平，缺乏对 LLM 角色和约束的强定义。

**优化方案**：
采用 "Role + Context + Task + Constraints + Output Format" 的五段式结构。

```python
# 示例：优化后的简历分析提示词
RESUME_ANALYSIS_PROMPT = """
<|start_of_role|>
You are an Expert Technical Recruiter with 15 years of experience in {industry}.
Your goal is to critically analyze a candidate's resume against a specific Job Description (JD) to predict interview risks and questions.
<|end_of_role|>

<|start_of_context|>
JOB DESCRIPTION:
{jd_text}

INTERVIEW INSIGHTS (from web search):
{interview_experience}
<|end_of_context|>

<|start_of_task|>
Analyze the RESUME provided below. Focus ONLY on the gap between the Resume and the JD/Interview Insights.
Do not provide generic advice. Be specific and critical.

RESUME:
{resume_text}
<|end_of_task|>

<|start_of_constraints|>
1. Output MUST be in valid JSON format.
2. Prioritize "Killer Questions" - technical depth questions that expose weak spots.
3. Identify "Red Flags" (gaps, short tenures, mismatching skills).
4. Do NOT compliment the candidate; focus on preparation.
<|end_of_constraints|>

<|start_of_format|>
Response format:
{{
    "match_score": <0-100>,
    "critical_gaps": ["gap1", "gap2"],
    "predicted_questions": [
        {{
            "question": "...",
            "reasoning": "Based on JD requirement X and Resume gap Y"
        }}
    ],
    "red_flags": ["flag1"]
}}
<|end_of_format|>
"""
```

### 2.2 动态思维链 (Dynamic CoT)

`gpt_researcher` 使用 `generate_search_queries_prompt` 来动态生成搜索计划。我们可以在 `probe` 阶段引入类似的机制。

*   **当前**：直接搜索 "{Company} {Role} 面试经验"。
*   **优化**：先让 LLM 生成搜索关键词列表（如 "XX公司 算法题库", "XX公司 文化 价值观"），再并行搜索。

### 2.3 来源引证 (Citations)

参考 `generate_report_prompt` 中的引用要求：
> "You MUST use in-text citation references... and make it with markdown hyperlink."

在生成最终报告时，强制要求 LLM 标注信息来源（如 `[来源1](url)`），增加报告的可信度。

## 3. 架构设计优化

### 3.1 引入 "Skills" 抽象

当前代码将所有逻辑写在 Graph 节点函数中。建议参考 `gpt_researcher/skills/` 进行拆分：

*   `skills/researcher.py`: 封装 `BaiduSearch` 和 `GoogleSearch`，统一返回 `Document` 对象（含 metadata）。
*   `skills/analyst.py`: 封装 LLM 分析逻辑（简历分析、JD 提取）。
*   `skills/writer.py`: 负责最终报告的生成和排版。

### 3.2 增强型状态管理 (State Management)

在 `InterviewResearchState` 中增加更丰富的数据结构：

```python
class InterviewResearchState(MessagesState):
    # ... 原有字段 ...

    # 新增：结构化资源库
    retrieved_docs: list[Document]  # 存储所有搜索到的原始文档

    # 新增：中间思考过程
    search_plan: list[str]  # 搜索计划
    reflection_notes: list[str]  # 自我反思笔记

    # 新增：配置项
    config: dict  # 包含 deep_mode, language 等配置
```

### 3.3 深度研究模式 (Deep Mode)

参考 `DeepResearchSkill`，为 VIP 用户或复杂场景增加 "Deep Mode"：
1.  **广度搜索**：先搜公司整体面经。
2.  **深度挖掘**：针对搜到的具体技术栈（如 "React Hook 原理"）进行二次定向搜索。
3.  **递归合成**：将多轮搜索结果合并分析。

## 4. 输出质量控制

### 4.1 报告结构标准化

参考 `generate_report_prompt`，使用 Markdown 模板强制输出结构：

1.  **核心结论** (TL;DR)
2.  **岗位画像** (基于 JD 和 外部信息)
3.  **简历匹配度分析** (Radar Chart 数据 + 详细 GAP 分析)
4.  **预测题库** (分类：行为、技术、系统设计)
5.  **薪资谈判策略** (基于查到的薪资数据)
6.  **参考资料列表**

### 4.2 自我修正循环

在 `generate_report` 之前增加 `Review` 节点：
*   LLM 检查：报告是否回答了用户的所有隐性需求？薪资数据是否缺失？
*   如果缺失关键信息，触发 `supplementary_search` (补充搜索)。

## 5. 执行路线图

1.  **Phase 1 (Prompt Upgrade)**: 将所有硬编码提示词提取到 `prompts.py`，应用结构化 Prompt 模板。
2.  **Phase 2 (Skills Refactoring)**: 拆分 `interview_prep_graph.py`，建立 `skills/` 目录。
3.  **Phase 3 (Deep Mode)**: 实现 "生成搜索计划 -> 并行执行 -> 递归深入" 的高级流程。
4.  **Phase 4 (Citation System)**: 改造搜索模块，保留 URL 并在最终报告中生成引用。
