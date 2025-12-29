"""
Fetch ALL leads from Hunter.io account (not domain search)
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def fetch_all_hunter_leads():
    api_key = os.getenv("HUNTER_API_KEY")
    
    if not api_key:
        print("❌ HUNTER_API_KEY not found")
        return []
    
    print("="*70)
    print("FETCHING ALL LEADS FROM HUNTER.IO ACCOUNT")
    print("="*70)
    
    all_leads = []
    offset = 0
    limit = 100  # Max per request
    
    while True:
        url = f"https://api.hunter.io/v2/leads?api_key={api_key}&offset={offset}&limit={limit}"
        
        print(f"\n🔍 Fetching leads {offset}-{offset+limit}...")
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                leads_data = data.get('data', {}).get('leads', [])
                
                if not leads_data:
                    print("   No more leads found.")
                    break
                
                print(f"   ✅ Got {len(leads_data)} leads")
                
                # Transform to our format
                for lead in leads_data:
                    transformed = {
                        "first_name": lead.get('first_name', 'Contact'),
                        "last_name": lead.get('last_name', ''),
                        "email": lead.get('email'),
                        "position": lead.get('position') or lead.get('title') or 'Professional',
                        "company": lead.get('company') or lead.get('organization', 'Company'),
                        "company_name": lead.get('company') or lead.get('organization', 'Company'),
                        "linkedin": lead.get('linkedin_url'),
                        "phone": lead.get('phone_number'),
                        "source": "hunter_leads_db",
                        "search_query": "Imported from Hunter.io Leads Database"
                    }
                    all_leads.append(transformed)
                
                # Check if we got all
                total = data.get('data', {}).get('meta', {}).get('results', 0)
                print(f"   Total in account: {total}")
                
                if len(all_leads) >= total:
                    break
                
                offset += limit
                
            elif response.status_code == 429:
                print(f"   ⚠️ Rate limited. Got {len(all_leads)} leads so far.")
                break
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                break
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            break
    
    print(f"\n{'='*70}")
    print(f"✅ TOTAL LEADS FETCHED: {len(all_leads)}")
    print(f"{'='*70}")
    
    return all_leads

def save_to_dashboard(leads):
    """Save leads to discovery_results.json for dashboard"""
    
    if not leads:
        print("\n❌ No leads to save")
        return
    
    print(f"\n💾 Saving {len(leads)} leads to dashboard...")
    
    # Add timestamp to each
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    
    for lead in leads:
        lead['timestamp'] = timestamp
    
    # Save to discovery log
    os.makedirs("logs", exist_ok=True)
    with open("logs/discovery_results.json", 'w') as f:
        json.dump(leads, f, indent=2)
    
    print("✅ Saved to: logs/discovery_results.json")
    
    # Show sample
    print(f"\n📧 Sample leads:")
    for i, lead in enumerate(leads[:5], 1):
        print(f"{i}. {lead['first_name']} {lead['last_name']}")
        print(f"   📧 {lead['email']}")
        print(f"   🏢 {lead['company_name']}")
        print(f"   💼 {lead['position']}\n")
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Open: http://localhost:5001")
    print(f"2. Go to Discovery tab")
    print(f"3. You'll see all {len(leads)} leads")
    print(f"4. Click 'Import Lead' to add to queue")
    print(f"5. Run: python main.py --test --bio 'Your Bio'")

if __name__ == "__main__":
    leads = fetch_all_hunter_leads()
    
    if leads:
        save_to_dashboard(leads)
    else:
        print("\n⚠️ No leads fetched. Check API key or rate limits.")
