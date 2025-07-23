import os
import warnings
from crewai import Agent, Task, Crew, LLM, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from IPython.display import Markdown, display
from bs4 import BeautifulSoup
import requests
import re
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore", category=UserWarning)

# Check for API keys in environment
if not os.getenv("GROQ_API_KEY") or not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY and OPENAI_API_KEY must be set in your environment or .env file.")

# Initialize LLMs
groq_llm = LLM(model="groq/llama-3.3-70b-versatile")
openai_llm = LLM(model="openai/gpt-4o-mini")

# Merge text files utility

expected_output = """ A complete resume formatted in plain text markdown-style structure with job-targeted projects and language. Keywords should be embedded, not listed.
# {{name}}

## Contact Information  
📧 {{email}} | 📞 {{phone}} | 🔗 [LinkedIn]({{linkedin}}) | 📍 {{location}}

---

## Professional Summary  
{{summary}}

---

## Technical Skills  
{{technical_skills}}

---

## Professional Experience  
{{#each experience}}
### {{title}} | **{{company}}**  
📅 {{start_date}} – {{end_date}}  
{{#each responsibilities}}
- {{this}}
{{/each}}

{{/each}}

---

## Education  
{{#each education}}
### {{degree}}  
**{{institution}}** | {{year}}  
{{#each details}}
- {{this}}
{{/each}}

{{/each}}

---

## Projects  
{{#each projects}}
### {{project_name}}  
{{#each highlights}}
- {{this}}
{{/each}}

{{/each}}

"""

def merge_text_files(file_list, output_file):
    missing_files = [file for file in file_list if not os.path.exists(file)]
    if missing_files:
        print(f"Error: The following files were not found: {missing_files}")
        return
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for file in file_list:
            try:
                with open(file, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
            except UnicodeDecodeError:
                try:
                    with open(file, 'r', encoding='cp1252') as infile:
                        outfile.write(infile.read())
                except UnicodeDecodeError:
                    print(f"Warning: Could not read file {file} due to encoding issues")
                    continue
            outfile.write("\n" + "="*40 + "\n")
    print(f"Merged file saved as '{output_file}'")

# Example file list (update with your actual file paths)
file_list = [
    'agent_output__jd.txt',
    'agent_output_company.txt',
    'agent_output_github.txt',
    'agent_output_profile.txt'
]
output_file = 'knowledge/merged_output.txt'
merge_text_files(file_list, output_file)

# Load knowledge sources
text_knowledge = TextFileKnowledgeSource(file_paths=[
    "merged_output.txt",
    "knowledgebase.txt"
])

resume_builder_agent = Agent(
    role="Senior Resume Builder and Career Strategist",
    goal="Create and refine a resume that is ATS-optimized and aligned with job, company, and technical profile.",
    backstory="You're a resume writing expert who knows how to translate project work into ATS-optimized bullet points aligned with top tech company expectations.",
    llm=openai_llm,
    verbose=True,
    knowledge_sources=[text_knowledge]
)

ats_agent = Agent(
    role="ATS Resume Evaluator",
    goal="Evaluate the resume for keyword relevance, technical alignment, formatting, and ATS compatibility. Give feedback to improve it.",
    backstory="You're a top-tier ATS and HR screening specialist trained to critique resumes using real hiring systems and keyword data.",
    llm=groq_llm,
    verbose=True,
    knowledge_sources=[text_knowledge]
)

def build_resume_task(resume_draft=""):
    return Task(
        description=f"""
You are an expert AI resume builder creating highly targeted, ATS-optimized, and human-readable resumes.

You have access to:
- The candidate’s job description, company research, GitHub profile, and previous experience (via knowledgebase)
- A list of keywords relevant to the role (implicitly embedded in the knowledgebase)
- Optional feedback from an ATS system (see below)

---

🔁 Resume Revision Cycle

If feedback is available, apply the suggestions carefully.

Previous ATS Feedback:
{resume_draft}

---

use these personal details for resume creation 

Name: P Kavya Samhitha
Phone: 7619565560
Email: savya20014@gmail.com
Location: Bengaluru
LinkedIn: www.linkedin.com/in/p-kavya-samhitha-65a308212

Education:
PES University, B.Tech Computer Science (2022–2026), CGPA: 8.07/10.0

Primus PU College, 12th Grade: 90.3% (2020–2022)

Delhi Public School East, 10th Grade: 95.1% (2012–2020)

Activities / Volunteering:
Events Team – Maaya Fest 2023

Finance Team – Maaya Fest 2024

ACM Club Member – Ops & Tech



🎯 Your Task

Generate a **complete, professional, ATS-optimized resume** formatted in clean plain-text using markdown-style formatting.

Focus on:
- Selecting 3–4 most relevant projects
- Integrating keywords naturally (no dumping)
- Two strong achievement-focused bullets per project
- Tight role alignment and structure


---
Here are just the examples these are examples Do not use this (NOT TO USE THIS PROJECTS IN RESUME) just take for reference
### ModelForge - Low-Code Machine Learning Framework  
- Developed a comprehensive low-code framework facilitating user-friendly training of AI models via intuitive YAML syntax, showcasing expertise in TensorFlow and PyTorch.  
- Enabled rapid model deployment capabilities, resulting in a 30% reduction in time to market for AI solutions, in line with business objectives.

### Sentiment Analysis Using Custom Transformer Model  
- Constructed a transformer-based model for sentiment classification, optimizing preprocessing with NLTK and Hugging Face for enhanced model performance on unstructured data.  
- Achieved an accuracy improvement of 25% over previous benchmark models, directly addressing organizational needs for effective NLP applications.

### Fraud Detection System  
- Engineered a robust machine learning solution using XGBoost and scikit-learn, capable of detecting fraudulent transactions with 95% accuracy by implementing advanced anomaly detection methods.  
- Collaborated closely with cross-functional teams to integrate the solution into production, resulting in a 40% reduction in fraudulent transaction occurrence.


---
Sections must include:
- Contact Information
- Summary
- Skills (grouped)
- Work Experience (if available)
- Projects (3–4 only, 2 detailed bullets each)
- Education
""",
        expected_output=expected_output,
        agent=resume_builder_agent,
        output_file=f"D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_resume{i}.txt"
    )



def evaluate_resume_task(resume_text):
    return Task(
        description=f"""
You are an elite ATS (Applicant Tracking System) evaluator trained to assess resumes for keyword alignment, structure, and job fit.  

You have access to:
-  A candidate's resume (see below)
-  A knowledge base containing keywords grouped by job category and priority (Top, Medium, Low)
-  Company and job context (via knowledge base)

Your task is to **objectively and strictly evaluate the resume** for its fit based on:
1.  Keyword Matching
2.  Formatting and Structure
3.  Role Alignment
4.  Clarity and Technical Depth

---

###  Keyword Scoring Rules:
- Top Priority = 3 pts  
- Medium Priority = 2 pts  
- Low Priority = 1 pt

Only count keywords with real usage (not just mentions).

---

###  Resume to Evaluate: {resume_text}

---

###  ATS Resume Evaluation Report (Markdown)

1. **Score Breakdown**
| Priority | Matched | Points |
|----------|---------|--------|
| Top      | ? / 20  | ??     |
| Medium   | ? / 15  | ??     |
| Low      | ? / 15  | ??     |
| **Total**| –       | ??/100 |

---

2. **What’s Working Well **
- List of 2–3 strengths (project selection, structure, technical coverage, etc.)

---

3. **Missing or Underused Keywords **
-  Missing: …
-  Underused: …

---

4. **Suggestions for Improvement **
- e.g. Add more backend tech to project descriptions, improve metrics, remove buzzwords

---

5. **Final Verdict **
Short but direct: "This resume is 80% there. Improve project framing and boost backend keyword use."

---
Only use content from resume and knowledgebase. Do not invent extra experience or hallucinate!
""",
        expected_output="""
##  ATS Resume Evaluation Report
- Markdown score table
- Good feedback
- Missing keyword list
- Concrete suggestions
- Final verdict
""",
        agent=ats_agent,
        output_file=f"D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_ats{i}.txt"
    )

MAX_ITERATIONS = 3
resume_text = ""
ats_feedback = ""

for i in range(1, MAX_ITERATIONS + 1):
    print(f"\n🔁 Iteration {i} - Generating Resume...\n")
    resume_task = build_resume_task(resume_draft=ats_feedback)
    ats_task = evaluate_resume_task(resume_text=resume_text)
    crew = Crew(
        agents=[resume_builder_agent, ats_agent],
        tasks=[resume_task, ats_task],
        llm=groq_llm,
        planning=False
    )
    result = crew.kickoff()
    result_text = result.raw
    if "ATS Score Report" in result_text:
        resume_text = result_text.split("ATS Score Report")[0].strip()
        ats_feedback = "ATS Score Report" + result_text.split("ATS Score Report")[-1].strip()
        print(ats_feedback)
    else:
        resume_text = result_text.strip()
        print("No ATS feedback.")
        ats_feedback = ""
    resume_file_path = f"D:\\vs code\\ml\\crewAi\\github\\imp codes\\resume_v{i}.txt"
    with open(resume_file_path, 'w', encoding='utf-8') as file:
        file.write(resume_text)
    print(f"✅ Resume v{i} saved to: {resume_file_path}")
    if i == MAX_ITERATIONS:
        ats_report_path = "D:\\vs code\\ml\\crewAi\\github\\imp codes\\ats_final_report.txt"
        with open(ats_report_path, "w", encoding="utf-8") as report:
            report.write(ats_feedback)
        print("📄 Final ATS report saved.")
print("\n🎯 Resume refinement loop completed.")