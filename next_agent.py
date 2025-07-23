import os
import warnings
from crewai import Agent, Task, Crew, LLM, Process
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from IPython.display import Markdown, display
import requests
import re
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore", category=UserWarning)
from bs4 import BeautifulSoup

# Initialize LLMs (can be done inside the function if preferred)
groq_llm = LLM(model="groq/llama-3.3-70b-versatile")
openai_llm = LLM(model="openai/gpt-4o-mini")

# Merge text files utility
def merge_text_files(file_list, output_file):
    missing_files = [file for file in file_list if not os.path.exists(file)]
    if missing_files:
        print(f"Error: The following files were not found: {missing_files}")
        return False # Indicate failure
    try:
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
                outfile.write("\n" + "="*40 + "\n") # Separator between files
        print(f"Merged file saved as '{output_file}'")
        return True # Indicate success
    except Exception as e:
        print(f"Error merging files: {e}")
        return False

def run_next_agent_processing(final4_output_paths, knowledgebase_file="knowledgebase.txt", max_iterations=3):
    """Runs the resume building and evaluation agent loop.

    Args:
        final4_output_paths (dict): Dictionary containing paths from run_final4_processing.
                                    Expected keys: 'jd_output', 'company_output', 'github_output', 'cv_output'.
        knowledgebase_file (str): Path to the general knowledgebase file.
        max_iterations (int): Maximum number of refinement iterations.

    Returns:
        str: Path to the final generated resume text file, or None if an error occurs.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    merged_output_file = os.path.join(current_dir, 'merged_output.txt')
    knowledgebase_path = os.path.join(current_dir, 'knowledge', knowledgebase_file)
    final_resume_file = None # Initialize

    # --- 1. Merge Input Files --- 
    input_files_to_merge = [
        final4_output_paths.get('jd_output'),
        final4_output_paths.get('company_output'),
        final4_output_paths.get('github_output'),
        final4_output_paths.get('cv_output')
    ]
    # Filter out None values in case some files weren't generated
    input_files_to_merge = [f for f in input_files_to_merge if f and os.path.exists(f)]

    if not input_files_to_merge:
        print("Error: No valid input files provided from final4 processing.")
        return None

    if not merge_text_files(input_files_to_merge, merged_output_file):
        print("Error: Failed to merge input files.")
        return None

    # --- 2. Setup Knowledge Sources --- 
    knowledge_files = [merged_output_file]
    if os.path.exists(knowledgebase_path):
        knowledge_files.append(knowledgebase_path)
    else:
        print(f"Warning: Knowledgebase file not found at {knowledgebase_path}")

    try:
        text_knowledge = TextFileKnowledgeSource(file_paths=knowledge_files)
    except Exception as e:
        print(f"Error initializing knowledge source: {e}")
        return None

    # --- 3. Define Agents --- 
    resume_builder_agent = Agent(
        role="Senior Resume Builder and Career Strategist",
        goal="Create and refine a resume that is ATS-optimized and aligned with job, company, and technical profile based on provided context.",
        backstory="You're a resume writing expert who knows exactly how to tailor resumes for ATS systems, tech recruiters, and modern roles using the merged context and knowledgebase.",
        llm=openai_llm,
        verbose=True,
        knowledge_sources=[text_knowledge]
    )

    ats_agent = Agent(
        role="ATS Resume Evaluator",
        goal="Evaluate the resume for keyword relevance, technical alignment, formatting, and ATS compatibility based on the provided context. Give feedback to improve it.",
        backstory="You're a top-tier ATS and HR screening specialist who helps candidates refine resumes to perfection based on real hiring systems and the provided context.",
        llm=openai_llm,
        verbose=True,
        knowledge_sources=[text_knowledge]
    )

    # --- 4. Define Tasks (dynamically inside the loop) --- 
    def build_resume_task(resume_draft="", iteration=1):
        output_filename = os.path.join(current_dir, f'agent_resume_iter_{iteration}.txt')
        return Task(
            description=f"""
            Using the merged context (job description, company info, GitHub analysis, CV analysis) and the knowledgebase, generate a tailored resume draft.
            If previous ATS feedback is provided below, incorporate it to improve the resume:
            --- ATS Feedback ---
            {resume_draft if resume_draft else 'No feedback yet.'}
            --- End Feedback ---
            Generate iteration {iteration} of the resume.
            """,
            expected_output="A full resume in plain text following modern formatting. Include Summary, Skills, Projects, Work Experience, Education. Ensure it's well-structured and uses keywords from the context.",
            agent=resume_builder_agent,
            output_file=output_filename
        )

    def evaluate_resume_task(resume_file_path):
        if not os.path.exists(resume_file_path):
             return Task(description="Resume file not found, cannot evaluate.", expected_output="Error message.", agent=ats_agent) # Dummy task
        try:
            with open(resume_file_path, 'r', encoding='utf-8') as f:
                resume_text = f.read()
        except Exception as e:
             return Task(description=f"Error reading resume file {resume_file_path}: {e}", expected_output="Error message.", agent=ats_agent) # Dummy task

        return Task(
            description=f"""
            Evaluate the following resume text (from {os.path.basename(resume_file_path)}) against ATS standards and the job/company requirements found in the merged context and knowledgebase:
            --- Resume Text ---
            {resume_text}
            --- End Resume Text ---

            Provide:
            1. An estimated ATS Score (0-100).
            2. Key missing keywords compared to the context.
            3. Specific suggestions for improving skills, formatting, or content alignment.
            4. An overall verdict on its readiness.
            """,
            expected_output="""
            ATS Score Report including:
            - Score (e.g., 75/100)
            - Keyword analysis (matched vs. missing)
            - Actionable suggestions for improvement
            - Final summary verdict (e.g., 'Needs significant revision', 'Good start, minor tweaks needed', 'Excellent fit')
            """,
            agent=ats_agent
            # No output file for evaluation, result is captured in kickoff() output
        )

    # --- 5. Run Iterative Refinement Crew --- 
    ats_feedback = "" # Start with no feedback
    current_resume_file = "" 

    for i in range(1, max_iterations + 1):
        print(f"\n🔁 Iteration {i} of {max_iterations} - Refining Resume...")
        
        # Create tasks for this iteration
        resume_task = build_resume_task(resume_draft=ats_feedback, iteration=i)
        # Evaluation task needs the *output* of the resume task
        # We'll run resume task first, then create and run eval task

        # Crew for building the resume
        build_crew = Crew(
            agents=[resume_builder_agent],
            tasks=[resume_task],
            process=Process.sequential,
            llm=groq_llm, # Can use a different LLM if needed
            # planning=False # Keep it simple for sequential
        )
        
        try:
            build_result = build_crew.kickoff()
            print(f"Resume Build (Iteration {i}) Result: {build_result}")
            current_resume_file = resume_task.output_file # Get the actual output file path
            if not os.path.exists(current_resume_file):
                 print(f"Error: Resume file {current_resume_file} was not generated in iteration {i}.")
                 break # Exit loop if resume generation failed
            print(f"✅ Resume v{i} saved to: {current_resume_file}")
            final_resume_file = current_resume_file # Update final resume path each iteration

        except Exception as e:
            print(f"Error during resume building (Iteration {i}): {e}")
            break # Exit loop on error

        # Crew for evaluating the generated resume
        eval_task = evaluate_resume_task(resume_file_path=current_resume_file)
        
        # Check if eval_task is valid (not a dummy error task)
        if "Resume file not found" in eval_task.description or "Error reading resume file" in eval_task.description:
            print(f"Skipping evaluation for iteration {i} due to resume file issue.")
            ats_feedback = "Error: Could not read or find resume file for evaluation."
            continue # Proceed to next iteration or finish
            
        evaluate_crew = Crew(
            agents=[ats_agent],
            tasks=[eval_task],
            process=Process.sequential,
            llm=groq_llm, # Can use a different LLM if needed
            # planning=False
        )

        try:
            eval_result = evaluate_crew.kickoff()
            ats_feedback = eval_result.raw if eval_result else "Evaluation failed to produce output."
            print(f"\n📊 ATS Evaluation (Iteration {i}):\n{ats_feedback}")
            
            # Save final ATS report only after the last iteration
            if i == max_iterations:
                ats_report_path = os.path.join(current_dir, "ats_final_report.txt")
                try:
                    with open(ats_report_path, "w", encoding="utf-8") as report:
                        report.write(ats_feedback)
                    print(f"📄 Final ATS report saved to: {ats_report_path}")
                except Exception as e:
                    print(f"Error saving final ATS report: {e}")

        except Exception as e:
            print(f"Error during resume evaluation (Iteration {i}): {e}")
            ats_feedback = f"Error during evaluation: {e}" # Pass error info potentially
            # Decide if you want to break or continue on evaluation error
            # break 

    print("\n🎯 Resume refinement loop completed.")
    
    if final_resume_file and os.path.exists(final_resume_file):
        print(f"Returning final resume file: {final_resume_file}")
        return final_resume_file
    else:
        print("Error: Final resume file was not generated or found.")
        return None

# Example usage (optional, for testing the function directly)
if __name__ == '__main__':
    print("Testing next_agent processing function...")
    # Create dummy output paths from final4 for testing
    # Ensure the dummy files actually exist from the final4 test run or create them here
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_final4_outputs = {
        'jd_output': os.path.join(current_dir, 'agent_output__jd.txt'),
        'company_output': os.path.join(current_dir, 'agent_output_company.txt'),
        'github_output': os.path.join(current_dir, 'agent_output_github.txt'),
        'cv_output': os.path.join(current_dir, 'agent_output_profile.txt')
    }
    dummy_knowledgebase = os.path.join('knowledge', 'knowledgebase.txt') # Relative to current_dir

    # Ensure dummy input files exist
    for key, f_path in dummy_final4_outputs.items():
         if not os.path.exists(f_path):
             print(f"Creating dummy input file for testing: {f_path}")
             os.makedirs(os.path.dirname(f_path), exist_ok=True)
             with open(f_path, 'w', encoding='utf-8') as f:
                 f.write(f"Sample content for {key}")
                 
    # Ensure dummy knowledgebase exists
    kb_path_full = os.path.join(current_dir, dummy_knowledgebase)
    if not os.path.exists(kb_path_full):
        print(f"Creating dummy knowledgebase file for testing: {kb_path_full}")
        os.makedirs(os.path.dirname(kb_path_full), exist_ok=True)
        with open(kb_path_full, 'w', encoding='utf-8') as f:
            f.write("Sample knowledgebase content.")

    final_resume = run_next_agent_processing(dummy_final4_outputs, knowledgebase_file=dummy_knowledgebase, max_iterations=2) # Run fewer iterations for testing

    if final_resume:
        print(f"\n✅ Test run successful. Final resume generated at: {final_resume}")
    else:
        print("\n❌ Test run failed.")