from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import markdown
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from html.parser import HTMLParser

class MarkdownToReportlab:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        self.story = []

    def _create_custom_styles(self):
        custom = {
            'Heading1': ParagraphStyle(
                'Heading1',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            ),
            'Heading2': ParagraphStyle(
                'Heading2',
                parent=self.styles['Heading2'],
                fontSize=18,
                spaceBefore=20,
                spaceAfter=10
            ),
            'Heading3': ParagraphStyle(
                'Heading3',
                parent=self.styles['Heading3'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=self.styles['Normal'],
                fontSize=11,
                leading=14
            ),
            'Code': ParagraphStyle(
                'Code',
                parent=self.styles['Code'],
                fontName='Courier',
                fontSize=9,
                leading=12,
                backColor=colors.lightgrey
            )
        }
        return custom

    def _process_html_element(self, element):
        if isinstance(element, str):
            if element.strip():
                self.story.append(Paragraph(element, self.custom_styles['Normal']))
            return

        tag = element.name

        if tag in ['h1', 'h2', 'h3']:
            style = self.custom_styles[f'Heading{tag[1]}']
            self.story.append(Paragraph(element.get_text(), style))
            self.story.append(Spacer(1, 12))

        elif tag == 'p':
            self.story.append(Paragraph(str(element), self.custom_styles['Normal']))
            self.story.append(Spacer(1, 12))

        elif tag == 'pre':
            code_text = element.get_text()
            self.story.append(Paragraph(code_text, self.custom_styles['Code']))
            self.story.append(Spacer(1, 12))

        elif tag == 'table':
            rows = []
            for tr in element.find_all('tr'):
                row = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                rows.append(row)

            if rows:
                table = Table(rows)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                self.story.append(table)
                self.story.append(Spacer(1, 12))

        elif tag == 'blockquote':
            quote_style = ParagraphStyle(
                'Quote',
                parent=self.custom_styles['Normal'],
                leftIndent=30,
                textColor=colors.darkgrey
            )
            self.story.append(Paragraph(element.get_text(), quote_style))
            self.story.append(Spacer(1, 12))

        else:
            for child in element.children:
                if child.name or child.strip():
                    self._process_html_element(child)

def convert_markdown_to_pdf(markdown_file, output_file=None):
    """Convert a markdown file to PDF using reportlab.
    
    Args:
        markdown_file (str): Path to the markdown file
        output_file (str, optional): Path for the output PDF file
    
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Validate input file
        if not os.path.exists(markdown_file):
            raise FileNotFoundError(f"Markdown file not found: {markdown_file}")
            
        # Set output file path if not provided
        if output_file is None:
            output_file = str(Path(markdown_file).with_suffix('.pdf'))
            
        # Read markdown content
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
                'markdown.extensions.nl2br'
            ]
        )

        # Parse HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Convert HTML to PDF elements
        converter = MarkdownToReportlab()
        converter._process_html_element(soup)
        
        # Build PDF
        doc.build(converter.story)
        
        return output_file
        
    except Exception as e:
        print(f"Error converting markdown to PDF: {str(e)}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python markdown_to_pdf_reportlab.py <markdown_file> [output_file]")
        return
        
    markdown_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = convert_markdown_to_pdf(markdown_file, output_file)
    if result:
        print(f"Successfully converted to PDF: {result}")

if __name__ == '__main__':
    main()