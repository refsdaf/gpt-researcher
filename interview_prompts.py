"""
面试准备 Agent 提示词库
采用 Role-Context-Task 结构设计，提升 LLM 输出的稳定性与针对性。
"""
from datetime import datetime

class InterviewPrompts:

    @staticmethod
    def get_resume_analysis_prompt(role_name: str, jd_text: str, interview_exp: str, resume_text: str) -> str:
        return f"""<|start_of_role|>
你是一位拥有 15 年经验的资深技术招聘专家和面试官。
你的目标是基于职位描述 (JD) 和市场面试情报，深入审视候选人的简历，挖掘潜在风险并预测高价值面试题。
<|end_of_role|>

<|start_of_context|>
【目标职位】
{role_name}

【职位描述 (JD)】
{jd_text if jd_text else "未提供详细 JD，请基于通用岗位标准分析。"}

【市场面试情报】
{interview_exp[:2000] if interview_exp else "暂无特定公司面试情报，请基于行业通用标准。"}
<|end_of_context|>

<|start_of_task|>
请分析以下简历，重点关注“简历内容”与“职位要求/面试情报”之间的差距。
不要提供泛泛的建议，要一针见血。

【候选人简历】
{resume_text}
<|end_of_task|>

<|start_of_constraints|>
请以 Markdown 格式输出以下四个模块，保持简洁：

1. **匹配度评估**
   - 给出匹配度评分 (0-100)
   - 列出 3 个核心匹配点
   - 列出 3 个关键缺口 (Critical Gaps)

2. **高频问题预测**
   - 结合 JD 重点和简历经历，预测 5 个深度面试题。
   - 包含：2个技术深挖题，2个项目细节题，1个软技能/行为题。
   - *格式：问题 (对应考察点)*

3. **风险预警 (Red Flags)**
   - 识别简历中的硬伤（如：空窗期、跳槽频繁、技能栈过时、描述虚浮等）。
   - 为每个风险点提供一句应对话术。

4. **自我介绍优化建议**
   - 基于岗位关键词，给出一个 30 秒的“高光”自我介绍逻辑框架。
<|end_of_constraints|>
"""

    @staticmethod
    def get_business_info_search_prompt(company_name: str) -> str:
        return f"""请搜索 {company_name} 公司的工商信息与经营风险。
重点关注：
1. 成立时间、注册资本、人员规模
2. 近期的法律诉讼（尤其是劳动争议、合同纠纷）
3. 经营异常或行政处罚记录

如果是知名大公司，请简述其核心业务板块。
如果是初创/小公司，请评估其经营稳定性。
请将回答控制在 150 字以内，客观中立。"""

    @staticmethod
    def get_role_risk_search_prompt(company_name: str, role_name: str) -> str:
        return f"""请搜索 {company_name} {role_name} 岗位的“避雷”信息或员工真实评价。
重点挖掘：
1. 真实的加班强度与考勤制度（如 996、大小周）
2. 部门稳定性（是否有裁员、毁约、卡转正记录）
3. 薪资兑现情况（年终奖打折、绩效坑）

如果找不到该公司具体信息，请列出该行业同类岗位的常见坑。
回答控制在 150 字以内，直接列出风险点。"""

    @staticmethod
    def get_company_product_search_prompt(company_name: str, role_name: str) -> str:
        return f"""请搜索 {company_name} 公司的核心产品与业务动态，特别是与 {role_name} 岗位相关的部分。
关注：
1. 核心盈利产品是什么？
2. 近期（半年内）发布了什么新产品或战略？
3. {role_name} 岗位可能所在的业务线及其在公司中的地位。

回答控制在 200 字以内，侧重业务逻辑。"""

    @staticmethod
    def get_fallback_interview_prompt(role_name: str) -> str:
        return f"""请总结 {role_name} 岗位在 2024 年的行业通用面试指南。
包含：
1. 标准面试流程（如：机试 -> 技术一面 -> 技术二面 -> HR面）
2. 5 个必考的基石面试题（含技术与非技术）
3. 面试官最看重的 3 个核心素质

请以 Markdown 列表形式输出。"""

    @staticmethod
    def get_fallback_salary_prompt(role_name: str) -> str:
        return f"""请提供 {role_name} 岗位的 2024 年市场薪资行情报告。
包含：
1. 一线城市 vs 二线城市的薪资范围
2. 应届/1-3年/3-5年/5年以上 的薪资阶梯
3. 该岗位的薪资构成惯例（如：底薪+绩效+期权）
4. 谈薪时的高情商话术建议（1条）

回答控制在 200 字以内。"""
