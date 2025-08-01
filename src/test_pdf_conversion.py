import os
from utils.text_to_pdf_converter import convert_text_to_pdf

def test_pdf():
    """
    Tests the PDF conversion functionality.
    """
    print("Testing PDF conversion...")
    # Use the last generated resume as input
    input_file = '../output/agent_resume_iter_3.txt'
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    pdf_path = convert_text_to_pdf(input_text_file=input_file)

    if pdf_path:
        print(f"✅ PDF conversion successful. PDF generated at: {pdf_path}")
    else:
        print("❌ PDF conversion failed.")

if __name__ == '__main__':
    test_pdf()