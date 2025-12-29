import imaplib
import email
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class InboxAgent:
    """
    Monitors the ASU/Gmail inbox for replies from recruiters.
    """
    def __init__(self):
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.email_user = os.getenv("SMTP_EMAIL")
        self.email_pass = os.getenv("SMTP_PASSWORD")

    def check_for_replies(self):
        """
        Scans the inbox for emails from recruiters already in our logs.
        Returns a list of email addresses that have replied.
        """
        replied_emails = []
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            # Search for all unread messages
            # Note: In a real scenario, you'd filter by sender email from your CSV
            status, messages = mail.search(None, 'UNSEEN')
            
            if status == "OK":
                for num in messages[0].split():
                    status, data = mail.fetch(num, '(RFC822)')
                    msg = email.message_from_bytes(data[0][1])
                    
                    # Get sender address
                    from_email = email.utils.parseaddr(msg['From'])[1]
                    replied_emails.append(from_email)
            
            mail.close()
            mail.logout()
            return list(set(replied_emails)) # Unique senders
            
        except Exception as e:
            logger.error(f"IMAP monitoring failed: {e}")
            return []

if __name__ == "__main__":
    agent = InboxAgent()
    print("Checking for new replies...")
    replies = agent.check_for_replies()
    print(f"Emails with new replies: {replies}")
