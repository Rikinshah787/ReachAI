import os
import requests
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class DiscoveryAgent:
    """
    Handles automated discovery with live progress updates:
    1. AI finds companies based on a query.
    2. Hunter.io finds contacts at those companies.
    """
    def __init__(self, progress_callback=None):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.hunter_api_key = os.getenv("HUNTER_API_KEY")
        self.model = "llama-3.1-8b-instant"
        self.progress_callback = progress_callback or (lambda msg, type: print(f"[{type}] {msg}"))
        self.errors = []
    
    def log(self, message, msg_type="info"):
        """Send progress update"""
        self.progress_callback(message, msg_type)
        if msg_type == "error":
            self.errors.append(message)

    def find_companies(self, query, limit=5):
        """
        Step 1: AI finds target companies based on user direction.
        Returns a list of companies with domains.
        """
        self.log(f"🤖 AI is analyzing query: '{query}'", "ai")
        
        prompt = f"""You are a B2B lead generation expert specializing in US-based companies. Find exactly {limit} real companies that match this criteria:

"{query}"

IMPORTANT RULES:
1. Only include REAL companies that actually exist
2. Companies must be DIRECTLY relevant to the search query
3. PRIORITIZE companies with US headquarters or significant US presence
4. Focus on companies that would have US-based recruiters/HR contacts
5. Include a mix of well-known and emerging companies
6. Provide the EXACT main website domain (e.g., "openai.com" not "www.openai.com")

Return a JSON object with a "companies" array. Each company must have:
- "name": Company name
- "domain": Main website domain (without www or https)
- "country": Country where HQ is located (prefer "USA")
- "reason": Brief explanation of why this company matches the query

Example format:
{{
  "companies": [
    {{"name": "OpenAI", "domain": "openai.com", "country": "USA", "reason": "Leading AI research lab in San Francisco"}}
  ]
}}
"""

        
        try:
            self.log("🧠 Calling Groq AI to find relevant companies...", "ai")
            
            completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a B2B lead generation expert. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            content = completion.choices[0].message.content.strip()
            data = json.loads(content)
            
            # Extract companies list
            companies = []
            if isinstance(data, dict):
                companies = data.get('companies', [])
            elif isinstance(data, list):
                companies = data
            
            if companies:
                self.log(f"✅ AI found {len(companies)} companies matching your query", "success")
                for i, c in enumerate(companies, 1):
                    reason = c.get('reason', 'Matches query criteria')
                    self.log(f"   {i}. {c.get('name')} ({c.get('domain')}) - {reason}", "info")
            else:
                self.log("⚠️ AI couldn't find matching companies. Try a different query.", "warning")
            
            return companies
            
        except json.JSONDecodeError as e:
            self.log(f"❌ AI returned invalid JSON: {str(e)}", "error")
            return []
        except Exception as e:
            self.log(f"❌ AI error: {str(e)}", "error")
            return []

    def get_contacts(self, domain, company_name=""):
        """
        Step 2: Use Hunter.io to find contacts for a domain.
        """
        if not self.hunter_api_key:
            self.log("❌ HUNTER_API_KEY not configured in .env", "error")
            return []
        
        self.log(f"🔍 Searching Hunter.io for contacts at {company_name or domain}...", "hunter")
            
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={self.hunter_api_key}"
        
        try:
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                emails = data.get('data', {}).get('emails', [])
                
                if not emails:
                    self.log(f"   ⚠️ No emails found for {domain}", "warning")
                    return []
                
                self.log(f"   📧 Found {len(emails)} contacts at {domain}", "success")
                
                contacts = []
                for entry in emails:
                    contacts.append({
                        "first_name": entry.get('first_name', 'Contact'),
                        "last_name": entry.get('last_name', ''),
                        "email": entry.get('value'),
                        "position": entry.get('position') or 'Staff',
                        "company": domain,
                        "company_name": company_name,
                        "linkedin": entry.get('linkedin'),
                        "confidence": entry.get('confidence', 0)
                    })
                return contacts
                
            elif response.status_code == 401:
                self.log(f"   ❌ Invalid Hunter.io API key", "error")
                return []
            elif response.status_code == 429:
                self.log(f"   ⚠️ Hunter.io rate limit reached", "warning")
                return []
            elif response.status_code == 402:
                self.log(f"   ❌ Hunter.io credits exhausted!", "error")
                return []
            else:
                error_msg = response.json().get('errors', [{}])[0].get('details', 'Unknown error')
                self.log(f"   ❌ Hunter.io error ({response.status_code}): {error_msg}", "error")
                return []
                
        except requests.Timeout:
            self.log(f"   ❌ Timeout searching {domain}", "error")
            return []
        except Exception as e:
            self.log(f"   ❌ Error: {str(e)}", "error")
            return []

    def run_discovery(self, query, max_domains=5):
        """
        Full automated discovery flow with progress updates.
        Limited to max_domains to control credit usage.
        """
        self.errors = []
        self.log(f"🚀 Starting AI Discovery for: '{query}'", "start")
        self.log(f"⚠️ This will search up to {max_domains} domains (uses Hunter.io credits)", "warning")
        
        # Step 1: AI finds companies
        companies = self.find_companies(query, limit=max_domains)
        
        if not companies:
            self.log("❌ No companies found. Discovery stopped.", "error")
            return []
        
        # Step 2: Search each domain
        results = []
        searched = 0
        
        for company in companies[:max_domains]:
            domain = company.get('domain')
            name = company.get('name', domain)
            
            if not domain:
                continue
                
            searched += 1
            self.log(f"📡 [{searched}/{len(companies)}] Processing {name}...", "progress")
            
            contacts = self.get_contacts(domain, name)
            
            # Filter for relevant personas
            relevant_keywords = ['recruit', 'hr', 'found', 'talent', 'tech', 'engineer', 
                               'ceo', 'cto', 'coo', 'head', 'director', 'manager', 'lead']
            
            for contact in contacts:
                position = (contact.get('position') or '').lower()
                # Include if position matches OR if no position (include all)
                if not position or any(kw in position for kw in relevant_keywords):
                    contact['search_query'] = query
                    contact['reason'] = company.get('reason', '')
                    results.append(contact)
        
        # Summary
        self.log("=" * 50, "divider")
        if results:
            self.log(f"✅ Discovery complete! Found {len(results)} relevant contacts", "success")
        else:
            self.log("⚠️ No contacts found matching criteria", "warning")
        
        if self.errors:
            self.log(f"⚠️ {len(self.errors)} errors occurred during discovery", "warning")
            
        return results

if __name__ == "__main__":
    agent = DiscoveryAgent()
    results = agent.run_discovery("AI startups hiring software engineers", max_domains=3)
    print(f"\nTotal results: {len(results)}")
