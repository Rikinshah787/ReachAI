import pandas as pd
import datetime
import os

class AuditAgent:
    """
    Tracks outreach status, logs results, and handles retries.
    """
    def __init__(self, log_path="logs/outreach_log.csv"):
        self.log_path = log_path
        self._init_log()

    def _init_log(self):
        if not os.path.exists(self.log_path):
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            df = pd.DataFrame(columns=[
                'timestamp', 'email', 'company', 'status', 'subject', 
                'error', 'has_attachment', 'template_used', 'scheduled_time'
            ])
            df.to_csv(self.log_path, index=False)

    def log_result(self, email, company, status, subject=None, error=None, has_attachment=False, template_used=None, scheduled_time=None):
        new_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'email': email,
            'company': company,
            'status': status,
            'subject': subject,
            'error': error,
            'has_attachment': has_attachment,
            'template_used': template_used,
            'scheduled_time': scheduled_time
        }
        df = pd.read_csv(self.log_path)
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(self.log_path, index=False)

    def mark_as_replied(self, email):
        """Mark a recruiter as having replied"""
        df = pd.read_csv(self.log_path)
        df.loc[df['email'] == email, 'status'] = 'REPLIED'
        df.to_csv(self.log_path, index=False)

    def get_stats(self):
        """Get summary statistics for dashboard"""
        if not os.path.exists(self.log_path):
            return {'total': 0, 'sent': 0, 'failed': 0, 'replied': 0}
        
        df = pd.read_csv(self.log_path)
        return {
            'total': len(df),
            'sent': len(df[df['status'] == 'SENT']),
            'failed': len(df[df['status'].str.contains('FAILED', na=False)]),
            'replied': len(df[df['status'] == 'REPLIED'])
        }

    def get_recent_activity(self, limit=10):
        """Get recent activity for dashboard"""
        if not os.path.exists(self.log_path):
            return []
        
        df = pd.read_csv(self.log_path)
        # Handle NaN values to ensure valid JSON
        df = df.where(pd.notnull(df), None)
        recent = df.tail(limit).to_dict('records')
        return list(reversed(recent))

    def has_been_contacted(self, email):
        """Check if a recruiter has already been contacted (with test exceptions)"""
        # Test exceptions: always allow these to be contacted multiple times
        test_exceptions = ["rikinshahindia@gmail.com", "rikinshahusa@gmail.com", "rikin@reachai.net", "rshah88@asu.edu"]
        if email.lower() in [e.lower() for e in test_exceptions]:
            return False
            
        if not os.path.exists(self.log_path):
            return False
        
        df = pd.read_csv(self.log_path)
        # Only count if status is SENT or REPLIED (ignore TEST or FAILED)
        contacted_df = df[df['status'].isin(['SENT', 'REPLIED'])]
        return email in contacted_df['email'].values

    def get_pending_follow_ups(self, days_limit=3):
        """Get recruiters who need follow-ups"""
        if not os.path.exists(self.log_path):
            return []
        
        df = pd.read_csv(self.log_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_limit)
        
        pending = df[
            (df['status'] == 'SENT') & 
            (df['timestamp'] < cutoff)
        ]
        # Handle NaN values
        pending = pending.where(pd.notnull(pending), None)
        return pending.to_dict('records')
