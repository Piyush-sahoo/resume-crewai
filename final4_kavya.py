import os
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("GROQ_API_KEY") or not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY and OPENAI_API_KEY must be set in your environment or .env file.")

# Initialize LLMs
groq_llm = LLM(model="groq/llama-3.3-70b-versatile")
openai_llm = LLM(model="openai/gpt-4o-mini")

def main():
    # Load Job Description
    with open('d:\\vs code\\ml\\crewAi\\github\\imp codes\\description.txt', 'r', encoding='utf-8') as file:
        job_description = file.read()

    # Load Company Name
    with open('d:\\vs code\\ml\\crewAi\\github\\imp codes\\company.txt', 'r', encoding='utf-8') as file:
        company_name = file.read().strip()

    # Load GitHub Profile
    with open('d:\\vs code\\ml\\crewAi\\github\\imp codes\\refined_output_github_llm.txt', 'r', encoding='utf-8') as file:
        github_profile = file.read()

    # Load Candidate CV
    with open('d:\\vs code\\ml\\crewAi\\github\\imp codes\\portfolio.txt', 'r', encoding='utf-8') as file:
        candidate_cv = file.read()

    # Set API key and define LLMs
    openai_llm = LLM(
        model="openai/gpt-4o-mini", # call model by provider/model_name
    )
    groq_llm = LLM(model="groq/llama-3.3-70b-versatile")

    # JD Analyzer Agent & Task
    jd_analyzer_agent = Agent(
    role="Senior Technical Job Description Analyst",
    goal="Extract structured requirements and relevant insights from job descriptions for tailored resume creation",
    backstory="Specialist in breaking down job descriptions to find required skills, cultural fit hints, and tech keywords",
    llm=openai_llm,
    verbose=True
    )

    analyze_jd_task = Task(
    description=f"""
    You are a **Senior Technical Job Description Analyst**.

    Please analyze the following job description thoroughly:

    ---
    {job_description}
    ---

    Your mission is to break it down in an expert, **point-by-point prose format** (NOT JSON or bullet lists). Make it feel like a human expert consultant is explaining it to a job seeker.

    Your analysis must cover:

    1.  **Core Responsibilities**: Write out the major tasks this role will handle, with explanations — not just bullet points.
    2.  **Required Technical Skills**: Mention each mandatory skill and explain its context in this role.
    3.  **Preferred Skills / Tools**: Highlight optional or preferred tech stacks or experience areas.
    4.  **Experience Level**: Estimate if the job is entry, mid, or senior based on wording and requirements.
    5.  **Soft Skills & Cultural Expectations**: Mention if they’re seeking leadership, collaboration, communication, etc.
    6.  **Domain/Industry Specificity**: Point out if it's FinTech, HealthTech, B2B SaaS, etc.
    7.  **Implicit Expectations**: Infer hidden requirements. For example, if "fast-paced" is mentioned, note that it's likely a startup.
    8.  **Any Contradictions or Confusions**: If any responsibilities or requirements seem conflicting, explain them.
    9.  **Remote/On-Site Flexibility**: If mentioned, what does it imply about their work culture?
    10. **Company Values or Mission (if present)**: Comment on any signs of values/culture, diversity, or inclusion.

    💡 **Write this in clear paragraph form, with headers for each section. Avoid lists or JSON.**

    End your analysis with:
    -  "Overall Impression": What kind of candidate would be a strong fit?
    -  "Missing Info": Mention if any critical info is missing (like salary, tech versioning, team size, etc.)
    """,
    expected_output="A structured multi-paragraph natural language analysis that reads like a consultant's breakdown of the JD.",
    agent=jd_analyzer_agent,
    output_file="D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output__jd.txt"
)

    # Company Intelligence Agent & Task
    employer_data_extraction_agent = Agent(
    role="Company Intelligence Agent",
    goal=f"Research {company_name}'s tech stack and culture using verified sources",
    verbose=True,
    llm=groq_llm,
    backstory="Specializes in extracting accurate company data from public sources to help candidates tailor their applications effectively."
    )
    
    extract_employer_data_task = Task(
    description=f"""
    🔍 You are a **Company Intelligence Analyst**.

    Your goal is to extract real, verifiable insights about **{company_name}** to help a candidate tailor their resume for a specific job.

     The job description is:
    ---
    {job_description}
    ---

    Your analysis must include:

    ### 1. CHAIN-OF-VERIFICATION
    - Visit the **official careers page** of {company_name}.
    - Search **LinkedIn company profile**.
    - Search for {company_name} on **Crunchbase** and AngelList (if a startup).
    - Check GitHub/StackOverflow (if available) for tech mentions.
    - Cross-check at least 2–3 sources and **cite them clearly** (with URLs or notes).

    ### 2. OUTPUT FORMAT (In Paragraphs)

    Write your findings like a consultant report covering:

    **Tech Stack & Infrastructure**
    - Which programming languages, frameworks, and cloud tools are commonly mentioned?
    - Cross-reference with the JD: Are these also in the job?

    **Company Culture & Mission**
    - Are there cultural keywords (collaboration, innovation)?
    - Values or mission statements on their site?
    - DEI / inclusion efforts?

    **Industry & Market Position**
    - What industry/vertical are they in (e.g., FinTech, SaaS)?
    - Startup vs Enterprise feel?
    - Any recent funding or news?

    **Resume Tailoring Tips**
    - Based on findings, what keywords, traits, or experience should the candidate emphasize?

    **Sources Used**
    - Bullet list of data sources with short notes on what was found.
    - Ex: linkedin.com/company/xyz – mentioned remote-first, uses Kubernetes

    ### 3. EDGE CASE HANDLING
    - Ambiguous name? Ask: "Delta Airlines or Delta Electronics?"
    - No data? Fallback to JD and infer stack/tools
    - Name typo? Suggest closest valid matches

     End with a paragraph giving overall impression of the company from a job-seeker's lens.
    """,
    expected_output="""
    Detailed paragraph-based breakdown of company data and how it ties to the job description. Include sources used and resume tailoring tips.
    """,
    agent=employer_data_extraction_agent,
    output_file="D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output_company.txt",
    context=[analyze_jd_task]  # Only include if you have a JD analysis task
    )

    # GitHub Analyzer Agent & Task
    github_analyzer_agent = Agent(
    role="Targeted GitHub Profile Analyst",
    goal=f"Analyze {github_profile}'s GitHub projects to identify and summarize the most impactful repositories for a role at {company_name}",
    verbose=True,
    llm=openai_llm,
    backstory=(
        f"As a GitHub analysis expert and technical recruiter, you're trained to translate open-source contributions "
        f"into resume-worthy insights. You understand what hiring managers at companies like {company_name} value, and can extract "
        f"relevant technologies, metrics, and project outcomes aligned with their job descriptions."
    )
)
    analyze_github_task = Task(
    description=f"""
## 🧑‍💻 GitHub Technical Portfolio Analysis

You're provided with a GitHub profile summary and a list of repositories for a candidate targeting a role at **{company_name}**.  
You also have access to job requirements and company expectations (via context).  

Your job is to analyze the GitHub profile and provide a **comprehensive, structured markdown report** covering the candidate's most relevant repositories for this job.

---

### 📂 1. Repository Filtering
- Include only **public, non-forked, technically significant** repositories.
- Use the job description and company profile to determine relevance.
- Select the **top 10 repositories** if more exist.

---

### 📘 2. For Each Selected Repository (Markdown Format)

Use this exact structure for each repo:

#### 🔹 Repo: [RepoName](RepoURL)

- **Role**: (e.g., Owner / Maintainer / Contributor)
- **Stack**: (Python, React, AWS, etc.)
- **Stars**: ⭐ X | **Forks**: 🍴 Y | **Last Updated**: 📆 MM/YYYY

---

1. **Main Purpose & Features**  
   Describe what the project does and what problems it solves. Include key features or capabilities.

2. **Technical Stack & Implementation**  
   Explain how the project is built. Mention languages, tools, architecture (e.g., REST APIs, microservices), and devops elements (CI/CD, containerization).

3. **Significance & Real-World Application**  
   Explain who this project is for and how it's useful in real-world scenarios, especially in relation to roles like the one at **{company_name}**.

4. **Code Quality & Maintenance**  
   Comment on the documentation, code organization, update activity, test coverage, and community engagement (if applicable).

- **Key Resume Keywords**: `Python`, `Docker`, `Security Automation`, `CI/CD`, ...

---

### 🧾 3. Resume Highlights

At the end, summarize **6–8 bullet points** from across all repositories.  
These should be **achievement-based**, written for a resume:

**Example:**
- Developed [Tracecat](https://github.com/...) using Docker + Temporal to automate security workflows for incident response.
- Deployed project on AWS Fargate using Terraform; improved deployment time by 70%.
- Integrated RESTful APIs with scalable architecture and YAML-driven orchestration logic.
""",
    
    expected_output="""
Your final output **must be a clean markdown-formatted string** containing:

1.  **Up to 10 Repositories**  
   - Each in the format defined above: title, role, stack, 4 rich descriptive sections, and resume keywords.

2.  **6–8 Resume Bullet Points**  
   - Achievement-focused
   - Action-oriented verbs
   - Resume-ready and tech-aligned
""",
    
    agent=github_analyzer_agent,
    context=[analyze_jd_task, extract_employer_data_task],
    output_file="D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output_github.txt"
)
    
    
    
    # CV Analyzer Agent & Task
    cv_analyzer_agent = Agent(
    role="Resume Intelligence Analyst",
    goal=f"Analyze the candidate's CV and extract the most relevant projects, skills, and achievements tailored for a role at {company_name}",
    verbose=True,
    llm=openai_llm,
    backstory=(
        "You're a senior talent intelligence analyst with deep expertise in matching resumes to job descriptions. "
        "You're skilled at parsing resumes to identify impactful achievements and aligning them with specific role requirements. "
        "You act like a hiring manager's secret weapon for filtering out top-tier, job-ready candidates."
    )
)
    
    cv_analysis_task = Task(
    description=f"""
You're reviewing a candidate's resume to assess **fit for a job at {company_name}**.

---
 **Job Description**:
{job_description}

📄 The company profile has been analyzed already. Use that and the job description to match the resume below:
---
{candidate_cv}
---

---

##  **Phase 1: Relevance Matching** - **MOST IMPORTANT**

- Identify **projects** and **work experiences** in the CV that align directly with the job description.
- Focus on **technical stack**, **tools**, **problem-solving**, **collaboration**, and **delivery**.
- **Score the best 10 projects** (or fewer if less than 10) based on:
  - **Relevance to the job description**
  - **Skill match** (e.g., Python, React, etc.)
  - **Tools/tech match** with company/role
  - **Detail**: Add more descriptive insights into each project, emphasizing relevant keywords for the role and company.

---

##  **Phase 2: Skill Mapping** - **IMPORTANT**

- Extract top skills from the CV that match the JD (languages, frameworks, methodologies).
- Point out **missing** or **underrepresented** skills relevant to the role.
- Flag any **buzzwords** or vague areas to improve.

---

##  **Phase 3: Resume Enhancement Output** - **HIGHLIGHTED SECTION**

1. For each matched project:
   - Write a **detailed summary** of what makes it relevant .
   - Focus on **key learnings**, **tools used**, and **skills demonstrated**.
   - Emphasize how it connects to the JD/Company, highlighting specific skills or tools (e.g., "aligns with Python/AI focus at {company_name}").

2. End with:
   ** Optimized Resume Highlights for This Role**:
   - **4–6 bullet points** (copy-paste ready) customized for this company & JD.

---

##  **Suggested Improvements** - **TO BE ADDRESSED**

- Add more **specific details** or measurable outcomes to **Project X**, such as the improvements it led to or challenges overcome.
- Include **cloud computing** experience more prominently, especially if relevant to the company's tech stack (e.g., AWS, Azure).
- If there are any gaps in tools or technologies listed, consider adding skills like Docker, Kubernetes, or CI/CD tools if you have experience with them.
- Ensure that the **README** or project documentation clearly explains your contributions, and if possible, update any projects with more recent work or relevant additions.

---

 **Output must read like a professional recruiter wrote it**, not a list or JSON. Use **paragraphs with headers** and **focus on the most important sections** (e.g., "Relevance Matching" and "Resume Enhancement Output").
""",
    expected_output=""" 
A detailed, professional analysis of the CV's relevance to the job, with clear suggestions for improvement. The output should include:
1. A breakdown of the most relevant projects and skills.
2. Resume-ready bullet points.
3. A final section with tailored suggestions for improvement (e.g., adding measurable outcomes, improving documentation, including more relevant skills).
""",
    agent=cv_analyzer_agent,
    context=[analyze_jd_task, extract_employer_data_task],
    output_file="D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output_profile.txt",
)
    

    # Run all crews sequentially
    print("\n🔹 Job Description Analysis Results 🔹")
    crew1 = Crew(
        agents=[jd_analyzer_agent],
        tasks=[analyze_jd_task],
        process=Process.sequential,
        llm=groq_llm
    )
    results1 = crew1.kickoff(inputs={"job_description": job_description})
    print(results1)

    print("\n🔹 Extracted Technical Requirements & Company Info 🔹")
    crew2 = Crew(
        agents=[employer_data_extraction_agent],
        tasks=[extract_employer_data_task],
        process=Process.sequential,
        llm=groq_llm
    )
    results2 = crew2.kickoff(inputs={"company_name": company_name, "job_description": job_description})
    print(results2)

    print("\n🔹 GitHub-Based Resume Insight Report 🔹")
    crew3 = Crew(
        agents=[github_analyzer_agent],
        tasks=[analyze_github_task],
        process=Process.sequential,
        llm=openai_llm
    )
    results3 = crew3.kickoff(inputs={"github_profile": github_profile, "company_name": company_name, "job_description": job_description})
    print(results3)

    print("\n🔹 Resume Fit & Tailoring Report 🔹")
    crew4 = Crew(
        agents=[cv_analyzer_agent],
        tasks=[cv_analysis_task],
        process=Process.sequential,
        llm=groq_llm
    )
    results4 = crew4.kickoff(inputs={"job_description": job_description, "company_name": company_name, "candidate_cv": candidate_cv})
    print(results4)

if __name__ == "__main__":
    main()