"""
HTML Email Template Formatter
Converts plain text email templates to professional HTML format
"""

def text_to_html_email(body_text, template_name="general"):
    """
    Convert plain text email body to professional HTML format
    
    Args:
        body_text: Plain text email content
        template_name: Type of template (sap_consultant, ai_genai, software_engineer, general)
    
    Returns:
        HTML formatted email string
    """
    
    # Subtle, professional colors that look human-written
    colors = {
        "sap_consultant": {"primary": "#1e3a8a"},
        "ai_genai": {"primary": "#1e293b"},
        "software_engineer": {"primary": "#1e3a8a"},
        "general": {"primary": "#1e3a8a"}
    }
    
    color_scheme = colors.get(template_name, colors["general"])
    
    # Split into paragraphs
    paragraphs = body_text.strip().split('\n\n')
    
    html_parts = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Check if it's a bullet list
        if '•' in para or para.startswith('- '):
            # Convert to HTML list
            lines = para.split('\n')
            html_parts.append('<ul style="margin: 15px 0; padding-left: 20px;">')
            for line in lines:
                line = line.strip()
                if line.startswith('•') or line.startswith('-'):
                    # Remove bullet and create list item
                    content = line.lstrip('•-').strip()
                    # Make first few words bold if they contain ':'
                    if ':' in content:
                        parts = content.split(':', 1)
                        content = f'<strong>{parts[0]}:</strong>{parts[1]}'
                    html_parts.append(f'<li style="margin: 8px 0;">{content}</li>')
            html_parts.append('</ul>')
        else:
            # Regular paragraph - make certain keywords highlighted
            para = para.replace('\n', '<br>')
            html_parts.append(f'<p style="margin: 12px 0; line-height: 1.6;">{para}</p>')
    
    body_html = '\n'.join(html_parts)
    
    # Build complete HTML email - minimal styling, looks human-written
    html_template = f"""<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
            color: #1f2937;
            line-height: 1.65;
            margin: 0;
            padding: 20px;
        }}
        .email-container {{
            max-width: 650px;
            margin: 0 auto;
        }}
        .email-body {{
            padding: 0;
        }}
        .content {{
            font-size: 15px;
            color: #1f2937;
        }}
        p {{
            margin: 14px 0;
            line-height: 1.65;
        }}
        .signature {{
            margin-top: 25px;
            padding-top: 0;
            border-top: none;
        }}
        .signature-name {{
            font-weight: 400;
            color: #1f2937;
            font-size: 15px;
            margin-bottom: 4px;
        }}
        .contact-info {{
            font-size: 14px;
            color: #6b7280;
            line-height: 1.6;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            margin: 14px 0;
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
            line-height: 1.65;
            color: #1f2937;
        }}
        strong {{
            font-weight: 600;
            color: #111827;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-body">
            <div class="content">
                {body_html}
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return html_template


def format_email_links(html_text):
    """Convert plain text URLs and emails to clickable links"""
    import re
    
    # Convert URLs
    url_pattern = r'(https?://[^\s<>"]+)'
    html_text = re.sub(url_pattern, r'<a href="\1">\1</a>', html_text)
    
    # Convert email addresses (not already in links)
    email_pattern = r'(?<!href=")([\w\.-]+@[\w\.-]+\.\w+)'
    html_text = re.sub(email_pattern, r'<a href="mailto:\1">\1</a>', html_text)
    
    return html_text
