import os
import subprocess

# --- Configuration (can be overridden by function arguments) ---
DEFAULT_INPUT_TEXT_FILE = 'agent_resume3.txt'  # Default if no path provided
DEFAULT_MARKDOWN_OUTPUT_FILE = 'resume.md' # Intermediate Markdown file
DEFAULT_PDF_SCRIPT = 'sendmdpdf.py' # Script for Markdown to PDF

# --- Text to Markdown Conversion (Basic Example) ---
def format_text_to_markdown(text):
    """Converts plain text to a basic Markdown format.
    
    This is a simple example. You might need a more sophisticated
    parser or logic depending on your input text structure.
    Assumes the input text might already have some Markdown-like structure.
    """
    # Basic replacements for structure - adjust as needed
    # This is highly dependent on the output format of next_agent.py
    # If next_agent.py already outputs good Markdown, this function might be simpler.
    lines = text.strip().split('\n')
    markdown_content = ""
    in_code_block = False

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("```"):
            in_code_block = not in_code_block
            markdown_content += line + "\n"
            continue
        
        if in_code_block:
            markdown_content += line + "\n"
            continue

        if stripped_line.startswith("## "):
             markdown_content += "\n" + line + "\n\n" # Add spacing around H2
        elif stripped_line.startswith("### "):
             markdown_content += "\n" + line + "\n\n" # Add spacing around H3
        elif stripped_line.startswith("- ") or stripped_line.startswith("* "):
             markdown_content += line + "\n" # Keep list items tight
        elif stripped_line:
             markdown_content += line + "\n\n" # Treat other non-empty lines as paragraphs
        else:
             markdown_content += "\n" # Preserve blank lines

    return markdown_content.strip()

# --- Main PDF Conversion Function --- 
def convert_text_to_pdf(input_text_file=DEFAULT_INPUT_TEXT_FILE, 
                        markdown_output_file=DEFAULT_MARKDOWN_OUTPUT_FILE, 
                        pdf_script=DEFAULT_PDF_SCRIPT):
    """Converts a text file to PDF via Markdown and an external script.

    Args:
        input_text_file (str): Path to the input text file (e.g., final resume).
        markdown_output_file (str): Path for the intermediate Markdown file.
        pdf_script (str): Path to the Python script that converts Markdown to PDF.

    Returns:
        str: Path to the generated PDF file, or None if conversion fails.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Ensure paths are absolute or relative to the script's directory
    input_text_file_abs = os.path.join(current_dir, input_text_file) if not os.path.isabs(input_text_file) else input_text_file
    markdown_output_file_abs = os.path.join(current_dir, markdown_output_file) if not os.path.isabs(markdown_output_file) else markdown_output_file
    pdf_script_abs = os.path.join(current_dir, pdf_script) if not os.path.isabs(pdf_script) else pdf_script
    pdf_output_file = os.path.splitext(markdown_output_file_abs)[0] + '.pdf'

    # 1. Read the input text
    try:
        with open(input_text_file_abs, 'r', encoding='utf-8') as f:
            plain_text = f.read()
        print(f"Successfully read text from '{input_text_file_abs}'.")
    except FileNotFoundError:
        print(f"Error: Input file '{input_text_file_abs}' not found.")
        return None
    except Exception as e:
        print(f"Error reading input file '{input_text_file_abs}': {e}")
        return None

    # 2. Convert text to Markdown (optional, if input isn't already Markdown)
    # If agent_resumeX.txt is already good Markdown, you might skip/simplify this.
    markdown_output = format_text_to_markdown(plain_text)
    # markdown_output = plain_text # Use this if input is already Markdown
    print("Formatted text to Markdown.")

    # 3. Write Markdown to the intermediate file
    try:
        with open(markdown_output_file_abs, 'w', encoding='utf-8') as f:
            f.write(markdown_output)
        print(f"Successfully wrote Markdown to '{markdown_output_file_abs}'.")
    except Exception as e:
        print(f"Error writing Markdown file '{markdown_output_file_abs}': {e}")
        return None

    # 4. Run the PDF conversion script
    print(f"\nRunning the PDF conversion script: {pdf_script_abs}...")
    try:
        # Ensure the script exists
        if not os.path.exists(pdf_script_abs):
             print(f"Error: PDF script '{pdf_script_abs}' not found.")
             return None
             
        # Run the script in the directory where it resides to handle relative paths within it
        script_dir = os.path.dirname(pdf_script_abs)
        result = subprocess.run(['python', os.path.basename(pdf_script_abs)], 
                                capture_output=True, text=True, check=True, 
                                encoding='utf-8', cwd=script_dir)
                                
        print("--- PDF Script Output ---")
        print(result.stdout)
        if result.stderr:
            print("--- PDF Script Errors ---")
            print(result.stderr)
        print("-------------------------")
        print(f"Successfully executed {os.path.basename(pdf_script_abs)}.")
        
        # Check if the expected PDF was created
        if os.path.exists(pdf_output_file):
            print(f"PDF generated: {pdf_output_file}")
            return pdf_output_file
        else:
            print(f"Error: PDF file '{pdf_output_file}' was not found after script execution.")
            print(f"Check the output/errors of '{os.path.basename(pdf_script_abs)}' above.")
            return None
            
    except FileNotFoundError:
        print(f"Error: 'python' command not found. Make sure Python is installed and in your PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error executing {os.path.basename(pdf_script_abs)}:")
        print("--- Error Output --- (stdout)")
        print(e.stdout)
        print("--- Error Output --- (stderr)")
        print(e.stderr)
        print("--------------------")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while running the PDF script: {e}")
        return None

# --- Main Execution (for testing) ---
if __name__ == '__main__':
    print("Testing PDF conversion function...")
    # Create a dummy input file if default doesn't exist
    if not os.path.exists(DEFAULT_INPUT_TEXT_FILE):
        print(f"Creating dummy input file: {DEFAULT_INPUT_TEXT_FILE}")
        try:
            with open(DEFAULT_INPUT_TEXT_FILE, 'w', encoding='utf-8') as f:
                f.write("# Test Resume\n\n## Section 1\n\n- Point 1\n- Point 2\n\nSome paragraph text.")
        except Exception as e:
            print(f"Failed to create dummy file: {e}")

    # Ensure the PDF script exists (provide a basic dummy if needed for testing)
    if not os.path.exists(DEFAULT_PDF_SCRIPT):
        print(f"Creating dummy PDF script: {DEFAULT_PDF_SCRIPT}")
        try:
            with open(DEFAULT_PDF_SCRIPT, 'w', encoding='utf-8') as f:
                f.write("import sys, os\nprint(f'Dummy PDF script running.')\n")
                f.write("md_file = 'resume.md'\npdf_file = 'resume.pdf'\n")
                f.write("if os.path.exists(md_file):\n")
                f.write("    try:\n")
                f.write("        with open(pdf_file, 'w') as pf: pf.write('Dummy PDF content')\n")
                f.write("        print(f'Created dummy PDF: {pdf_file}')\n")
                f.write("    except Exception as e: print(f'Dummy script error: {e}'); sys.exit(1)\n")
                f.write("else: print(f'Markdown file {md_file} not found.'); sys.exit(1)\n")
        except Exception as e:
            print(f"Failed to create dummy PDF script: {e}")

    # Run the conversion
    pdf_path = convert_text_to_pdf()

    if pdf_path:
        print(f"\n✅ Test successful. PDF generated at: {pdf_path}")
    else:
        print("\n❌ Test failed.")