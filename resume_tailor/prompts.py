# 简历定制代理的提示词

ANALYZE_JD_PROMPT = """You are an expert Career Coach and Resume Strategist.
Your task is to deconstruct the following Job Description (JD) using the "Mirror Method".

Job Description:
{job_description}

Analyze the JD and extract the following:
1. **Keywords**:
   - Hard Skills: Specific tools, certifications, methodologies.
   - Soft Skills: Adjectives used to describe the ideal employee (e.g., "scrappy", "entrepreneurial").
2. **Pain Points**: What specific problems is the company trying to solve? Read between the lines.
3. **Culture**: Based on the tone, is it Corporate/Formal or Startup/Modern?
4. **Key Responsibilities**: The top 3-5 most important duties.

Return the output as a JSON object with keys: "hard_skills", "soft_skills", "pain_points", "culture", "key_responsibilities".
"""

STRATEGIC_ASSESSMENT_PROMPT = """You are a Strategic Resume Consultant.
Your goal is to define the structure and high-level strategy for the resume based on the Job Description (JD) and the Candidate's Profile.

**Inputs:**
- JD Analysis: {analysis}
- Candidate Summary: {current_summary}
- Candidate Experience (Brief): {experience_overview}

**Tasks:**
1. **Target Title**: Extract the EXACT job title from the JD to be used as the resume headline.
2. **Section Ordering**: Decide the optimal order of sections.
   - If the candidate's recent experience is a perfect match, use: ["summary", "experience", "skills", "education"].
   - If the candidate is pivoting or lacks direct experience, use: ["summary", "skills", "experience", "education"].
3. **Key Achievements**: Select 3 specific "wins" or projects from the candidate's history that directly prove they can solve the JD's "Pain Points". (Summarize them briefly).

Return a JSON object with keys:
- "target_title": string
- "section_order": list of strings
- "key_achievements": list of strings
"""

TAILOR_SUMMARY_PROMPT = """You are a professional resume writer. Rewrite the Professional Summary and Header.

**Context:**
- Current Summary: {current_summary}
- Target Job Title (Headline): {target_title}
- Key Skills to Highlight: {keywords}
- Pain Points to Address: {pain_points}
- Company Culture: {culture}

**Instructions:**
- **Headline**: The first line MUST be the Target Job Title.
- **Summary**: Follow this formula: [Adjective from JD] [Target Title] with [Number] years of experience. Expert in [Skill 1] and [Skill 2]. Proven track record of [Major Achievement relevant to JD].
- If the JD mentions specific goals (e.g., "Global Expansion"), explicitly mention experience relevant to that.
- Keep the summary under 4 lines.

Output ONLY the rewritten summary text (do not include the headline in the text block, strictly the paragraph).
"""

TAILOR_EXPERIENCE_PROMPT = """You are a professional resume writer. Your task is to tailor a specific job entry from a resume to match a target Job Description.

**Input Data:**
- Role: {role}
- Company: {company}
- Current Description (Bullets): {current_bullets}
- Target Job Keywords: {keywords}
- Target Pain Points: {pain_points}
- Configuration - Remove Irrelevant: {remove_irrelevant}
- Configuration - Exaggerate Mode: {exaggerate}

**Instructions:**
1. **Re-prioritize**: Move bullet points that match the JD's requirements to the top.
2. **Language Mirroring**: Change verbs and phrasing to match the JD (e.g., change "Managed team" to "Orchestrated cross-functional collaboration" if the JD uses that language).
3. **Metric Matching**: If the JD focuses on efficiency, highlight time saved. If growth, highlight revenue.
4. **Irrelevant Info**: If `remove_irrelevant` is True, remove bullets that have NO connection to the new role.
5. **Exaggeration Level**:
   - If `exaggerate` is False: Stick strictly to the facts.
   - If `exaggerate` is True: Use "Power Verbs" and aggressive framing.

6. **Bolding**: Wrap key matching terms in bold markdown (e.g., **Python**).

Return the tailored bullet points as a list of strings.
"""

TAILOR_SKILLS_PROMPT = """You are optimizing the "Skills" section for an ATS.

**Input:**
- Current Skills: {current_skills}
- JD Keywords (Hard/Soft): {keywords}

**Instructions:**
1. **Exact Phrasing**: Use the exact specific skill names found in the JD (e.g., "MS Excel" instead of "Microsoft Office").
2. **Categorization**: Group skills logically (e.g., "Languages", "Tools", "Frameworks").
3. Prioritize skills mentioned in the JD.

Return the result as a list of strings or a dictionary of categories.
"""
