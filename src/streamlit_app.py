import streamlit as st
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to make imp_codes accessible
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
imp_codes_dir = current_dir  # Define imp_codes_dir as the current directory
sys.path.append(parent_dir)

from utils.input_validator import InputValidator
from utils.pdf_to_text import convert_pdf_to_text
from utils.github_scraper_new import get_user_repositories, get_repo_data, save_to_text
from utils.github_refiner_llm import read_github_data, parse_repositories, analyze_repository_with_llm, format_output
from agents.final4 import run_final4_processing
from agents.next_agent import run_next_agent_processing

# Initialize session state variables if they don't exist
if 'validator' not in st.session_state:
    st.session_state.validator = InputValidator()
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'cv_text_path' not in st.session_state:
    st.session_state.cv_text_path = None
if 'github_output_file' not in st.session_state:
    st.session_state.github_output_file = None
if 'refined_output_file' not in st.session_state:
    st.session_state.refined_output_file = None
if 'job_description_file' not in st.session_state:
    st.session_state.job_description_file = None

# Set page title and description
st.title('Job Application Input Manager')
st.write('Please provide the following information for job application processing:')

# Create form for input collection
with st.form('input_form'):
    # Job Description input
    st.subheader('1. Job Description')
    job_description = st.text_area(
        'Enter job description or type "na" if not available',
        help='Paste your job description here. Type "na" to skip.'
    )

    # Company Name input
    st.subheader('2. Company Name')
    company_name = st.text_input(
        'Enter company name',
        help='Company name is required'
    )

    # GitHub Profile input
    st.subheader('3. GitHub Profile')
    github_profile = st.text_input(
        'Enter GitHub username or profile URL',
        help='Enter your GitHub username, profile URL, or "na" to skip'
    )

    # CV File upload
    st.subheader('4. CV Upload')
    cv_file = st.file_uploader(
        'Upload your CV (PDF or TXT file)',
        type=['pdf', 'txt'],
        help='Upload your CV in PDF or TXT format, or skip this step'
    )

    # Submit button
    submitted = st.form_submit_button('Process Application')

# Handle form submission
if submitted:
    # Validate and process inputs
    validator = st.session_state.validator
    
    # Validate job description
    if not job_description.strip() and job_description.lower() != 'na':
        st.error('Please provide a job description or enter "na".')
    else:
        validator.inputs['job_description'] = job_description
        # Save job description to file
        if job_description.lower() != 'na':
            job_description_file = os.path.join('data', 'description.txt')
            with open(job_description_file, 'w', encoding='utf-8') as file:
                file.write(job_description)
            st.session_state.job_description_file = job_description_file
            st.success('Job description saved successfully!')

    # Validate company name
    if not company_name.strip():
        st.error('Company name is required.')
    else:
        validator.inputs['company_name'] = company_name
        # Save company name to file
        company_file = os.path.join('data', 'company.txt')
        with open(company_file, 'w', encoding='utf-8') as file:
            file.write(company_name)
        st.success('Company name saved successfully!')

    # Validate GitHub profile
    if github_profile.strip():
        if validator.validate_github_profile(github_profile):
            validator.inputs['github_profile'] = github_profile
            
            # Process GitHub data if not 'na'
            if github_profile.lower() != 'na':
                with st.spinner('Processing GitHub profile...'):
                    try:
                        # Extract username
                        if 'github.com' in github_profile:
                            username = github_profile.split('/')[-1]
                        else:
                            username = github_profile

                        # Fetch repositories
                        repositories = get_user_repositories(username)
                        if repositories:
                            # Get repository data
                            all_repo_data = []
                            for repo_url in repositories:
                                repo_data = get_repo_data(repo_url)
                                if repo_data:
                                    all_repo_data.append(repo_data)

                            if all_repo_data:
                                # Save GitHub data
                                github_output_file = os.path.join('data', 'output_github.txt')
                                save_to_text(all_repo_data, github_output_file)
                                st.session_state.github_output_file = github_output_file

                                # Refine GitHub data
                                content = read_github_data(github_output_file)
                                parsed_repos = parse_repositories(content)
                                enhanced_repositories = []
                                for repo in parsed_repos:
                                    enhanced_repo = analyze_repository_with_llm(repo)
                                    enhanced_repositories.append(enhanced_repo)

                                refined_output_file = os.path.join('data', 'refined_output_github_llm.txt')
                                formatted_output = format_output(enhanced_repositories)
                                with open(refined_output_file, 'w', encoding='utf-8') as file:
                                    file.write(formatted_output)
                                st.session_state.refined_output_file = refined_output_file
                                st.success('GitHub profile processed successfully!')
                    except Exception as e:
                        st.error(f'Error processing GitHub profile: {str(e)}')
        else:
            st.error('Please provide a valid GitHub username or profile URL.')

    # Process CV file if uploaded
    if cv_file is not None:
        with st.spinner('Processing CV...'):
            try:
                # Save uploaded file
                file_path = os.path.join('data', cv_file.name)
                with open(file_path, 'wb') as f:
                    f.write(cv_file.getbuffer())

                # Validate and process CV
                if validator.validate_cv_file(file_path):
                    validator.inputs['personal_cv'] = cv_file.name
                    validator.cv_file_path = file_path

                    # Convert PDF to text if necessary
                    if file_path.lower().endswith('.pdf'):
                        cv_text_path = convert_pdf_to_text(file_path)
                        if cv_text_path:
                            st.session_state.cv_text_path = cv_text_path
                            st.success('CV processed successfully!')
                        else:
                            st.error('Failed to convert CV to text.')
                    else:
                        st.session_state.cv_text_path = file_path
                        st.success('CV processed successfully!')
                else:
                    st.error('Please upload a valid PDF or TXT file.')
            except Exception as e:
                st.error(f'Error processing CV: {str(e)}')
    else:
        validator.inputs['personal_cv'] = 'na'

    # Mark processing as complete if all required fields are valid
    if all(value is not None for value in validator.inputs.values()):
        st.session_state.processing_complete = True

# Display results if processing is complete
if st.session_state.processing_complete:
    st.subheader('Processing Results')
    
    # Display processed data locations
    if st.session_state.cv_text_path:
        st.write(f'📄 CV text version: {st.session_state.cv_text_path}')
        with open(st.session_state.cv_text_path, 'r', encoding='utf-8') as file:
            st.text_area('CV Content', file.read(), height=200)

    if st.session_state.github_output_file:
        st.write(f'📊 GitHub repository analysis: {st.session_state.github_output_file}')
        with open(st.session_state.github_output_file, 'r', encoding='utf-8') as file:
            st.text_area('GitHub Analysis', file.read(), height=200)

    if st.session_state.refined_output_file:
        st.write(f'🔍 Refined GitHub analysis: {st.session_state.refined_output_file}')
        with open(st.session_state.refined_output_file, 'r', encoding='utf-8') as file:
            st.text_area('Refined GitHub Analysis', file.read(), height=200)

    # Display collected inputs in JSON format
    st.subheader('Collected Data (JSON format)')
    st.json(st.session_state.validator.inputs)

    if st.button('Generate Resume'):
        with st.spinner('Running the resume generation pipeline...'):
            final4_outputs = run_final4_processing(
                job_description_file=st.session_state.job_description_file,
                company_file=os.path.join('data', 'company.txt'),
                github_profile_file=st.session_state.refined_output_file,
                candidate_cv_file=st.session_state.cv_text_path
            )

            if final4_outputs:
                final_resume_file = run_next_agent_processing(final4_outputs)
                if final_resume_file:
                    with open(final_resume_file, 'r', encoding='utf-8') as file:
                        st.text_area('Final Resume', file.read(), height=600)
                else:
                    st.error('Resume generation failed.')
            else:
                st.error('Initial analysis failed.')