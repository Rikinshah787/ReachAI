# Quick Start Guide

## ✅ You're All Set!

Your system is configured and ready to go. Here's how to use it:

### 1. Test Mode (Preview Only - No Emails Sent)
```powershell
python main.py --test --bio "I am a Full-Stack Developer with 5 years of experience in Python, React, and building scalable web applications."
```

### 2. Send Real Email to Yourself (Test)
```powershell
python main.py --bio "I am a Full-Stack Developer with 5 years of experience in Python, React, and building scalable web applications." --delay 5
```

This will send an email to `rikinshah787@gmail.com` with your resume attached!

### 3. Check Your Inbox
- Go to https://gmail.com
- Look for an email from yourself
- Verify the subject line and body are personalized
- Check that your resume is attached

### 4. View Dashboard (Optional)
Open a second terminal and run:
```powershell
python dashboard.py
```

### 5. Add Real Recruiters
Once you've tested successfully:
1. Open `data/recruiters.csv`
2. Add real recruiter emails
3. Run the pipeline again

## 📊 What Happens When You Run It

1. ✅ Loads recruiter data from CSV
2. ✅ Generates personalized email using Groq AI
3. ✅ Attaches your resume (from `data/resume.pdf`)
4. ✅ Sends via Gmail SMTP
5. ✅ Logs everything to `logs/outreach_log.csv`

## 🎯 Current Test Data

Your CSV currently has:
- **Rikin** (rikinshah787@gmail.com) at TestCompany

This is perfect for testing! You'll receive the email at your own address.

## ⚠️ Important Notes

- The system will **skip** recruiters you've already contacted (duplicate prevention)
- Default delay between emails is 30 seconds (you can change with `--delay`)
- All activity is logged in `logs/` directory
- Test mode (`--test`) shows you what would be sent without actually sending

## 🚀 Ready to Go Live?

When you're ready to contact real recruiters:
1. Update `data/recruiters.csv` with real recruiter data
2. Remove the `--test` flag
3. Run the command
4. Monitor with `dashboard.py`

Good luck with your job search! 🎉
