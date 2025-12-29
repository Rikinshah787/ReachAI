# Complete System Flow Summary

## ✅ All Features Implemented

### 1. Discovery Tab
- **100 Hunter.io leads** loaded and displayed
- **Pagination**: 10 leads per page
- **Import All on This Page** button
- **Import All Leads (All Pages)** button  
- Individual **Import Lead** buttons

### 2. Queue Tab
- Shows all imported leads from CSV
- Real-time status: PENDING / SENT / REPLIED / FAILED
- **Remove** button on each lead
- Auto-refreshes every 5 seconds

### 3. Automated Email Scheduling

The existing `main.py` already handles auto-pickup:
- Reads from `data/recruiters.csv`
- Processes leads with status "PENDING"
- Default quota: **30 emails per day**
- Configurable via `.env`: `DAILY_EMAIL_LIMIT=30`

## How It Works

```
┌──────────────────────────────────────────────────────┐
│  USER ACTION: Click "Find Leads" (Manual Trigger)   │
│  → Fetches from Hunter.io ONCE                      │
│  → Displays 100 leads with pagination                │
└────────────────┬─────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────┐
│  IMPORT OPTIONS:                                     │
│  • Click individual "Import Lead"                    │
│  • "Import All on This Page" (10 leads)             │
│  • "Import All Leads" (all 100 leads)                │
└────────────────┬─────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────┐
│  QUEUE TAB:                                          │
│  • Shows imported leads from recruiters.csv          │
│  • View status (PENDING → SENT → REPLIED)           │
│  • Remove unwanted leads                             │
└────────────────┬─────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────┐
│  AUTOMATED SYSTEM:                                   │
│  python main.py --bio "Your Bio"                     │
│  • Picks up to 30 PENDING leads                      │
│  • Generates personalized emails                     │
│  • Sends automatically                               │
│  • Updates status in logs                            │
└──────────────────────────────────────────────────────┘
```

## API Endpoints

- `POST /api/discover/search` - Trigger Hunter.io search (manual only)
- `GET /api/discover/results` - Get discovered leads
- `POST /api/leads` - Import single lead
- `POST /api/leads/import-all` - Bulk import leads
- `POST /api/leads/remove` - Remove lead from queue
- `GET /api/queue/status` - Get queue with statuses

## No Auto-Fetch

The system does **NOT** auto-fetch from Hunter.io anymore:
- Only fetches when user clicks "Find Leads"
- Existing leads persist in `logs/discovery_results.json`
- No API calls on page refresh

## Current Status

Dashboard running at: http://localhost:5001

**Ready to use:**
1. Go to Discovery tab
2. Browse 100 leads (paginated)
3. Import leads (individual or bulk)
4. Check Queue tab
5. Run: `python main.py --bio "Your bio"`
6. System auto-sends up to 30 emails
