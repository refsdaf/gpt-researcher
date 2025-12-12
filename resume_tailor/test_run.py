import os
import json
from resume_tailor.graph import create_resume_tailor_graph

# 模拟数据
MOCK_RESUME = {
    "summary": "Software Engineer with 5 years experience in web dev.",
    "experience": [
        {
            "role": "Senior Developer",
            "company": "Tech Corp",
            "bullets": [
                "Built a react app.",
                "Managed a team of 3.",
                "Optimized database queries.",
                "Organized the office holiday party."
            ]
        },
        {
            "role": "Junior Developer",
            "company": "Startup Inc",
            "bullets": [
                "Fixed bugs in Python backend.",
                "Wrote unit tests."
            ]
        }
    ],
    "skills": ["React", "Python", "SQL", "Git"]
}

MOCK_JD = """
We are looking for a Senior Full Stack Engineer (Python/React) to join our fast-paced startup.
Must be scrappy, entrepreneurial, and ready to ship code daily.
Key Responsibilities:
- Architect scalable backend systems using Python (Django/FastAPI).
- Lead frontend development with React.
- Mentor junior engineers.
- Solve complex performance bottlenecks.
Required Skills: Python, React, PostgreSQL, AWS, CI/CD.
Pain Points: We are growing too fast and our current legacy code is slow. We need someone to refactor it without stopping feature dev.
"""

def run_test():
    graph = create_resume_tailor_graph()

    inputs = {
        "resume_data": MOCK_RESUME,
        "job_description": MOCK_JD,
        "config": {
            "remove_irrelevant": True,
            "exaggerate": True
        }
    }

    print("Starting Resume Tailor Agent...")
    try:
        result = graph.invoke(inputs)
        print("\n\nResulting Tailored Resume:")
        print(json.dumps(result["tailored_resume_data"], indent=2))
        print("\nAnalysis:")
        print(json.dumps(result["analysis"], indent=2))
    except Exception as e:
        print(f"Error running graph: {e}")

if __name__ == "__main__":
    run_test()
