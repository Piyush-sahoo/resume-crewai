import PyPDF2
import os

def convert_pdf_to_text(pdf_path, output_path=None):
    """Convert a PDF file to text format.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Path for the output text file. 
            If not provided, will use the same name as PDF with .txt extension
    
    Returns:
        str: Path to the created text file
    """
    try:
        # If output path is not provided, create one based on PDF path
        if output_path is None:
            output_path = os.path.splitext(pdf_path)[0] + '.txt'
        
        # Open the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Get total number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from all pages
            with open(output_path, 'w', encoding='utf-8') as text_file:
                for page_num in range(num_pages):
                    # Get the page object
                    page = pdf_reader.pages[page_num]
                    
                    # Extract text from page
                    text = page.extract_text()
                    
                    # Write text to file
                    text_file.write(text)
                    
                    # Add page separator if not the last page
                    if page_num < num_pages - 1:
                        text_file.write('\n\n' + '-'*50 + '\n\n')
            
            return output_path
            
    except FileNotFoundError:
        print(f"Error: The PDF file '{pdf_path}' was not found.")
        return None
    except Exception as e:
        print(f"Error occurred while converting PDF: {str(e)}")
        return None

def main():
    # Example usage
    pdf_path = input("Enter the path to your PDF file: ")
    output_path = input("Enter the output text file path (press Enter to use default): ").strip()
    
    # If no output path provided, pass None to use default
    if not output_path:
        output_path = None
    
    result_path = convert_pdf_to_text(pdf_path, output_path)
    
    if result_path:
        print(f"\nSuccessfully converted PDF to text!")
        print(f"Text file saved at: {result_path}")

if __name__ == "__main__":
    main()