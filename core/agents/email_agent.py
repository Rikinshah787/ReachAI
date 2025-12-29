import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import logging

load_dotenv()

class EmailAgent:
    """
    Sends emails via SMTP and manages communication.
    """
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.password = os.getenv("SMTP_PASSWORD")
        self.sender_name = os.getenv("SENDER_NAME")

    def send_email(self, recipient_email, subject, body, attachment_path=None):
        try:
            # Create a multipart message
            msg = MIMEMultipart('mixed')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Create the body part
            msg_body = MIMEMultipart('alternative')
            
            # 1. Plain text version (strip HTML if needed or just use as is if simple)
            # For robust stripping we'd use BeautifulSoup, but for now assuming body might be HTML
            # We'll send the raw body as HTML and a simple version as text
            
            # Simple strip tags for plain text (rudimentary)
            import re
            plain_text = re.sub('<[^<]+?>', '', body)
            
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(body, 'html')

            # Attach parts into message body
            # According to RFC 2046, the last part of a multipart/alternative is the preferred one
            msg_body.attach(part1)
            msg_body.attach(part2)
            
            msg.attach(msg_body)

            # Attach resume if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(attachment_path)
                    part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                    msg.attach(part)
                    logging.info(f"Attached resume: {filename}")

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.password)
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Email successfully sent to {recipient_email}")
            return True
        except Exception as e:
            logging.error(f"Failed to send email to {recipient_email}: {e}")
            return False

if __name__ == "__main__":
    # Test logic (Requires real credentials)
    agent = EmailAgent()
    # agent.send_email("test@example.com", "Hello", "Test body")
