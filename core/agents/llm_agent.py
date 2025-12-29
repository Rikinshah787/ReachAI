import os
from groq import Groq
from dotenv import load_dotenv
from agents.templates import EmailTemplates

load_dotenv()

class LLMAgent:
    """
    Uses role-specific templates with AI-generated subject lines
    """
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"

    def generate_email(self, recruiter_info, user_bio=None, template_key=None):
        """
        Generate email using pre-written template with AI subject line
        
        Args:
            recruiter_info: Dict with recruiter details
            user_bio: Not used (templates have built-in content)
            template_key: Optional template override
            
        Returns:
            Dict with 'subject', 'body', 'template_used', 'template_name'
        """
        # Auto-select template if not specified
        if not template_key:
            template_key = EmailTemplates.select_template(recruiter_info)
        
        template_data = EmailTemplates.get_template(template_key)
        
        # Format the pre-written template (plain text)
        body_text = EmailTemplates.format_email(template_key, recruiter_info)
        
        # Convert plain text to professional HTML
        try:
            from utils.html_formatter import text_to_html_email, format_email_links
            body_html = text_to_html_email(body_text, template_key)
            body_html = format_email_links(body_html)
            body = body_html
        except Exception as e:
            # Fallback to plain text if HTML formatting fails
            print(f"HTML formatting failed: {e}")
            body = body_text
        
        # Generate subject line with AI
        subject = self._generate_subject(recruiter_info, template_key)
        
        return {
            'subject': subject,
            'body': body,
            'template_used': template_key,
            'template_name': template_data['name'],
            'resume': template_data.get('resume')
        }

    def _generate_subject(self, recruiter_info, template_key):
        """Generate catchy subject line using AI"""
        role = recruiter_info.get('role_hiring_for', 'Position')
        company = recruiter_info.get('company', 'Company')
        
        prompt = f"""
        Generate a professional, catchy email subject line for a job application.
        
        Role: {role}
        Company: {company}
        Template Type: {template_key}
        
        Guidelines:
        - Keep it under 60 characters
        - Professional but engaging
        - Include role or key skill
        - No "Application for" or generic phrases
        
        Return ONLY the subject line, no quotes or extra text.
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You output only the subject line, nothing else."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model
            )
            
            subject = chat_completion.choices[0].message.content.strip()
            # Remove quotes if AI added them
            subject = subject.strip('"').strip("'")
            return subject
        except Exception as e:
            # Fallback subject if AI fails
            return f"{role} - Rikin Shah"

if __name__ == "__main__":
    agent = LLMAgent()
    
    # Test different role types
    test_recruiters = [
        {"first_name": "Pawan", "company": "SAP", "role_hiring_for": "SAP Consultant"},
        {"first_name": "David", "company": "OpenAI", "role_hiring_for": "AI Engineer"},
        {"first_name": "Sarah", "company": "Google", "role_hiring_for": "Software Engineer SE3"}
    ]
    
    for recruiter in test_recruiters:
        print(f"\n{'='*60}")
        print(f"Testing: {recruiter['company']} - {recruiter['role_hiring_for']}")
        print(f"{'='*60}")
        result = agent.generate_email(recruiter)
        print(f"Template: {result['template_name']}")
        print(f"Subject: {result['subject']}")
        print(f"Body Preview: {result['body'][:150]}...")
