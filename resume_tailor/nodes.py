import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .state import ResumeTailorState
from .prompts import (
    ANALYZE_JD_PROMPT,
    TAILOR_SUMMARY_PROMPT,
    TAILOR_EXPERIENCE_PROMPT,
    TAILOR_SKILLS_PROMPT
)
from .utils import get_llm, get_search_tool

llm = get_llm()

def analyze_job_posting(state: ResumeTailorState) -> dict:
    """Analyzes the JD to extract specific targeting info."""
    print("--- Analysis Phase ---")
    jd = state["job_description"]

    prompt = ChatPromptTemplate.from_template(ANALYZE_JD_PROMPT)
    chain = prompt | llm | JsonOutputParser()

    analysis = chain.invoke({"job_description": jd})
    return {"analysis": analysis}

def research_company(state: ResumeTailorState) -> dict:
    """Searches for company culture/values if company name is in JD."""
    print("--- Research Phase ---")
    # This is a simplification. A real agent might extract the company name first.
    # We'll just search for 'Company Culture' + first few words of JD title if explicit name isn't passed,
    # or rely on the extraction from the previous step if we modified the state to hold company name.

    # For now, let's assume the JD might contain the company name or we just search broadly based on context.
    # But usually, the user provides the company name or it's in the text.

    search = get_search_tool()
    query = f"Company culture and values for job description: {state['job_description'][:100]}..."
    results = search.run(query)

    return {"company_research": str(results)}

def tailor_resume(state: ResumeTailorState) -> dict:
    """The main execution node. Iterates through the resume sections."""
    print("--- Tailoring Phase ---")
    resume = state["resume_data"]
    analysis = state["analysis"]
    culture_context = state.get("company_research", "")
    config = state.get("config", {})

    tailored_resume = resume.copy()

    # 1. Tailor Summary
    if "summary" in resume:
        summary_prompt = ChatPromptTemplate.from_template(TAILOR_SUMMARY_PROMPT)
        summary_chain = summary_prompt | llm

        # Prepare context for the prompt
        keywords = f"{analysis.get('hard_skills', [])}, {analysis.get('soft_skills', [])}"

        new_summary = summary_chain.invoke({
            "current_summary": resume["summary"],
            "target_title": analysis.get("key_responsibilities", "Target Role"), # Simplification
            "keywords": keywords,
            "pain_points": analysis.get("pain_points", ""),
            "culture": f"{analysis.get('culture', '')}. External Research: {culture_context}"
        })
        tailored_resume["summary"] = new_summary.content

    # 2. Tailor Experience
    if "experience" in resume:
        tailored_experience = []
        exp_prompt = ChatPromptTemplate.from_template(TAILOR_EXPERIENCE_PROMPT)
        exp_chain = exp_prompt | llm | JsonOutputParser() # Expecting list of strings

        for job in resume["experience"]:
            # job is expected to have 'role', 'company', 'bullets' (list)
            try:
                # Handle cases where bullets might be a string or list
                current_bullets = job.get("bullets", [])
                if isinstance(current_bullets, str):
                    current_bullets = [current_bullets]

                new_bullets = exp_chain.invoke({
                    "role": job.get("role", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "current_bullets": current_bullets,
                    "keywords": keywords,
                    "pain_points": analysis.get("pain_points", ""),
                    "remove_irrelevant": config.get("remove_irrelevant", False),
                    "exaggerate": config.get("exaggerate", False)
                })

                job_copy = job.copy()
                job_copy["bullets"] = new_bullets
                tailored_experience.append(job_copy)
            except Exception as e:
                print(f"Error tailoring job {job.get('role')}: {e}")
                tailored_experience.append(job) # Fallback to original

        tailored_resume["experience"] = tailored_experience

    # 3. Tailor Skills
    if "skills" in resume:
        skills_prompt = ChatPromptTemplate.from_template(TAILOR_SKILLS_PROMPT)
        skills_chain = skills_prompt | llm

        # Determine current skills format (list or dict)
        current_skills = resume["skills"]
        new_skills_resp = skills_chain.invoke({
            "current_skills": current_skills,
            "keywords": keywords
        })

        # We'll just take the text output for now, assuming the prompt instructs well.
        # Ideally, we'd parse this back into the original structure.
        # For this PoC, we store it as a string or try to parse if JSON.
        try:
            tailored_resume["skills"] = json.loads(new_skills_resp.content)
        except:
            tailored_resume["skills"] = new_skills_resp.content.split("\n")

    return {"tailored_resume_data": tailored_resume}

def format_resume(state: ResumeTailorState) -> dict:
    """Final output generation (Optional)."""
    # In a full app, this might generate a PDF or Markdown string.
    # For now, we rely on the structured data being the result.
    return {}
