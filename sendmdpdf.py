# NO LINE BETWEEN NAME AND CONTACT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
import markdown
import os
from pathlib import Path
from bs4 import BeautifulSoup


class MarkdownToReportlab:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        self.story = []
        self.skip_next_hr = False  # To handle special case between name and contact info

    def _create_custom_styles(self):
        custom = {
            'Heading1': ParagraphStyle('Heading1', parent=self.styles['Heading1'], fontSize=24, spaceAfter=8),
            'Heading2': ParagraphStyle('Heading2', parent=self.styles['Heading2'], fontSize=18, spaceBefore=6, spaceAfter=4),
            'Heading3': ParagraphStyle('Heading3', parent=self.styles['Heading3'], fontSize=14, spaceBefore=4, spaceAfter=2),
            'Normal': ParagraphStyle('CustomNormal', parent=self.styles['Normal'], fontSize=11, leading=12),
            'Code': ParagraphStyle('Code', parent=self.styles['Code'], fontName='Courier', fontSize=9, leading=10, backColor=colors.lightgrey)
        }
        return custom

    def _process_html_element(self, element, parent_tag=None):
        if isinstance(element, str) and element.strip():
            self.story.append(Paragraph(element, self.custom_styles['Normal']))
            return

        tag = element.name

        if tag in ['h1', 'h2', 'h3']:
            style = self.custom_styles[f'Heading{tag[1]}']
            self.story.append(Paragraph(element.get_text(), style))
            self.story.append(Spacer(1, 4))
            if tag == 'h1':
                self.skip_next_hr = True  # Set flag to skip <hr> if it's immediately after <h1>
        elif tag == 'hr':
            if self.skip_next_hr:
                self.skip_next_hr = False  # Reset after skipping once
                return
            self.story.append(Spacer(1, 8))
            self.story.append(HRFlowable(color=colors.black, thickness=1, spaceBefore=4, spaceAfter=4, width="100%"))
            self.story.append(Spacer(1, 8))
        elif tag == 'p':
            self.story.append(Paragraph(str(element), self.custom_styles['Normal']))
            self.story.append(Spacer(1, 4))
        elif tag == 'pre':
            self.story.append(Paragraph(element.get_text(), self.custom_styles['Code']))
            self.story.append(Spacer(1, 4))
        elif tag == 'table':
            rows = [[td.get_text().strip() for td in tr.find_all(['td', 'th'])] for tr in element.find_all('tr')]
            if rows:
                table = Table(rows)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                self.story.append(table)
                self.story.append(Spacer(1, 4))
        elif tag == 'blockquote':
            quote_style = ParagraphStyle('Quote', parent=self.custom_styles['Normal'], leftIndent=20, textColor=colors.darkgrey)
            self.story.append(Paragraph(element.get_text(), quote_style))
            self.story.append(Spacer(1, 4))
        else:
            for child in element.children:
                if child.name or (isinstance(child, str) and child.strip()):
                    self._process_html_element(child, parent_tag=tag)


def convert_markdown_to_pdf():
    markdown_file = 'resume.md'
    output_file = str(Path(markdown_file).with_suffix('.pdf'))

    if not os.path.exists(markdown_file):
        raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br'])
    soup = BeautifulSoup(html_content, 'html.parser')

    doc = SimpleDocTemplate(output_file, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)

    converter = MarkdownToReportlab()
    converter._process_html_element(soup)

    doc.build(converter.story)
    print(f"Successfully converted to PDF: {output_file}")


if __name__ == '__main__':
    convert_markdown_to_pdf()
