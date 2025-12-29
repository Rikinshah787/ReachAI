import json
import os
from datetime import datetime
import pandas as pd

class QueueAgent:
    """
    Unified lead queue manager.
    Single source of truth for all leads (discovered, imported, sent).
    """
    def __init__(self, queue_path="data/leads_queue.json"):
        self.queue_path = queue_path
        os.makedirs(os.path.dirname(queue_path), exist_ok=True)
        
    def get_all_leads(self):
        """Get all leads from queue"""
        if not os.path.exists(self.queue_path):
            return []
        
        with open(self.queue_path, 'r') as f:
            try:
                return json.load(f)
            except:
                return []
    
    def add_lead(self, lead_data):
        """Add a new lead to the queue"""
        leads = self.get_all_leads()
        
        # Check for duplicates by email
        email = lead_data.get('email')
        if any(l.get('email') == email for l in leads):
            return {"status": "duplicate", "message": f"{email} already in queue"}
        
        # Add metadata
        lead_data['added_at'] = datetime.now().isoformat()
        lead_data['status'] = 'pending'  # pending, sent, replied, failed
        lead_data['last_updated'] = datetime.now().isoformat()
        
        leads.append(lead_data)
        self._save_queue(leads)
        
        return {"status": "success", "message": "Lead added to queue"}
    
    def update_lead_status(self, email, status, extra_data=None):
        """Update lead status after sending"""
        leads = self.get_all_leads()
        
        for lead in leads:
            if lead.get('email') == email:
                lead['status'] = status
                lead['last_updated'] = datetime.now().isoformat()
                if extra_data:
                    lead.update(extra_data)
                break
        
        self._save_queue(leads)
    
    def get_pending_leads(self):
        """Get leads that haven't been contacted yet"""
        leads = self.get_all_leads()
        return [l for l in leads if l.get('status') == 'pending']
    
    def get_stats(self):
        """Get queue statistics"""
        leads = self.get_all_leads()
        return {
            'total': len(leads),
            'pending': len([l for l in leads if l.get('status') == 'pending']),
            'sent': len([l for l in leads if l.get('status') == 'sent']),
            'replied': len([l for l in leads if l.get('status') == 'replied']),
            'failed': len([l for l in leads if l.get('status') == 'failed'])
        }
    
    def _save_queue(self, leads):
        """Save queue to disk"""
        with open(self.queue_path, 'w') as f:
            json.dump(leads, f, indent=2)
    
    def export_to_csv(self, csv_path="data/recruiters.csv"):
        """Export pending leads to CSV for backward compatibility"""
        pending = self.get_pending_leads()
        if not pending:
            return
        
        df = pd.DataFrame(pending)
        # Keep only required columns for main.py
        required_cols = ['first_name', 'email', 'company', 'role_hiring_for']
        
        # Ensure all required columns exist
        for col in required_cols:
            if col not in df.columns:
                # Map from discovery format
                if col == 'company' and 'company_name' in df.columns:
                    df['company'] = df['company_name']
                elif col == 'role_hiring_for' and 'position' in df.columns:
                    df['role_hiring_for'] = df['position']
                else:
                    df[col] = 'N/A'
        
        df = df[required_cols]
        df.to_csv(csv_path, index=False)
        return len(df)
