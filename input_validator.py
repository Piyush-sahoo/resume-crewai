import json
import os
import re
from typing import Dict, Optional, Union
from pdf_to_text import convert_pdf_to_text
from github_scraper_new import get_user_repositories, get_repo_data, save_to_text
from github_refiner_llm import read_github_data, parse_repositories, analyze_repository_with_llm, format_output


class InputValidator:
    """Class to validate and collect required inputs for job application processing."""

    def __init__(self):
        """Initialize the validator with empty input fields."""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.inputs = {
            "job_description": None,
            "company_name": None,
            "github_profile": None,
            "personal_cv": None
        }
        self.cv_file_path = None
        self.cv_text_path = None
        self.github_output_file = None
        self.refined_output_file = None

    def validate_github_profile(self, profile: str) -> bool:
        """Validate if the provided string is a valid GitHub profile or link."""
        # Allow 'na' as a valid input
        if profile.lower() == 'na':
            return True
            
        # Check if it's a GitHub URL
        github_url_pattern = r'^https?://(?:www\.)?github\.com/[\w-]+/?.*$'
        # Check if it's just a username (alphanumeric with hyphens)
        github_username_pattern = r'^[\w-]+$'
        
        return bool(re.match(github_url_pattern, profile) or re.match(github_username_pattern, profile))

    def validate_cv_file(self, file_path: str) -> bool:
        """Validate if the provided file exists and is a txt or PDF file."""
        # Allow 'na' as a valid input
        if file_path.lower() == 'na':
            return True
            
        if not os.path.exists(file_path):
            return False
        
        # Check if file is txt or PDF
        return file_path.lower().endswith(('.txt', '.pdf'))

    def collect_inputs(self) -> Dict[str, str]:
        """Collect all required inputs from the user."""
        print("Please provide the following information for job application processing:")
        
        # Collect job description (optional, can be 'na')
        while not self.inputs["job_description"]:
            print("1. Job Description (or 'na' if not available)")
            print("Paste your job description below. Press Enter twice (i.e., leave a blank line) when finished:")
            lines = []
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
            
            job_desc = '\n'.join(lines)
            
            if job_desc.lower() == 'na':
                confirm = input("Are you sure you want to skip the job description? (yes/no): ")
                if confirm.lower() in ['yes', 'y']:
                    self.inputs["job_description"] = "na"
                else:
                    continue
            elif job_desc.strip():
                self.inputs["job_description"] = job_desc
            else:
                print("Job description cannot be empty. Please provide a valid job description or 'na'.")
        
        # Collect company name (required)
        while not self.inputs["company_name"]:
            company = input("2. Company Name: ")
            if company.strip():
                self.inputs["company_name"] = company
            else:
                print("Company name cannot be empty. Please provide a valid company name.")
        
        # Collect GitHub profile
        while not self.inputs["github_profile"]:
            github = input("3. GitHub Profile or Link: ")
            if github.strip() and self.validate_github_profile(github):
                if github.lower() == 'na':
                    self.inputs["github_profile"] = "na"
                else:
                    # Extract username and process GitHub data immediately
                    if re.match(r'^https?://(?:www\.)?github\.com/([\w-]+)/?.*$', github):
                        username = re.match(r'^https?://(?:www\.)?github\.com/([\w-]+)/?.*$', github).group(1)
                    else:
                        username = github
                    
                    self.inputs["github_profile"] = f"github.com/{username}"
                    print(f"\nFetching GitHub repositories for {username}...")
                    
                    # Process GitHub data
                    repositories = get_user_repositories(username)
                    if not repositories:
                        print("No repositories found or error occurred while fetching repositories.")
                        continue

                    # Get repository data and save to file
                    all_repo_data = []
                    for repo_url in repositories:
                        repo_data = get_repo_data(repo_url)
                        if repo_data:
                            all_repo_data.append(repo_data)

                    if not all_repo_data:
                        print("Failed to fetch repository data.")
                        continue

                    self.github_output_file = os.path.join(self.script_dir, "output_github.txt")
                    save_to_text(all_repo_data, self.github_output_file)

                    # Refine GitHub data using LLM
                    print("\nAnalyzing GitHub repositories using LLM...")
                    content = read_github_data(self.github_output_file)
                    parsed_repos = parse_repositories(content)

                    enhanced_repositories = []
                    for repo in parsed_repos:
                        enhanced_repo = analyze_repository_with_llm(repo)
                        enhanced_repositories.append(enhanced_repo)

                    self.refined_output_file = os.path.join(self.script_dir, "refined_output_github_llm.txt")
                    formatted_output = format_output(enhanced_repositories)
                    with open(self.refined_output_file, 'w', encoding='utf-8') as file:
                        file.write(formatted_output)
                    print(f"GitHub analysis complete! Results saved to {self.github_output_file} and {self.refined_output_file}")
            else:
                print("Please provide a valid GitHub username or profile URL.")
        
        # Collect personal CV (optional, can be 'na')
        while not self.inputs["personal_cv"]:
            cv_path = input("4. Personal CV (provide file path to .txt or .pdf file, or 'na' if not available): ")
            if cv_path.lower() == 'na':
                self.inputs["personal_cv"] = "na"
                self.cv_file_path = None
            elif cv_path.strip() and self.validate_cv_file(cv_path):
                self.inputs["personal_cv"] = os.path.basename(cv_path)
                self.cv_file_path = cv_path
                # Process CV immediately after validation
                if cv_path.lower().endswith('.pdf'):
                    self.cv_text_path = convert_pdf_to_text(self.cv_file_path)
                    if not self.cv_text_path:
                        print("Failed to convert CV to text. Please check the PDF file.")
                        continue
                    # Ensure cv_text_path is in the same directory
                    self.cv_text_path = os.path.join(self.script_dir, os.path.basename(self.cv_text_path))
                    print(f"CV converted successfully. Text version available at: {self.cv_text_path}")
            else:
                print("Please provide a valid path to a .txt or .pdf CV file or 'na'.")
        
        print("\nAll required inputs have been collected successfully!")
        print("Data is ready for processing.")
        
        return self.inputs

    def to_json(self) -> str:
        """Convert the collected inputs to JSON format."""
        return json.dumps(self.inputs, indent=4)


def main():
    """Main function to run the input validation process."""
    validator = InputValidator()
    validator.collect_inputs()
    
    # Output the collected data in JSON format
    json_output = validator.to_json()
    print("\nCollected Data (JSON format):")
    print(json_output)
    
    return json_output


if __name__ == "__main__":
    main()