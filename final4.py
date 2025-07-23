import os
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required environment variables
if not os.getenv("GROQ_API_KEY") or not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("GROQ_API_KEY and OPENAI_API_KEY must be set in your environment or .env file.")

# Initialize LLMs
groq_llm = LLM(model="groq/llama-3.3-70b-versatile")
openai_llm = LLM(model="openai/gpt-4o-mini")

def run_final4_processing(job_description_file, company_file, github_profile_file, candidate_cv_file):
    """Runs the agent processing pipeline from final4.py.

    Args:
        job_description_file (str): Path to the job description text file.
        company_file (str): Path to the company name text file.
        github_profile_file (str): Path to the refined GitHub profile text file.
        candidate_cv_file (str): Path to the candidate's CV text file (e.g., portfolio.txt).

    Returns:
        dict: A dictionary containing the paths to the generated output files.
              Keys: 'jd_output', 'company_output', 'github_output', 'cv_output'
    """
    try:
        # Load Job Description
        with open(job_description_file, 'r', encoding='utf-8') as file:
            job_description = file.read()

        # Load Company Name
        with open(company_file, 'r', encoding='utf-8') as file:
            company_name = file.read().strip()

        # Load GitHub Profile
        with open(github_profile_file, 'r', encoding='utf-8') as file:
            github_profile = file.read()

        # Load Candidate CV
        with open(candidate_cv_file, 'r', encoding='utf-8') as file:
            candidate_cv = file.read()
    except FileNotFoundError as e:
        print(f"Error loading input file: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while loading input files: {e}")
        return None

    # Define output file paths (using absolute paths for clarity)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jd_output_file = os.path.join(current_dir, 'agent_output__jd.txt')
    company_output_file = os.path.join(current_dir, 'agent_output_company.txt')
    github_output_file = os.path.join(current_dir, 'agent_output_github.txt')
    cv_output_file = os.path.join(current_dir, 'agent_output_profile.txt')

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
        1. ✅ **Core Responsibilities**: Write out the major tasks this role will handle, with explanations — not just bullet points.
        2. ✅ **Required Technical Skills**: Mention each mandatory skill and explain its context in this role.
        3. ✅ **Preferred Skills / Tools**: Highlight optional or preferred tech stacks or experience areas.
        4. ✅ **Experience Level**: Estimate if the job is entry, mid, or senior based on wording and requirements.
        5. ✅ **Soft Skills & Cultural Expectations**: Mention if they’re seeking leadership, collaboration, communication, etc.
        6. ✅ **Domain/Industry Specificity**: Point out if it's FinTech, HealthTech, B2B SaaS, etc.
        7. ✅ **Implicit Expectations**: Infer hidden requirements. For example, if \"fast-paced\" is mentioned, note that it's likely a startup.
        8. ✅ **Any Contradictions or Confusions**: If any responsibilities or requirements seem conflicting, explain them.
        9. ✅ **Remote/On-Site Flexibility**: If mentioned, what does it imply about their work culture?
        10. ✅ **Company Values or Mission (if present)**: Comment on any signs of values/culture, diversity, or inclusion.
        💡 **Write this in clear paragraph form, with headers for each section. Avoid lists or JSON.**
        End your analysis with:
        - ✅ \"Overall Impression\": What kind of candidate would be a strong fit?
        - ❗ \"Missing Info\": Mention if any critical info is missing (like salary, tech versioning, team size, etc.)
        """,
        expected_output="A structured multi-paragraph natural language analysis that reads like a consultant's breakdown of the JD.",
        agent=jd_analyzer_agent,
        output_file=jd_output_file
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
        📝 The job description is:
        ---
        {job_description}
        ---
        Your analysis must include:
        ---
        ### 1. CHAIN-OF-VERIFICATION
        - Visit the **official careers page** of {company_name}.
        - Search **LinkedIn company profile**.
        - Search for {company_name} on **Crunchbase** and AngelList (if a startup).
        - Check GitHub/StackOverflow (if available) for tech mentions.
        - Cross-check at least 2–3 sources and **cite them clearly** (with URLs or notes).
        ---
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
        ---
        ### 3. EDGE CASE HANDLING
        - Ambiguous name? Ask: \"Delta Airlines or Delta Electronics?\"
        - No data? Fallback to JD and infer stack/tools
        - Name typo? Suggest closest valid matches
        🧠 End with a paragraph giving overall impression of the company from a job-seeker's lens.
        """,
        expected_output="Detailed paragraph-based breakdown of company data and how it ties to the job description. Include sources used and resume tailoring tips.",
        agent=employer_data_extraction_agent,
        output_file=company_output_file,
        context=[analyze_jd_task]
    )

    # GitHub Analyzer Agent & Task
    github_analyzer_agent = Agent(
        role="Targeted GitHub Profile Analyst",
        goal=f"Analyze {github_profile}'s GitHub profile and extract insights relevant to the job at {company_name}",
        verbose=True,
        llm=openai_llm,
        backstory=(
            f"You're a senior technical recruiter and GitHub analyst with expertise in translating GitHub activity into career-relevant achievements. "
            f"You understand what companies like {company_name} care about and can match a developer's GitHub activity to role-specific requirements."
        )
    )
    analyze_github_task = Task(
        description=f"""
        You are analyzing the GitHub profile provided in the input file to determine how well it aligns with a specific job at **{company_name}**.
        You’ve already reviewed the job description and company profile. Use that context to:
        ---
        ### 🔍 Phase 1: Repo Selection
        - Prioritize original repos (exclude forks and tutorials).
        - Select 3–5 **relevant** repos showing job-related technologies.
        - Consider:
          - Tech stack mentioned in JD (Python, React, Docker, etc.)
          - Projects demonstrating DevOps, API design, frontend/backend, etc.
          - Project maturity (stars, forks, recency, maintenance)
        ---
        ### 🧠 Phase 2: Analysis Per Project
        For each project selected:
        - Project summary & tech stack
        - Your role (creator, contributor, etc.)
        - Key achievements (performance, architecture, automation, etc.)
        - Collaboration: PRs, issues, contributions
        - Documentation quality (README + extras)
        - Infra: Docker, GitHub Actions, k8s, etc.
        ---
        ### 🧩 Phase 3: Match Against JD
        - Which JD-required skills are evident?
        - Are any *missing* or only partially demonstrated?
        - What areas should be **emphasized in resume**?
        - What **improvements** could make the GitHub profile more job-ready?
        ---
        ### 📝 Output Format
        - Paragraph-style analysis report
        - Final section:  
        **🔧 Resume Highlights Based on GitHub**  
        Include 4–6 bullet points the candidate can paste into a resume.
        ---
        Handle edge cases:
        - Sparse profile: focus on depth
        - Inactive repo: mention what’s still useful
        - Name confusion: clarify who is being analyzed
        Cite project links in markdown where possible.
        """,
        expected_output="A recruiter-style paragraph breakdown of technical qualifications and project alignment with the target job, plus resume suggestions.",
        agent=github_analyzer_agent,
        context=[analyze_jd_task, extract_employer_data_task],
        output_file=github_output_file
    )

    # CV Analyzer Agent & Task
    cv_analyzer_agent = Agent(
        role="Resume Intelligence Analyst",
        goal=f"Analyze the candidate's CV and extract the most relevant projects, skills, and achievements tailored for a role at {company_name}",
        verbose=True,
        llm=openai_llm,
        backstory=(
            f"You're a senior talent intelligence analyst with deep expertise in matching resumes to job descriptions. "
            f"You're skilled at parsing resumes to identify impactful achievements and aligning them with specific role requirements. "
            f"You act like a hiring manager's secret weapon for filtering out top-tier, job-ready candidates."
        )
    )
    cv_analysis_task = Task(
        description=f"""
        You are reviewing a candidate's resume ({candidate_cv_file}) to assess **fit for a job at {company_name}**.
        --- 
        📝 Job Description Context (from previous analysis):
        {analyze_jd_task.output}
        --- 
        🏢 Company Context (from previous analysis):
        {extract_employer_data_task.output}
        --- 
        🧑‍💻 GitHub Context (from previous analysis):
        {analyze_github_task.output}
        --- 
        📄 Candidate's CV:
        {candidate_cv}
        --- 
        Your task is to:
        1.  **Extract Key Information**: Identify core skills, years of experience, key projects, quantifiable achievements, and education.
        2.  **Align with Job Requirements**: Compare the extracted info against the job description analysis. Highlight matches and gaps.
        3.  **Align with Company Context**: Does the CV reflect the company's tech stack, culture, or industry focus?
        4.  **Integrate GitHub Insights**: Does the CV corroborate or contradict the GitHub analysis? Are the suggested GitHub highlights present?
        5.  **Identify Strengths & Weaknesses**: Based on the job/company, what are the candidate's strongest selling points and areas needing improvement?
        6.  **Suggest Resume Enhancements**: Provide 3-5 specific, actionable suggestions for tailoring the CV *better* for this specific role (e.g., "Quantify achievement X," "Add keyword Y related to Z skill," "Rephrase project description to highlight A").
        
        **Output Format:**
        - Write a concise, paragraph-based analysis covering points 1-5.
        - Conclude with a bulleted list under the heading: **✨ Recommended CV Enhancements for {company_name} Role**
        
        Handle edge cases:
        - Missing CV: State clearly that the CV is missing.
        - Poorly formatted CV: Note the difficulty in parsing and focus on what *can* be extracted.
        - Contradictions: Point out discrepancies between CV, GitHub, and JD.
        """,
        expected_output="A concise analysis of the candidate's CV against the job/company context, highlighting strengths, weaknesses, and specific tailoring suggestions.",
        agent=cv_analyzer_agent,
        context=[analyze_jd_task, extract_employer_data_task, analyze_github_task],
        output_file=cv_output_file
    )

    # Define the Crew
    job_application_crew = Crew(
        agents=[jd_analyzer_agent, employer_data_extraction_agent, github_analyzer_agent, cv_analyzer_agent],
        tasks=[analyze_jd_task, extract_employer_data_task, analyze_github_task, cv_analysis_task],
        process=Process.sequential,
        llm=groq_llm
    )

    # Execute the Crew
    print("\n🚀 Starting Agent Processing Pipeline...")
    try:
        result = job_application_crew.kickoff()
        print("\n✅ Agent Processing Pipeline Completed.")
        print("\n📊 Final Result:")
        print(result)

        # Verify output files were created
        output_files = {
            'jd_output': jd_output_file,
            'company_output': company_output_file,
            'github_output': github_output_file,
            'cv_output': cv_output_file
        }
        for key, path in output_files.items():
            if not os.path.exists(path):
                print(f"Warning: Output file {key} not found at {path}")
                # Potentially return None or raise an error if files are critical
            else:
                print(f"Output file {key} generated at: {path}")
        
        return output_files

    except Exception as e:
        print(f"\n❌ An error occurred during agent processing: {e}")
        # Consider logging the full traceback for debugging
        # import traceback
        # print(traceback.format_exc())
        return None

# Example usage (optional, for testing the function directly)
if __name__ == '__main__':
    # Define dummy input file paths for testing
    # Ensure these files exist or create them with sample content
    test_jd_file = 'd:\vs code\ml\crewAi\github\imp codes\description.txt'
    test_company_file = 'd:\vs code\ml\crewAi\github\imp codes\company.txt'
    test_github_file = 'd:\vs code\ml\crewAi\github\imp codes\refined_output_github_llm.txt'
    test_cv_file = 'd:\vs code\ml\crewAi\github\imp codes\portfolio.txt' # Assuming portfolio.txt is the CV

    # Create dummy files if they don't exist for the test run
    for f_path in [test_jd_file, test_company_file, test_github_file, test_cv_file]:
        if not os.path.exists(f_path):
            print(f"Creating dummy file: {f_path}")
            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(f"Sample content for {os.path.basename(f_path)}")

    print("Running final4 processing directly for testing...")
    output_paths = run_final4_processing(test_jd_file, test_company_file, test_github_file, test_cv_file)

    if output_paths:
        print("\nFunction executed successfully. Output file paths:")
        for key, path in output_paths.items():
            print(f"- {key}: {path}")
    else:
        print("\nFunction execution failed.")