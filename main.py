import os
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv
import logging
from core.agents.data_agent import DataAgent
from core.agents.llm_agent import LLMAgent
from core.agents.email_agent import EmailAgent
from core.agents.audit_agent import AuditAgent
from core.agents.inbox_agent import InboxAgent

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Orchestrator")

def is_business_hours():
    """Check if current time is within business hours (using config)"""
    try:
        from core.utils.config import load_schedule_config
        config = load_schedule_config()
        
        business_only = config.get("business_hours_only", False)
        if not business_only:
            return True
        
        now = datetime.now()
        start_hour = int(config.get("start_hour", 9))
        end_hour = int(config.get("end_hour", 17))
        
        return start_hour <= now.hour < end_hour
    except Exception as e:
        logger.warning(f"Error checking business hours config: {e}")
        # Fallback to env vars or default
        return True

def run_outreach_pipeline(csv_path, bio, test_mode=False, delay=30, resume_path=None, limit=None, force=False):
    load_dotenv()
    
    # Initialize Team
    data_agent = DataAgent(csv_path)
    llm_agent = LLMAgent()
    email_agent = EmailAgent()
    audit_agent = AuditAgent()
    inbox_agent = InboxAgent()
    
    # Get resume path from env if not provided
    if not resume_path:
        resume_path = os.getenv("RESUME_PATH")
    
    logger.info("🚀 Starting Recruiter Outreach Pipeline...")
    if test_mode:
        logger.info("⚠️  TEST MODE: No emails will be sent")
    
    if force:
        logger.info("⚡ FORCE MODE: Bypassing business hours checks")
    
    # Check for replies first (skip if disabled for faster testing)
    skip_inbox = os.getenv("SKIP_INBOX_CHECK", "false").lower() == "true"
    if not skip_inbox:
        logger.info("📬 Checking inbox for replies...")
        try:
            replied_emails = inbox_agent.check_for_replies()
            for email in replied_emails:
                audit_agent.mark_as_replied(email)
                logger.info(f"✅ Marked {email} as REPLIED")
        except Exception as e:
            logger.warning(f"⚠️  Inbox check failed (continuing anyway): {e}")
    else:
        logger.info("⏭️  Skipping inbox check (SKIP_INBOX_CHECK=true)")
    
    # 1. Ingest Data
    try:
        recruiters = data_agent.load_data()
        logger.info(f"📊 Loaded {len(recruiters)} recruiter records")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        return

    # 2. Process each recruiter
    sent_count = 0
    skipped_count = 0
    
    for idx, recruiter in enumerate(recruiters, 1):
        recipient = recruiter['email']
        company = recruiter['company']
        
        # Skip if already contacted
        if audit_agent.has_been_contacted(recipient):
            logger.info(f"⏭️  Skipping {recipient} (already contacted)")
            skipped_count += 1
            continue
        
        # Check business hours (skip if forced)
        if not force and not is_business_hours():
            logger.warning("⏰ Outside business hours. Pausing pipeline.")
            break
        
        logger.info(f"📧 [{idx}/{len(recruiters)}] Processing {recipient} from {company}...")
        
        # 2a. Generate Personalization
        try:
            draft = llm_agent.generate_email(recruiter, bio)
            subject = draft['subject']
            body = draft['body']
            template_used = draft.get('template_used', 'unknown')
            template_name = draft.get('template_name', 'Unknown')
            
            # Get resume from template
            attachment = resume_path  # Default to global
            template_resume = draft.get('resume')
            
            if template_resume:
                # Handle relative paths (assume in data/ folder if simple filename)
                if not os.path.isabs(template_resume) and '/' not in template_resume and '\\' not in template_resume:
                    attachment = os.path.join('data', template_resume)
                else:
                    attachment = template_resume
            
            logger.info(f"✍️  Generated email with template: {template_name}")
            logger.info(f"   Subject: {subject}")
            logger.info(f"   Attachment: {attachment}")
        except Exception as e:
            logger.error(f"LLM Generation failed for {recipient}: {e}")
            audit_agent.log_result(recipient, company, "FAILED_LLM", error=str(e))
            continue

        # 2b. Send Email (or simulate in test mode)
        if test_mode:
            logger.info(f"🧪 TEST MODE: Would send to {recipient}")
            logger.info(f"   Body Preview: {body[:100]}...")
            if attachment:
                logger.info(f"   Attachment: {attachment}")
            audit_agent.log_result(recipient, company, "TEST", subject=subject, has_attachment=bool(attachment), template_used=template_used)
            sent_count += 1
        else:
            success = email_agent.send_email(recipient, subject, body, attachment_path=attachment)
            
            # 2c. Log & Audit
            if success:
                audit_agent.log_result(recipient, company, "SENT", subject=subject, has_attachment=bool(attachment), template_used=template_used)
                logger.info(f"✅ Sent to {recipient}")
                sent_count += 1
            else:
                audit_agent.log_result(recipient, company, "FAILED_SEND", subject=subject, template_used=template_used)
                logger.error(f"❌ Failed to send to {recipient}")
        
        # 2d. Rate limiting delay
        if idx < len(recruiters) and (sent_count < limit if limit else True):
            logger.info(f"⏳ Waiting {delay} seconds before next email...")
            time.sleep(delay)
            
        # Check Batch Limit
        if limit and sent_count >= limit:
            logger.info(f"🛑 Batch limit of {limit} reached. Stopping.")
            break

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Pipeline Execution Complete!")
    logger.info(f"   Sent: {sent_count}")
    logger.info(f"   Skipped: {skipped_count}")
    logger.info(f"   Total Processed: {len(recruiters)}")
    logger.info(f"{'='*60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Recruiter Outreach System")
    parser.add_argument("--csv", default="data/recruiters.csv", help="Path to recruiters CSV")
    parser.add_argument("--bio", default="Senior Software Engineer targeting AI/ML roles...", help="Your professional bio/context")
    parser.add_argument("--test", action="store_true", help="Test mode (no emails sent)")
    parser.add_argument("--force", action="store_true", help="Bypass business hours checks")
    parser.add_argument("--delay", type=int, default=30, help="Delay between emails in seconds")
    parser.add_argument("--resume", help="Path to resume file (overrides .env)")
    parser.add_argument("--limit", type=int, help="Limit number of emails to send (Batch Size)")
    
    args = parser.parse_args()
    
    run_outreach_pipeline(
        csv_path=args.csv,
        bio=args.bio,
        test_mode=args.test,
        delay=args.delay,
        resume_path=args.resume,
        limit=args.limit,
        force=args.force
    )
