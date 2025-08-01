import re
from typing import List, Dict
from openai import OpenAI  # Changed from groq
import os
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY must be set in your environment or .env file.")

# Initialize OpenAI client (Ensure OPENAI_API_KEY is set in your .env file)
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

def read_github_data(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def parse_repositories(content: str) -> List[Dict]:
    repositories = []
    repo_sections = content.split('==========\n\n')
    
    for section in repo_sections:
        if not section.strip():
            continue
            
        repo_data = {}
        lines = section.strip().split('\n')
        
        for line in lines:
            if line.startswith('Repository: '):
                repo_data['name'] = line.replace('Repository: ', '').strip()
            elif line.startswith('URL: '):
                repo_data['url'] = line.replace('URL: ', '').strip()
            elif line.startswith('README Content:'):
                readme_start = lines.index(line)
                readme_content = '\n'.join(lines[readme_start + 1:])
                repo_data['readme'] = readme_content.strip()
        
        if repo_data:
            repositories.append(repo_data)
    
    return repositories

def analyze_repository_with_llm(repo_data: Dict) -> Dict:
    """Use OpenAI's gpt-4o-mini to analyze repository content and generate insights."""  # Updated docstring
    prompt = f"""Analyze this GitHub repository and provide key insights:

Repository Name: {repo_data['name']}
Repository URL: {repo_data['url']}

README Content:
{repo_data['readme'][:2000]}  # Limit README to 2000 chars to stay within context window

Provide a concise analysis covering:
1. Main purpose and key features
2. Technical stack and technologies used
3. Project significance and potential applications
4. Code quality indicators (based on README structure and documentation)

Format the response in markdown."""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # Changed model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )

    repo_data['llm_analysis'] = completion.choices[0].message.content
    return repo_data

def format_output(repositories: List[Dict]) -> str:
    output = []
    output.append('# Enhanced GitHub Repository Analysis\n')
    
    for repo in repositories:
        if not repo.get('readme') or repo['readme'] == 'No Readme':
            continue
            
        output.append(f"## {repo['name']}")
        output.append(f"Repository URL: {repo['url']}\n")
        
        # Add LLM analysis
        if repo.get('llm_analysis'):
            output.append(repo['llm_analysis'])
        
        output.append('\n---\n')
    
    return '\n'.join(output)

def main():
    input_file = 'd:/vs code/ml/crewAi/github/output_github.txt'
    output_file = 'd:/vs code/ml/crewAi/github/refined_output_github_llm.txt'
    
    # Read and parse the input file
    content = read_github_data(input_file)
    repositories = parse_repositories(content)
    
    # Analyze each repository using LLM
    enhanced_repositories = []
    for repo in repositories:
        enhanced_repo = analyze_repository_with_llm(repo)
        enhanced_repositories.append(enhanced_repo)
    
    # Format and write the output
    formatted_output = format_output(enhanced_repositories)
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(formatted_output)

if __name__ == '__main__':
    main()