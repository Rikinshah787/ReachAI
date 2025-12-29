"""
Email Templates for ReachAI Recruiter Outreach
Role-specific templates with actual professional experience
"""

class EmailTemplates:
    """
    Manages role-specific email templates with real professional content
    """
    
    # User's professional details
    USER_INFO = {
        "name": "Rikin Shah",
        "email": "rshah88@asu.edu",
        "phone": "(917)-238-5682",
        "credentials": "MS, CSM, SAP",
        "linkedin": "https://linkedin.com/in/rikin-shah",
        "portfolio": "https://pawan-rikin.vercel.app/",
        "github": "https://github.com/Rikinshah787"
    }
    
    TEMPLATES = {
        "sap_consultant": {
            "name": "SAP Specialist",
            "role_keywords": ["sap", "consultant", "erp", "bw", "hana", "bods", "s/4", "abap"],
            "template": """Greetings {recruiter_name},

I hope this email finds you well. My name is Rikin Shah, and I am reaching out regarding the {role} position at {company}. With a Master's in IT from Arizona State University, a Certified Scrum Master (CSM) certification, and extensive hands-on experience in SAP BODS, BW4/HANA, and Analytics, I am confident I can contribute significant value to your team.

Over the past several years, I have:
• Led end-to-end SAP ERP implementations at Deloitte Consulting, supporting SAP (ABAP, BW, BW/4HANA, Datasphere, S/4 HANA). My involvement ranged from requirements gathering and data modeling to project delivery.
• Developed and optimized critical reporting and analytics solutions using BW, HANA, Tableau, and BusinessObjects. I have experience designing scalable ETL pipelines in SAP BODS and creating dynamic dashboards for OTC and financial processes.
• Utilized EDI, ALE/IDocs, BAPIs, and RFCs for seamless system integration.
• Supported functional and technical enhancements in fast-paced environments, collaborating closely with business stakeholders to deliver timely solutions and ongoing production support.

I would love to connect to discuss how my skills align with {company}'s current needs. Attached, please find my resume for your review.

Best regards,

Rikin Shah, MS, CSM, SAP
rshah88@asu.edu | {phone}
{linkedin}"""
        },
        
        "ai_genai": {
            "name": "AI/GenAI Engineer",
            "role_keywords": ["ai", "genai", "machine learning", "llm", "automation", "agentic", "nlp", "vision"],
            "template": """Hi {recruiter_name},

I'm Rikin Shah, and I've been following {company}'s work for some time. I'm reaching out regarding the {role} position or potential opportunities in the AI/Automation space.

My background includes work at Deloitte as a Data Analyst and a Master's from ASU. Recently, I've pivoted strictly into the GenAI space, building agentic AI workflow systems. A few highlights:
• OrchestrateIQ: An IBM Watson Hackathon winner delivering agentic automation across HR, Sales, and Finance (https://ibm-aiorch-u5vh.vercel.app/).
• Wildflower Coalition: A dynamic blog platform with integrated AI-driven admin tools.
• Tech Stack: I live in Cursor and n8n, leveraging LangChain, Crew.ai, AWS Bedrock, and various LLMs to build autonomous agents that drive business impact.

I don't just "use" AI—I build systems that leverage it for real-world innovation. I would love to discuss how I can help {company} stay at the forefront of this space.

My resume is attached. Are you available for a brief conversation this week?

Best,

Rikin Shah
rshah88@asu.edu | {phone}
{portfolio}"""
        },
        
        "software_engineer": {
            "name": "Software Engineer",
            "role_keywords": ["software engineer", "developer", "full-stack", "backend", "frontend", "se3", "python", "react", "node"],
            "template": """Hi {recruiter_name},

I'm reaching out regarding the {role} position at {company}. With a Master's in IT from ASU and hands-on experience across the full stack (Python, React, Node.js), I believe I'd be a strong fit for your technical team.

Throughout my career, I've focused on building robust, scalable systems:
• Developed enterprise-grade SAP implementations at Deloitte.
• Built modern web applications with React/Next.js and Node.js.
• Recently focused on integrating AI capabilities into standard software workflows (SaaS/B2B).
• Experience with cloud-native architectures and database design (SQL/NoSQL).

I thrive in environments that move fast and value clean, maintainable code. I'm passionate about the intersection of classical software engineering and modern AI capabilities.

I've attached my resume and would love the chance to connect for a quick call.

Best regards,

Rikin Shah
rshah88@asu.edu | {phone}
{github}"""
        },
        
        "general": {
            "name": "General Professional",
            "role_keywords": [],
            "template": """Hi {recruiter_name},

I hope your week is going well.

I'm Rikin Shah, reaching out about the {role} position at {company}. With a Master's in IT from Arizona State University and a career that spans Deloitte consulting, project management, and automated systems development, I bring a unique blend of technical expertise and business strategy.

My experience includes leading large-scale SAP implementations, building full-stack web applications, and most recently, developing autonomous AI agents. I am adaptive, quick to learn, and focused on delivering high-quality results.

I've attached my resume for your review. I would welcome the opportunity to discuss how my background aligns with your team's goals.

Best regards,

Rikin Shah
rshah88@asu.edu | {phone}
{linkedin}"""
        }
    }
    @classmethod
    def _load_templates(cls):
        """Load templates merging defaults with custom config"""
        try:
            from utils.config import load_template_config
            config = load_template_config()
            
            if not config:
                return cls.TEMPLATES
            
            # Create a copy to merge into
            import copy
            templates = copy.deepcopy(cls.TEMPLATES)
            
            for key, data in config.items():
                if key == 'custom_template':
                    # Special case: 'custom_template' overwrites 'general'
                    if isinstance(data, str): # Handle old format string or new format object
                         templates['general']['template'] = data
                    elif isinstance(data, dict) and 'custom_template' in data:
                         templates['general']['template'] = data['custom_template']
                    elif isinstance(data, dict) and 'template' in data:
                         templates['general']['template'] = data['template']
                elif key in templates:
                    if 'custom_template' in data:
                        templates[key]['template'] = data['custom_template']
                    if 'resume' in data:
                        templates[key]['resume'] = data['resume']
            return templates
        except Exception as e:
            print(f"Error loading template config: {e}")
            return cls.TEMPLATES

    @classmethod
    def select_template(cls, recruiter_info):
        """Selects the best template based on recruiter's role/company"""
        role = str(recruiter_info.get('role_hiring_for', '')).lower()
        company = str(recruiter_info.get('company', '')).lower()
        
        # Load current templates
        templates = cls._load_templates()
        
        # Check specific templates first
        for key, data in templates.items():
            if key == 'general': continue
            
            # Check keywords
            for keyword in data.get('role_keywords', []):
                if keyword in role or keyword in company:
                    return key
                    
        return "general"

    @classmethod
    def get_template(cls, key):
        """Get template data by key"""
        templates = cls._load_templates()
        return templates.get(key, templates["general"])
    
    @staticmethod
    def format_email(template_key, recruiter_info):
        """
        Format email template with recruiter info and user links
        """
        template_data = EmailTemplates.get_template(template_key)
        template_text = template_data['template']
        
        return template_text.format(
            recruiter_name=recruiter_info.get('first_name', 'there'),
            company=recruiter_info.get('company', 'your company'),
            role=recruiter_info.get('role_hiring_for', 'the position'),
            phone=EmailTemplates.USER_INFO['phone'],
            linkedin=EmailTemplates.USER_INFO['linkedin'],
            portfolio=EmailTemplates.USER_INFO['portfolio'],
            github=EmailTemplates.USER_INFO['github']
        )
