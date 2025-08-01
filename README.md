# Adversarial Multi-Agent Framework for AI-Driven Resume Optimization Using Crewai

This project presents a sophisticated AI system composed of multiple intelligent agents designed to generate highly tailored and optimized resumes. By leveraging a multi-agent architecture, advanced prompt engineering techniques, and an adversarial feedback loop, this framework helps users create resumes that are not only ATS-compliant but also perfectly aligned with specific job descriptions and company cultures.

## Overview

In today's competitive job market, a generic resume is not enough. This project tackles the challenge of resume personalization by creating an intelligent pipeline that analyzes a candidate's profile (CV, GitHub), a target job description, and company details to produce a superior, customized resume.

The system employs a series of specialized AI agents, each with a distinct role, from parsing job requirements to analyzing a candidate's portfolio and generating impactful, STAR-formatted bullet points. The core of the system is an adversarial loop between a **Resume Builder Agent** and an **ATS Checker Agent**, which iteratively refines the resume to achieve a high ATS score and strong keyword alignment.

## Key Features

- **Multi-Agent Architecture**: A team of specialized AI agents work together to handle different aspects of resume creation, from data extraction to content generation and evaluation.
- **Adversarial Feedback Loop**: An innovative generative-evaluative loop between the Resume Builder and ATS Checker agents ensures continuous improvement and optimization of the resume.
- **Advanced Prompt Engineering**: Utilizes a variety of prompt engineering strategies, including Chain of Thought (CoT), Step-Back Reasoning, and Chain of Verification (CoV), to enhance the reasoning and output quality of the LLMs.
- **Deep Profile Analysis**: Goes beyond simple keyword matching by analyzing GitHub repositories, company culture, and the candidate's existing CV to create a holistic profile.
- **ATS Compliance and Optimization**: Generates resumes that are rich in relevant keywords and formatted to pass through modern Applicant Tracking Systems.
- **Interactive Streamlit UI**: A user-friendly web interface for easy input of information and visualization of the final generated resume.
- **Secure and Organized**: The project is structured for clarity and maintainability, with all sensitive information like API keys managed through a `.env` file.

## System Architecture

The system is designed as a modular, multi-agent pipeline that takes four key inputs from the user:
1.  **Job Description**: The description of the job the user is applying for.
2.  **Company Name**: The name of the company.
3.  **GitHub Profile**: The user's GitHub username or profile URL.
4.  **Existing CV**: The user's current CV in PDF or TXT format.

The pipeline consists of the following agents:

- **Agent 1: Job Description Parser**: Extracts key responsibilities, skills, and requirements from the job description.
- **Agent 2: Employer Data Extractor**: Gathers information about the company's culture, values, and tech stack from public sources.
- **Agent 3: GitHub Profile Analyzer**: Analyzes the user's GitHub profile to identify key projects, technologies used, and contributions.
- **Agent 4: Portfolio Analyzer**: Synthesizes the information from the CV and GitHub to create a comprehensive profile of the candidate.
- **Agent 5: Resume Builder**: Generates the resume content, including impactful, STAR-formatted bullet points, based on the analyzed data.
- **Agent 6: ATS Checker**: Evaluates the generated resume for ATS compliance, keyword density, and overall quality, providing feedback for refinement.
- **Conditional Input Agent**: Checks for missing or insufficient input data and prompts the user for more information if needed.

## Technical Stack

- **Backend**: Python
- **AI Framework**: CrewAI
- **LLMs**: OpenAI GPT-4.1 (or other models like Groq Llama)
- **Frontend**: Streamlit
- **PDF Processing**: PyPDF2, ReportLab
- **Web Scraping**: BeautifulSoup
- **Dependencies**: See `requirements.txt` for a full list of dependencies.

## Prompt Engineering Strategies

To maximize the effectiveness of the LLMs, this project employs several advanced prompt engineering techniques:

- **Chain of Thought (CoT)**: Used to break down complex tasks like job description analysis into a series of intermediate reasoning steps.
- **Step-Back Reasoning**: Allows agents to self-critique and refine their generated content.
- **Self-Consistency**: Ensures that the output from the agents is logically coherent and consistent.
- **Chain of Verification (CoV)**: Used to validate information scraped from public sources about the company.

## Project Structure

The project is organized into the following directory structure:

- `src/`: Contains the main source code for the application.
  - `main.py`: The main script to orchestrate the entire resume generation workflow (can be run as a standalone script).
  - `streamlit_app.py`: The Streamlit web interface.
  - `agents/`: Contains the scripts defining the AI agents (`final4.py`, `next_agent.py`).
  - `utils/`: Contains utility scripts for tasks like PDF conversion, web scraping, and input validation.
- `data/`: Stores the input data files provided by the user.
- `output/`: Stores the generated output files, including the final resume PDF and intermediate text files.
- `knowledge/`: Contains the knowledge base used by the AI agents.
- `requirements.txt`: A list of all the Python dependencies for this project.
- `.env`: For storing API keys and other sensitive information.

## Setup and Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Set up the Environment**:
    - Create a virtual environment:
      ```bash
      python -m venv venv
      ```
    - Activate the virtual environment:
      ```bash
      venv\Scripts\activate
      ```
    - Install the required dependencies:
      ```bash
      pip install -r requirements.txt
      ```
3.  **Provide API Keys**:
    - Create a `.env` file in the root of the project.
    - Add your OpenAI API key to the `.env` file:
      ```
      OPENAI_API_KEY="YOUR_API_KEY_HERE"
      ```

## How to Run

- Start the Streamlit app:
  ```bash
  streamlit run src/streamlit_app.py
  ```
- Fill in the required information in the web interface and click "Process Application".
- Once the initial processing is complete, a "Generate Resume" button will appear. Click it to run the full `crewai` pipeline.
- The final, tailored resume will be displayed in the app and saved as `output/resume.pdf`.

## Future Work

- **Real-time Job Market Data Integration**: Integrate with APIs from platforms like LinkedIn or Glassdoor to provide real-time suggestions based on market trends.
- **Multilingual Support**: Extend the system to support languages other than English.
- **Advanced Personalization**: Implement adaptive learning agents that tailor their feedback based on the user's career level.
- **Collaborative Module**: Add a feature for mentors, peers, or recruiters to comment on and co-edit resumes in real-time.

## Authors

- P Kavya Samhitha
- Piyush Sahoo
- Pratyush Tripathi

## Acknowledgments

We would like to express our sincere gratitude to our faculty guide, Dr. Pooja Agarwal, for her invaluable guidance, insights, and support throughout the course of this project.
