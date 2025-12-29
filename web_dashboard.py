import os
import sys
import json
import logging
import signal
import subprocess
import threading
import time
import pandas as pd
from datetime import datetime, timedelta
import pytz
import math
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv
from core.agents.audit_agent import AuditAgent
from core.agents.discovery_agent import DiscoveryAgent
from core.agents.templates import EmailTemplates

DISCOVERY_LOG = "logs/discovery_results.json"

app = Flask(__name__, template_folder='ui/templates')

def sanitize_data(obj):
    """Recursively replace NaN with None for JSON compatibility"""
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: sanitize_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_data(i) for i in obj]
    return obj

def get_stats():
    """Get dashboard statistics"""
    audit_agent = AuditAgent()
    stats = audit_agent.get_stats()
    
    # Get template stats
    template_stats = {}
    if os.path.exists("logs/outreach_log.csv"):
        df = pd.read_csv("logs/outreach_log.csv")
        if 'template_used' in df.columns and not df.empty:
            for template in df['template_used'].dropna().unique():
                template_df = df[df['template_used'] == template]
                total = len(template_df)
                sent = len(template_df[template_df['status'] == 'SENT'])
                replied = len(template_df[template_df['status'] == 'REPLIED'])
                
                template_stats[template] = {
                    'total': total,
                    'sent': sent,
                    'replied': replied,
                    'reply_rate': (replied / sent * 100) if sent > 0 else 0
                }
    
    # Get recent activity
    recent = audit_agent.get_recent_activity(limit=10)
    
    # Get scheduled emails
    scheduled = []
    if os.path.exists("logs/outreach_log.csv"):
        df = pd.read_csv("logs/outreach_log.csv")
        if not df.empty and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            last_sent = df[df['status'] == 'SENT'].sort_values('timestamp', ascending=False)
            
            if not last_sent.empty:
                from dotenv import load_dotenv
                load_dotenv()
                delay = int(os.getenv("EMAIL_DELAY_SECONDS", 30))
                
                last_time = last_sent.iloc[0]['timestamp']
                next_scheduled = last_time + timedelta(seconds=delay)
                
                if next_scheduled > datetime.now():
                    time_until = (next_scheduled - datetime.now()).total_seconds()
                    scheduled.append({
                        'scheduled_time': next_scheduled.strftime('%H:%M:%S'),
                        'time_until': int(time_until)
                    })
    
    return {
        'stats': stats,
        'template_stats': template_stats,
        'recent': recent,
        'scheduled': scheduled,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'timezone': 'America/Phoenix (MST)'
    }

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard data"""
    data = get_stats()
    sanitized_data = sanitize_data(data)
    response = jsonify(sanitized_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/leads', methods=['POST'])
def add_lead():
    """
    Endpoint for Zapier/Apollo integration.
    Expects JSON: { "first_name": "...", "email": "...", "company": "...", "role_hiring_for": "..." }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ['first_name', 'email', 'company', 'role_hiring_for']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Add to recruiters.csv
        csv_path = "data/recruiters.csv"
        new_row = pd.DataFrame([{
            'first_name': data['first_name'],
            'email': data['email'],
            'company': data['company'],
            'role_hiring_for': data['role_hiring_for'],
            'linkedin': data.get('linkedin', ''),
            'phone': data.get('phone', '')
        }])
        
        if os.path.exists(csv_path):
            # Check if we need to add missing columns
            existing_df = pd.read_csv(csv_path)
            changed = False
            if 'linkedin' not in existing_df.columns:
                existing_df['linkedin'] = ''
                changed = True
            if 'phone' not in existing_df.columns:
                existing_df['phone'] = ''
                changed = True
            
            if changed:
                existing_df.to_csv(csv_path, index=False)
            
            new_row.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            new_row.to_csv(csv_path, index=False)
            
        return jsonify({"status": "success", "message": "Lead added to ReachAI queue"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/discover/search', methods=['POST'])
def discover_leads():
    """Trigger AI + Hunter.io discovery flow with progress tracking"""
    try:
        query = request.json.get('query')
        max_domains = request.json.get('max_domains', 5)  # Limit credit usage
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Collect progress logs
        progress_logs = []
        def progress_callback(message, msg_type):
            progress_logs.append({"message": message, "type": msg_type})
            print(f"[Discovery] {message}")
        
        agent = DiscoveryAgent(progress_callback=progress_callback)
        leads = agent.run_discovery(query, max_domains=max_domains)
        
        # Persist results
        current_data = []
        if os.path.exists(DISCOVERY_LOG):
            with open(DISCOVERY_LOG, 'r') as f:
                try:
                    current_data = json.load(f)
                except:
                    pass
        
        # Add timestamp and query info to each lead for the dashboard
        timestamp = datetime.now().isoformat()
        for lead in leads:
            lead['timestamp'] = timestamp
            if 'search_query' not in lead:
                lead['search_query'] = query
        
        # Prepend new leads to keep history
        updated_data = leads + current_data
        # Limit history to 1000 leads
        updated_data = updated_data[:1000]
        
        os.makedirs(os.path.dirname(DISCOVERY_LOG), exist_ok=True)
        with open(DISCOVERY_LOG, 'w') as f:
            json.dump(updated_data, f, indent=2)
        
        return jsonify({
            "status": "success", 
            "leads_found": len(leads), 
            "leads": leads,
            "progress": progress_logs,
            "errors": agent.errors
        })
        
    except Exception as e:
        print(f"Discovery error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/discover/results', methods=['GET'])
def get_discovery_results():
    """Retrieve history of discovered leads"""
    if os.path.exists(DISCOVERY_LOG):
        with open(DISCOVERY_LOG, 'r') as f:
            try:
                data = json.load(f)
                return jsonify(sanitize_data(data))
            except:
                return jsonify([])
    return jsonify([])

@app.route('/api/discover/clear', methods=['POST'])
def clear_discovery():
    """Clear all discovered leads"""
    try:
        if os.path.exists(DISCOVERY_LOG):
            os.remove(DISCOVERY_LOG)
        return jsonify({"status": "success", "message": "Discovery results cleared"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/scheduler/toggle', methods=['POST'])
def toggle_scheduler():
    """Enable or disable the scheduler"""
    try:
        from utils.config import load_schedule_config, save_schedule_config
        config = load_schedule_config()
        
        # Toggle current state
        new_state = not config.get("auto_enabled", False)
        config["auto_enabled"] = new_state
        
        save_schedule_config(config)
        
        status_msg = "Enabled" if new_state else "Disabled"
        return jsonify({
            "status": "success", 
            "auto_enabled": new_state,
            "message": f"Scheduler {status_msg}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/discover/hunter-leads', methods=['POST'])
def fetch_hunter_leads():

    """
    Fetch NEW leads from Hunter.io LEADS database (FREE - no credits consumed!)
    Checks against existing leads and only imports new ones.
    """
    import requests
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        return jsonify({"error": "HUNTER_API_KEY not configured"}), 400
    
    print("🔍 Fetching leads from Hunter.io Leads Database (FREE)...")
    
    # Load existing leads to check for duplicates
    existing_emails = set()
    existing_leads = []
    if os.path.exists(DISCOVERY_LOG):
        try:
            with open(DISCOVERY_LOG, 'r') as f:
                existing_leads = json.load(f)
                existing_emails = {lead.get('email', '').lower() for lead in existing_leads if lead.get('email')}
        except:
            pass
    
    print(f"📊 Found {len(existing_emails)} existing leads in database")
    
    all_leads = []
    offset = 0
    limit = 100  # Max per request
    max_leads = 1000  # Increased limit to store all leads
    total_from_hunter = 0
    
    try:
        while len(all_leads) < max_leads:
            url = f"https://api.hunter.io/v2/leads?api_key={api_key}&offset={offset}&limit={limit}"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                leads_data = data.get('data', {}).get('leads', [])
                
                if not leads_data:
                    break
                
                total_from_hunter = data.get('data', {}).get('meta', {}).get('results', 0)
                
                # Transform to our format
                timestamp = datetime.now().isoformat()
                for lead in leads_data:
                    transformed = {
                        "first_name": lead.get('first_name', 'Contact'),
                        "last_name": lead.get('last_name', ''),
                        "email": lead.get('email'),
                        "phone": lead.get('phone_number') or '',
                        "position": lead.get('position') or lead.get('title') or 'Professional',
                        "company": lead.get('company') or lead.get('organization', 'Company'),
                        "company_name": lead.get('company') or lead.get('organization', 'Company'),
                        "linkedin": lead.get('linkedin_url'),
                        "timestamp": timestamp,
                        "search_query": "Imported from Hunter.io Leads Database",
                        "source": "hunter_leads_db"
                    }
                    all_leads.append(transformed)
                
                if len(all_leads) >= total_from_hunter:
                    break
                    
                offset += limit
                
            elif response.status_code == 429:
                print("⚠️ Rate limited")
                break
            else:
                print(f"❌ Hunter.io error: {response.status_code}")
                return jsonify({"error": f"Hunter.io error: {response.status_code}"}), 500
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return jsonify({"error": str(e)}), 500
    
    # Filter out duplicates
    new_leads = []
    skipped_count = 0
    for lead in all_leads:
        email = (lead.get('email') or '').lower()
        if email and email not in existing_emails:
            new_leads.append(lead)
            existing_emails.add(email)  # Prevent duplicates within this batch
        else:
            skipped_count += 1
    
    print(f"📧 Hunter.io has {total_from_hunter} total leads")
    print(f"✅ New leads to import: {len(new_leads)}")
    print(f"⏭️  Skipped (already exists): {skipped_count}")
    
    if new_leads:
        # Merge with existing leads (new ones first)
        combined_leads = new_leads + existing_leads
        
        # Save to discovery log
        os.makedirs(os.path.dirname(DISCOVERY_LOG), exist_ok=True)
        with open(DISCOVERY_LOG, 'w') as f:
            json.dump(combined_leads, f, indent=2)
        
        message = f"✅ Imported {len(new_leads)} NEW leads | ⏭️ Skipped {skipped_count} (already exist)"
    else:
        message = f"✅ All {total_from_hunter} leads already exist in your database"
    
    return jsonify({
        "status": "success", 
        "total_in_hunter": total_from_hunter,
        "new_leads": len(new_leads),
        "skipped": skipped_count,
        "total_in_database": len(existing_leads) + len(new_leads),
        "message": message
    })


@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """Get status of imported leads from CSV"""
    try:
        # Read CSV
        csv_path = "data/recruiters.csv"
        if not os.path.exists(csv_path):
            return jsonify({"queue": []})
        
        df = pd.read_csv(csv_path)
        
        # Get outreach log to check status
        audit_agent = AuditAgent()
        log_df = None
        if os.path.exists("logs/outreach_log.csv"):
            log_df = pd.read_csv("logs/outreach_log.csv")
        
        # Build queue with status
        queue = []
        for _, row in df.iterrows():
            email = row['email']
            
            # Check if contacted
            status = 'pending'
            if log_df is not None and not log_df.empty:
                matches = log_df[log_df['email'] == email]
                if not matches.empty:
                    latest_status = matches.iloc[-1]['status']
                    status = latest_status.lower()
            
            queue.append({
                "first_name": row['first_name'],
                "email": email,
                "company": row['company'],
                "role_hiring_for": row['role_hiring_for'],
                "linkedin": row.get('linkedin', '') if 'linkedin' in row.index else '',
                "phone": row.get('phone', '') if 'phone' in row.index else '',
                "status": status
            })
        
        return jsonify(sanitize_data({"queue": queue}))
        
    except Exception as e:
        print(f"Queue status error: {e}")
        return jsonify({"queue": [], "error": str(e)})

@app.route('/api/send-history', methods=['GET'])
def get_send_history():
    """Get history of manual send clicks"""
    import json
    try:
        history_file = "logs/send_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
            return jsonify(history)
        else:
            return jsonify({"clicks": []})
    except Exception as e:
        print(f"Send history error: {e}")
        return jsonify({"clicks": [], "error": str(e)})


@app.route('/api/send-now', methods=['POST'])
def send_now():
    """Trigger immediate email sending using existing main.py logic"""
    global active_process
    
    try:
        import subprocess
        import sys
        
        data = request.json
        count = data.get('count', 5)
        
        # Log click history
        history_file = "logs/send_history.json"
        try:
            history = {"clicks": []}
            if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
                try:
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    logging.warning(f"⚠️ Resetting corrupted history file: {history_file}")
            
            click_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": count,
                "status": "initiated"
            }
            history["clicks"].append(click_entry)
            
            logging.info(f"📝 Logging click to {history_file}: {click_entry}")
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
            logging.info("✅ Click history saved successfully")
        except Exception as e:
            logging.error(f"❌ Could not log click history: {e}")
            print(f"Warning: Could not log click history: {e}")
        
        if count < 1 or count > 30:
            return jsonify({"error": "Count must be between 1 and 30"}), 400
        
        # Check if already running (and clean up completed processes)
        if active_process:
            poll_result = active_process.poll()
            if poll_result is None:
                # Process is actually running
                pid = active_process.pid
                msg = f"Email sending already in progress (PID: {pid}). Please wait for it to finish."
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Send blocked - {msg}")
                return jsonify({"error": msg, "pid": pid}), 409
            else:
                # Process completed, clean up
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧹 Cleaned up completed process {active_process.pid}")
                active_process = None

        # Pre-send Validation: Check how many leads are actually pending
        try:
            from agents.audit_agent import AuditAgent
            from agents.data_agent import DataAgent
            
            data_agent = DataAgent("data/recruiters.csv")
            audit_agent = AuditAgent()
            
            all_leads = data_agent.load_data()
            pending_leads = [l for l in all_leads if not audit_agent.has_been_contacted(l['email'])]
            
            if not pending_leads:
                msg = "No pending leads found in your queue! All leads in recruiters.csv have already been contacted."
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Validation Failed: {msg}")
                return jsonify({
                    "error": msg,
                    "details": "Add more leads in the Discovery tab or clean your log to re-send."
                }), 400
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Validation Passed: {len(pending_leads)} pending leads available.")
        except Exception as e:
            print(f"Warning: Pre-send validation skipped due to error: {e}")
        
        # Use existing main.py with proper arguments including --limit
        env = os.environ.copy()
        env['SKIP_INBOX_CHECK'] = 'true'  # Skip inbox for faster sending
        
        # Build command with --limit for batch control and --force for manual override
        cmd = [
            sys.executable,
            "main.py",
            "--bio", "Rikin Shah",
            "--csv", "data/recruiters.csv",
            "--limit", str(count),
            "--delay", "30",
            "--force"
        ]
        
        print(f"\n{'='*60}")
        print(f"🚀 MANUAL SEND triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📧 Count: {count} emails")
        print(f"⚡ Command: {' '.join(cmd)}")
        print(f"{'='*60}")
        
        # Start process in background
        active_process = subprocess.Popen(
            cmd,
            cwd=os.getcwd(),
            env=env
            # Removed PIPE to allow direct terminal output on Windows
        )
        
        print(f"✅ Send process started (PID: {active_process.pid})")
        print(f"📊 Activity will appear in terminal and Activity tab")
        print(f"{'='*60}\n")

        return jsonify({
            "status": "success",
            "message": f"Started sending emails to top {count} pending leads. Check terminal and Activity tab for results."
        })
            
    except Exception as e:
        print(f"Send now error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all email templates with resume mappings"""
    try:
        from agents.templates import EmailTemplates
        from utils.config import load_template_config
        
        # Load resume mappings from config
        template_config = load_template_config()
        
        templates = []
        for key, data in EmailTemplates.TEMPLATES.items():
            # Get resume & custom content from config or default
            resume = 'resume_rikin.pdf'
            template_content = data['template']
            
            if template_config and key in template_config:
                resume = template_config[key].get('resume', 'resume_rikin.pdf')
                if 'custom_template' in template_config[key]:
                    template_content = template_config[key]['custom_template']
            
            templates.append({
                'key': key,
                'name': data['name'],
                'keywords': ', '.join(data['role_keywords']) if data['role_keywords'] else 'Default',
                'preview': template_content[:200] + '...' if len(template_content) > 200 else template_content,
                'full_template': template_content,
                'resume': resume
            })
        
        return jsonify(sanitize_data({'templates': templates}))
    except Exception as e:
        print(f"Templates error: {e}")
        return jsonify({"templates": [], "error": str(e)})

@app.route('/api/templates/save', methods=['POST'])
def save_template():
    """Save template configuration"""
    try:
        from utils.config import load_template_config, save_template_config
        
        data = request.json
        template_key = data.get('key')
        resume = data.get('resume')
        template_text = data.get('template')
        
        if not template_key:
            return jsonify({"error": "Template key required"}), 400
        
        # Load current config
        config = load_template_config() or {}
        
        # Update template
        if template_key not in config:
            config[template_key] = {}
        
        if resume:
            config[template_key]['resume'] = resume
        if template_text:
            config[template_key]['custom_template'] = template_text
        
        # Save
        save_template_config(config)
        
        return jsonify({"status": "success", "message": f"Template {template_key} saved"})
    except Exception as e:
        print(f"Save template error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get schedule configuration"""
    try:
        from utils.config import load_schedule_config
        config = load_schedule_config()
        return jsonify(config)
    except Exception as e:
        print(f"Get schedule error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedule/save', methods=['POST'])
def save_schedule():
    """Save schedule configuration"""
    try:
        from utils.config import save_schedule_config
        
        data = request.json
        save_schedule_config(data)
        
        return jsonify({"status": "success", "message": "Schedule settings saved"})
    except Exception as e:
        print(f"Save schedule error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/remove', methods=['POST'])
def remove_lead():
    """Remove a lead from the queue (CSV)"""
    try:
        data = request.json
        email_to_remove = data.get('email')
        
        if not email_to_remove:
            return jsonify({"error": "Email required"}), 400
        
        csv_path = "data/recruiters.csv"
        if not os.path.exists(csv_path):
            return jsonify({"error": "No queue found"}), 404
        
        df = pd.read_csv(csv_path)
        original_length = len(df)
        
        # Remove the lead
        df = df[df['email'] != email_to_remove]
        
        if len(df) == original_length:
            return jsonify({"error": "Lead not found"}), 404
        
        df.to_csv(csv_path, index=False)
        return jsonify({"status": "success", "message": f"Removed {email_to_remove}"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/remove-all', methods=['POST'])
def remove_all_leads_from_queue():
    """Remove all pending leads from the queue"""
    try:
        csv_path = "data/recruiters.csv"
        if not os.path.exists(csv_path):
            return jsonify({"status": "success", "message": "Queue already empty", "count": 0})
            
        df = pd.read_csv(csv_path)
        
        # We only want to remove leads that haven't been contacted yet
        # Get outreach log to identify contacted leads
        log_path = "logs/outreach_log.csv"
        contacted_emails = set()
        if os.path.exists(log_path):
            log_df = pd.read_csv(log_path)
            if not log_df.empty:
                contacted_emails = set(log_df['email'].unique())
        
        original_count = len(df)
        # Keep leads that ARE in contacted_emails
        df = df[df['email'].isin(contacted_emails)]
        removed_count = original_count - len(df)
        
        df.to_csv(csv_path, index=False)
        return jsonify({
            "status": "success", 
            "message": f"Removed {removed_count} pending leads", 
            "count": removed_count
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/import-all', methods=['POST'])
def import_all_leads():
    """Import multiple leads at once"""
    try:
        data = request.json
        leads = data.get('leads', [])
        
        if not leads:
            return jsonify({"error": "No leads provided"}), 400
        
        csv_path = "data/recruiters.csv"
        
        # Read existing CSV
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            existing_emails = set(existing_df['email'].values)
        else:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            existing_emails = set()
        
        # Filter out duplicates
        new_leads = []
        duplicates_count = 0
        for lead in leads:
            if lead['email'] in existing_emails:
                duplicates_count += 1
                continue
                
            new_leads.append({
                'first_name': lead['first_name'],
                'email': lead['email'],
                'company': lead['company'],
                'role_hiring_for': lead['role_hiring_for'],
                'linkedin': lead.get('linkedin', ''),
                'phone': lead.get('phone', '')
            })
            existing_emails.add(lead['email'])
        
        if not new_leads:
            return jsonify({
                "status": "success", 
                "message": f"No new leads imported. {duplicates_count} duplicates found.", 
                "count": 0,
                "duplicates": duplicates_count
            }), 200
        
        # Append to CSV
        new_df = pd.DataFrame(new_leads)
        
        if os.path.exists(csv_path):
            # Check if we need to add missing columns
            existing_df = pd.read_csv(csv_path)
            changed = False
            if 'linkedin' not in existing_df.columns:
                existing_df['linkedin'] = ''
                changed = True
            if 'phone' not in existing_df.columns:
                existing_df['phone'] = ''
                changed = True
            
            if changed:
                existing_df.to_csv(csv_path, index=False)
                
            new_df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            new_df.to_csv(csv_path, index=False)
        
        msg = f"Imported {len(new_leads)} leads."
        if duplicates_count > 0:
            msg += f" {duplicates_count} duplicates skipped."
            
        return jsonify({
            "status": "success", 
            "message": msg, 
            "count": len(new_leads),
            "duplicates": duplicates_count
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/sample-csv')
def download_sample_csv():
    """Download a sample CSV template"""
    try:
        from flask import send_file
        sample_path = os.path.join(os.getcwd(), "data", "sample_recruiters.csv")
        if not os.path.exists(sample_path):
            # Create if doesn't exist
            os.makedirs(os.path.dirname(sample_path), exist_ok=True)
            with open(sample_path, 'w') as f:
                f.write("first_name,email,company,role_hiring_for,linkedin,phone\n")
                f.write("John,john@example.com,Acme Corp,Software Engineer,https://linkedin.com/in/johndoe,+1234567890\n")
        
        return send_file(sample_path, as_attachment=True, download_name="reachai_sample_leads.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Global process tracker for scheduler
active_process = None

# Global scheduler state
scheduler_state = {
    "status": "Inactive",
    "last_check": None,
    "next_check": None,
    "last_run": None,
    "message": "Initializing..."
}

@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Return scheduler status with current config"""
    from utils.config import load_schedule_config
    config = load_schedule_config()
    
    # Include config in response so frontend always shows latest settings
    response = dict(scheduler_state)
    response['config'] = {
        'start_time': config.get('start_time', ''),
        'batch_interval': config.get('batch_interval', 60),
        'batch_size': config.get('batch_size', 5),
        'auto_enabled': config.get('auto_enabled', False)
    }
    return jsonify(response)


# --- Background Scheduler ---
def scholarship_scheduler():
    """Background thread - runs at configured start_time, then repeats at interval"""
    global active_process, scheduler_state
    
    import time
    from datetime import datetime, timedelta
    from utils.config import load_schedule_config
    
    print("⏰ Scheduler Started - Using start_time datetime with interval repeats")
    
    scheduler_state["status"] = "Active"
    last_run_time = None  # Track when we last ran to use interval
    
    while True:
        try:
            now = datetime.now()
            
            # Load config
            config = load_schedule_config()
            if not config or not config.get("auto_enabled", False):
                scheduler_state["status"] = "Disabled"
                scheduler_state["message"] = "Auto-Sending Disabled"
                print(f"[{now.strftime('%H:%M:%S')}] ⏸️  Scheduler Disabled")
                time.sleep(60)
                continue
            
            scheduler_state["status"] = "Active"
            
            # Get start_time as full datetime (format: YYYY-MM-DDTHH:MM or YYYY-MM-DD HH:MM)
            start_time_str = config.get("start_time", "")
            batch_interval = config.get("batch_interval", 60)  # Minutes between batches
            
            # Determine next run time
            next_run = None
            start_datetime = None
            
            if start_time_str:
                try:
                    # Parse the start_time (supports both T and space separators)
                    clean_start_time = start_time_str.replace("T", " ")
                    if len(clean_start_time) == 16:  # YYYY-MM-DD HH:MM
                        start_datetime = datetime.strptime(clean_start_time, "%Y-%m-%d %H:%M")
                    elif len(clean_start_time) == 10:  # YYYY-MM-DD only
                        start_datetime = datetime.strptime(clean_start_time, "%Y-%m-%d")
                    else:
                        raise ValueError(f"Unknown format: {start_time_str}")
                    
                    print(f"[{now.strftime('%H:%M:%S')}] 📅 Config start_time: {start_datetime}")
                    
                except Exception as e:
                    print(f"[{now.strftime('%H:%M:%S')}] ❌ Error parsing start_time '{start_time_str}': {e}")
                    scheduler_state["message"] = f"Invalid start_time: {start_time_str}"
                    time.sleep(60)
                    continue
            
            # Logic to determine next run:
            # 1. If never run, use start_datetime (or now if past/not set)
            # 2. If start_datetime is in the future, always wait for it (allows reschedule)
            # 3. Otherwise, use last_run_time + interval
            
            if start_datetime and start_datetime > now:
                # Config start_time is in the future - always respect this (allows reschedule)
                next_run = start_datetime
                print(f"[{now.strftime('%H:%M:%S')}] ⏳ Waiting for configured start_time")
            elif last_run_time is None:
                # Never run before
                if start_datetime and now >= start_datetime:
                    # Start time is in the past - run immediately!
                    next_run = now
                    print(f"[{now.strftime('%H:%M:%S')}] ⚡ Start time is in the past - running immediately!")
                elif start_datetime:
                    next_run = start_datetime
                else:
                    # No start_time set - run now
                    next_run = now
            else:
                # We have run before - use interval from last run
                next_run = last_run_time + timedelta(minutes=batch_interval)

            
            # Calculate time until next run
            time_until = next_run - now
            total_seconds = time_until.total_seconds()
            
            if total_seconds > 0:
                hours_until = int(total_seconds // 3600)
                minutes_until = int((total_seconds % 3600) // 60)
                scheduler_state["message"] = f"Next run in {hours_until}h {minutes_until}m at {next_run.strftime('%Y-%m-%d %H:%M')}"
                scheduler_state["next_check"] = next_run.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now.strftime('%H:%M:%S')}] 📅 Next run: {next_run.strftime('%Y-%m-%d %H:%M')} ({hours_until}h {minutes_until}m)")
                time.sleep(30)  # Check every 30 seconds
                continue
            
            # Time to run!
            # Check if process is already running
            if active_process and active_process.poll() is None:
                print(f"[{now.strftime('%H:%M:%S')}] ⏳ Email send already in progress (PID: {active_process.pid})")
                scheduler_state["message"] = f"Sending in progress (PID: {active_process.pid})"
                time.sleep(30)
                continue
            
            # Execute batch
            batch_size = config.get("batch_size", 5)
            delay = config.get("delay_seconds", 30)
            
            print(f"\n{'='*60}")
            print(f"🚀 SCHEDULER TRIGGERED at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📧 Batch Size: {batch_size} emails")
            print(f"⏱️  Delay: {delay} seconds")
            print(f"🔄 Next batch in: {batch_interval} minutes")
            print(f"{'='*60}\n")
            
            scheduler_state["message"] = f"🚀 Running batch ({batch_size} emails)"
            
            cmd = [sys.executable, "main.py", "--limit", str(batch_size), "--delay", str(delay), "--bio", "Rikin Shah", "--force"]
            
            # Set environment
            env = os.environ.copy()
            if config.get("daily_limit"):
                env["DAILY_EMAIL_LIMIT"] = str(config.get("daily_limit"))
            
            # Start process - don't capture stdout so it streams to terminal
            active_process = subprocess.Popen(
                cmd,
                cwd=os.getcwd(),
                env=env
            )
            
            # Mark last run time
            last_run_time = now
            scheduler_state["last_run"] = now.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now.strftime('%H:%M:%S')}] ✅ Started process PID: {active_process.pid}")
            
            # Wait before next check
            time.sleep(30)

            
        except Exception as e:
            print(f"❌ Scheduler Error: {e}")
            import traceback
            traceback.print_exc()
            scheduler_state["message"] = f"Error: {str(e)}"
            time.sleep(60)

# Start Scheduler
threading.Thread(target=scholarship_scheduler, daemon=True).start()

if __name__ == '__main__':
    print("🚀 Starting Web Dashboard...")
    print("📊 Open your browser to: http://localhost:5001")
    print("Press Ctrl+C to stop")
    # webbrowser.open('http://127.0.0.1:5000') # Optional
    app.run(debug=True, port=5001, use_reloader=False) # Disable reloader to prevent duplicate threads
