from crewai import Agent, Task, Crew ,llm    

import os
import warnings
from crewai import Agent, Task, Crew, LLM
from IPython.display import Markdown, display
from bs4 import BeautifulSoup
import requests
import re
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY must be set in your environment or .env file.")

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY must be set in your environment or .env file.")

warnings.filterwarnings("ignore", category=UserWarning)

# Initialize the Groq LLM
groq_llm = LLM(model="groq/llama-3.3-70b-versatile")

with open('d:\\vs code\\ml\\crewAi\\github\\imp codes\\description.txt', 'r') as file:
    # Read the contents of the file
    job_description = file.read()


# Job Description Analyzer Agent
from crewai_tools import FileReadTool



groq_llm = LLM(model="groq/llama-3.3-70b-versatile")
# job_description = input("Paste the job description (or type 'skip' if unavailable): ")

jd_analyzer_agent = Agent(
    role="Senior Job Description Analyst",
    goal=f"Extract structured requirements from job descriptions for precise resume matching for the following jod description{job_description}",
    verbose=True,
    llm=groq_llm,
    backstory="Specializes in decoding complex job descriptions to identify key technical and cultural requirements",
    prompt=f"""
    As a Job Description Analyst, follow this structured approach for the following jod description{job_description}:
    
    1. CHAIN-OF-THOUGHT ANALYSIS:
    - Step 1: Identify REQUIRED skills (explicitly mentioned as mandatory)
    - Step 2: Extract DESIRED skills (marked as 'nice-to-have' or 'preferred')
    - Step 3: List CORE RESPONSIBILITIES (key task bullet points)
    - Step 4: Infer IMPLICIT KEYWORDS (e.g., "cloud environment" → AWS/Azure)
    - Step 5: Determine EXPERIENCE LEVEL (entry/mid/senior)
    
    2. OUTPUT FORMAT:
    Structured detailed points containing:
    
      "required_skills": ["list", "of", "hard", "skills"],
      "desired_skills": ["list"],
      "responsibilities": ["bullet", "points"],
      "keywords": ["relevant", "terms"],
      "experience_level": "level",
      "contradictions": ["any_conflicting_requirements"]
    
    
    3. EDGE CASE HANDLING:
    - EMPTY JD: "Please paste the full job description or type 'skip' to proceed with minimal data"
    - VAGUE JD: "This description seems generic. Could you specify: 1) Top 3 required skills 2) Key tools/technologies?"
    - LANGUAGE DETECTION: "Detected non-English text. Should I attempt translation? (Y/N)"
    - CONTRADICTIONS: "Found conflicting requirements: [X] vs [Y]. Which should take priority?"
    """
)

analyze_jd_task = Task(
    description=f"""Analyze the provided job description with precision for the following jod description{job_description}:
    - Handle vague/insufficient descriptions
    - Detect implicit requirements
    - Flag any inconsistencies
    - Support multi-language input""",
    expected_output="""Structured detailed points containing:
    - Required/desired skills
    - Key responsibilities 
    - Experience level
    - Detected keywords
    - Any flagged issues""",
    agent=jd_analyzer_agent, 
    output_file= "D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output_job.txt"
)

# # # Run CrewAI
# crew = Crew(
#     agents=[jd_analyzer_agent],
#     tasks=[analyze_jd_task],
#     llm=groq_llm
# )
# results = crew.kickoff(inputs={"job_description": job_description})

# print("\n🔹 Job Description Analysis Results 🔹")
# print(results)



with open('d:\\vs code\\ml\\crewAi\\github\\imp codes\\company.txt', 'r') as file:
    # Read the contents of the file
    company_name = file.read()

# print(company_name)






employer_data_extraction_agent = Agent(
    role="Company Intelligence Agent",
    goal=f"Research {company_name}'s tech stack and culture using verified sources",
    verbose=True,
    llm=groq_llm,
    backstory="Specializes in extracting accurate company data from multiple sources to help candidates tailor their applications",
    prompt=f"""As a Company Intelligence Agent, follow this process for this job description {job_description}:
    
    1. SOURCE VERIFICATION:
    - Check the company's official website careers page
    - Search LinkedIn for tech stack mentions
    - Review Crunchbase for industry data
    - Cross-reference at least 2 sources
    
    2. DATA EXTRACTION:
    - Identify primary programming languages and frameworks
    - Note infrastructure tools (AWS/GCP/etc.)
    - Extract cultural keywords from mission statements
    - Determine industry sector
    
    3. OUTPUT FORMAT:
    Structured detailed points containing:
    {{
      "tech_stack": ["list", "of", "technologies"],
      "culture_keywords": ["keywords"],
      "industry": "industry_name",
      "data_sources": ["sources_used"]
    }}
    
    
    EDGE CASE HANDLING:
    - If company is unknown: Ask user "Can you describe their tech stack or share a relevant LinkedIn post?"
    - If ambiguous name (e.g., 'Delta'): Request clarification "Please specify industry/location (e.g., Delta Airlines)"
    - If typos detected: Suggest correction "Did you mean [corrected_name]?"
    - If no data found: "No public data found. Using JD keywords as fallback"
    """
)

extract_employer_data_task = Task(
    description=f"""Extract comprehensive technical and cultural information about {company_name}, for te related job description {job_description}. 
    Handle these scenarios:
    - New startups with limited online presence
    - Companies with common names
    - Potential typos in company name
    Return structured, actionable data for resume tailoring.""",
    expected_output="""Structured detailed points containing:
    - Verified tech stack
    - Cultural attributes
    - Industry classification
    - Sources used
    With proper handling of edge cases""",
    agent=employer_data_extraction_agent,
    output_file= "D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output_company.txt",
    context = [analyze_jd_task]
)

# Run Crew AI
# crew = Crew(
#     agents=[employer_data_extraction_agent], 
#     tasks=[extract_employer_data_task], 
#     llm=groq_llm
# )
# results = crew.kickoff(inputs= {"company_name": company_name})

# print("\n🔹 Extracted Technical Requirements & Company Info 🔹")
# print(results)



with open('refined_output_github_llm.txt', 'r') as file:
    # Read the contents of the file
    github_profile = file.read()

# print(github_profile)



# Enhanced GitHub Analyzer Agent
os.environ["GEMINI_API_KEY"] = "AIzaSyAspAmAiOfwPOClk9oW_FqNp__qtUbBahs"
openai_llm = LLM(
    model="openai/gpt-4o-mini", # call model by provider/model_name

)



github_analyzer_agent = Agent(
    role="Senior GitHub Profile Analyst",
    goal=f"Comprehensively analyze {github_profile}'s GitHub profile to extract resume-worthy technical qualifications and project achievements",
    verbose=True,
    llm=openai_llm,
    backstory=(
        "A technical recruitment specialist with 10+ years experience analyzing developer profiles. "
        "Expert in identifying meaningful patterns in GitHub activity that correlate with professional "
        "software engineering competencies. Known for distinguishing between superficial and substantial "
        "contributions."
    ),
    prompt="""
    # GitHub Profile Analysis Protocol
    
    ## Phase 1: Data Ingestion & Validation
    1. Verify profile exists and has public repositories
    2. Classify repositories by:
       - Original projects vs forks
       - Personal vs organizational
       - Active vs archived
    3. Filter out:
       - Tutorial/example repositories
       - Empty/boilerplate projects
       - Incomplete migrations
    
    ## Phase 2: Technical Skills Analysis
    ### Language Proficiency:
    - Calculate language distribution across all original repos
    - Identify primary languages (>30% of code)
    - Note secondary languages (appearing in multiple projects)
    - Detect language combinations (e.g., Python + C++ for ML)
    
    ### Tech Stack Reconstruction:
    For each significant project (>500 LOC or active >6 months):
    1. Parse dependency files (requirements.txt, package.json, etc.)
    2. Identify:
       - Core frameworks (Django, React, etc.)
       - Database technologies
       - Testing frameworks
       - Build tools
    3. Note architectural patterns:
       - Microservices
       - API design (REST/GraphQL)
       - Cloud integration
    
    ### Infrastructure Skills:
    - Containerization (Docker files)
    - Orchestration (k8s manifests)
    - IaC (Terraform files)
    - CI/CD pipelines
    
    ## Phase 3: Project Evaluation
    For each notable project (pinned or >3 contributors):
    1. Analyze commit history:
       - Main development periods
       - Maintenance activity
       - Bug fix vs feature commit ratio
    2. Evaluate collaboration:
       - PR review patterns
       - Issue resolution time
       - Community engagement
    3. Assess documentation:
       - README completeness (0-5 scale):
         1. Project purpose
         2. Installation
         3. Usage examples
         4. Contribution guidelines
         5. License
       - Wiki presence
       - API documentation
    
    ## Phase 4: Activity Assessment
    1. Contribution timeline analysis:
       - Active months in last year
       - Streaks of activity
       - Current engagement level
    2. Code quality indicators:
       - Presence of linters
       - Test coverage mentions
       - Code review practices
    3. Community impact:
       - Stars/forks per original project
       - External contributors
       - Dependency usage
    
    ## Output Specification
    Structured detailed points containing

**Technical Profile**

**Language Proficiency:**
- Primary Language:
  - Python – Used extensively in project1 and project2
- Secondary Languages:
  - JavaScript, SQL
- Language Combinations:
  - Frequently combines Python and JavaScript in full-stack projects

**Tech Stack:**
- Frontend: React, Redux
- Backend: Django, FastAPI
- Databases: PostgreSQL, MongoDB
- DevOps: Docker, AWS ECS

---

**Project Highlights**

Project: project-name  
- Role: Creator / Maintainer / Contributor  
- Duration: 6 months  
- Technical Highlights:
  - Implemented JWT authentication
  - Optimized database queries, reducing response time by 40%
- Collaboration:
  - Team size: 3
  - Contributions: Led API development, Reviewed PRs
- Impact:
  - GitHub Stars: 15
  - Forks: 3
  - External users: Yes

---

**Activity Analysis**

- Consistency: Regular contributor (10+ commits per month)
- Recency: Active within the last month
- Engagement:
  - Issues Opened: 12
  - Issues Closed: 8
  - Pull Requests: 15

---

**Documentation Quality**

- Average README Score: 4.2 out of 5
- Best Documented Project: project-name
- Improvement Opportunities:
  - Add more usage examples
  - Include architecture diagrams

---

**Recommendations**

**Profile Improvements:**
- Pin the most technical projects to the GitHub profile
- Add clear and consistent project tags

**Resume Highlights:**
- Full-stack experience with Django and React
- Proven track record of maintaining production systems


    
    ## Edge Case Handling Guide
    1. Sparse Profiles:
    - If <3 original repos: "Focus on quality over quantity. Expand documentation for existing projects."
    - If only forks: "Consider adding original projects or documenting significant fork modifications."
    
    2. Inconsistent Activity:
    - Gaps >6 months: "Highlight specific skills rather than timeline. Focus on project depth."
    
    3. Common Issues:
    - Poor documentation: "Suggest README template with sections: Problem Solved, Tech Stack, Installation"
    - No tests: "Recommend adding even basic pytest examples"
    - No CI/CD: "Suggest simple GitHub Actions starter workflow"
    
    4. Name Ambiguity:
    - Multiple matches: "Verify profile URL. Current analysis for: [username]"
    """
)

analyze_github_task = Task(
    description=f"""Conduct in-depth technical analysis of {github_profile}'s GitHub profile to:
    1. Identify all resume-worthy technical qualifications
    2. Extract measurable project achievements
    3. Evaluate collaboration and maintenance patterns
    4. Assess code quality and documentation standards
    5. Generate specific profile improvement recommendations
    6. Provide tailored suggestions for resume presentation
    
    Special Considerations:
    - Differentiate between hobby and professional-grade projects
    - Detect skills transferable to target job roles
    - Identify hidden competencies (e.g., DevOps from deployment files)
    - Highlight open-source contributions
    """,
    expected_output="""Comprehensive technical Structured detailed points containing:
    1. Detailed technical skills matrix
    2. Annotated project portfolio
    3. Quantitative activity metrics
    4. Documentation quality assessment
    5. Actionable improvement suggestions
    6. Ready-to-use resume bullet points
    
    With professional handling of:
    - Sparse profiles
    - Inconsistent activity
    - Common quality issues
    - Profile ambiguity""",
    agent=github_analyzer_agent,
    output_file= "D:\\vs code\\ml\\crewAi\\github\\imp codes\\agent_output_github.txt",
    context = [analyze_jd_task, extract_employer_data_task]
    
)

# Run Enhanced Analysis
crew = Crew(
    agents=[jd_analyzer_agent, github_analyzer_agent, employer_data_extraction_agent],
    tasks=[analyze_jd_task, extract_employer_data_task, analyze_github_task],
    llm=groq_llm,
    process="sequential"  # For thorough analysis
)
github_results = crew.kickoff(inputs= {"github_profile": github_profile,
"company_name": company_name,
"job_description": job_description})

print("\n🔹 Comprehensive GitHub Analysis Report 🔹")
print(github_results)