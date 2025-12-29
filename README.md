# ReachAI 🚀
### Autonomous Outbound Intelligence for Modern Sales

**ReachAI** is an AI-powered outbound automation engine that handles the heavy lifting of lead discovery, email personalization, and automated outreach. Built with a modular agent architecture for maximum extensibility.

> ⚠️ **Status: Active Development** - Core features are functional, more integrations coming soon!

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      ReachAI Engine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Discovery  │  │    LLM      │  │   Email     │         │
│  │   Agent     │  │   Agent     │  │   Agent     │         │
│  │ (Hunter.io) │  │  (Groq AI)  │  │   (SMTP)    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐         │
│  │    Data     │  │   Audit     │  │   Inbox     │         │
│  │   Agent     │  │   Agent     │  │   Agent     │         │
│  │  (CSV/DB)   │  │  (Logging)  │  │  (Replies)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   Queue     │  │  Templates  │                          │
│  │   Agent     │  │   Engine    │                          │
│  │ (Scheduler) │  │  (5 Types)  │                          │
│  └─────────────┘  └─────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Current Features (Built & Working)

| Feature | Status | Description |
|---------|--------|-------------|
| **Hunter.io Integration** | ✅ Live | Fetch verified contacts from any company domain |
| **Discovery Agent** | ✅ Live | AI-powered company search with lead extraction |
| **LLM Email Generation** | ✅ Live | Groq-powered personalized email drafts |
| **Smart Scheduling** | ✅ Live | Batch-based outreach with configurable timing |
| **Email Templates** | ✅ Live | 5 professional templates (startup, enterprise, etc.) |
| **CSV Import** | ✅ Live | Bulk lead ingestion with duplicate detection |
| **Web Dashboard** | ✅ Live | Flask-based real-time control center |
| **Audit Logging** | ✅ Live | Complete tracking of all sent emails |
| **Inbox Monitoring** | ✅ Live | Automatic detection of replies |

---

## 🔮 Future Updates (Coming Soon)

| Feature | Priority | Description |
|---------|----------|-------------|
| **Apollo.io Integration** | 🔥 High | Additional lead source with enriched data |
| **LinkedIn Automation** | 🔥 High | Direct outreach via LinkedIn messaging |
| **AI Lead Scoring** | 🔥 High | ML-based lead qualification and prioritization |
| **Multi-Step Sequences** | 🟡 Medium | Automated follow-up email chains |
| **A/B Subject Testing** | 🟡 Medium | AI-driven subject line optimization |
| **CRM Sync** | 🟡 Medium | HubSpot, Pipedrive, Salesforce integration |

---

## ⭐ Community Goal: 200 GitHub Stars

**At 200 GitHub Stars, we unlock additional premium features!**

### 📊 Progress
`[██░░░░░░░░░░░░░░░░░░] 10% (Current: ~20 / Goal: 200)`

### What unlocks at 200 stars?
- 🤖 **Advanced AI Agents** - Multi-step reasoning for lead qualification
- 🔌 **Native Integrations** - Zapier, Apollo, Salesforce connectors
- 📝 **Template A/B Testing** - AI-driven performance tracking

---

## 🛠️ Installation & Setup

### Requirements
- Python 3.9+
- Hunter.io API Key
- Groq API Key (for AI email generation)
- SMTP Credentials (Gmail recommended)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/Rikinshah787/ReachAI-.git
cd ReachAI-

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python web_dashboard.py
```

---

## 📁 Tech Stack

- **Backend**: Python, Flask
- **AI/LLM**: Groq API
- **Lead Source**: Hunter.io API
- **Email**: SMTP (Gmail compatible)
- **Scheduling**: Custom Python scheduler
- **Storage**: CSV-based (simple & portable)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

> **All Pull Requests require approval from @Rikinshah787**

---

## 📜 License

This project is licensed under the **AGPL-3.0 License**.

---

**Built with ❤️ by [@Rikinshah787](https://github.com/Rikinshah787)**
