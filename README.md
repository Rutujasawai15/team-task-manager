# ⚡ TaskFlow — Team Task Manager

A full-stack web app to manage projects, assign tasks, and track progress with role-based access control.

## Tech Stack
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask, SQLAlchemy
- **Database:** SQLite (local) / auto-upgrades on Railway
- **Deploy:** Railway

## Features
- 🔐 Authentication (Signup/Login) with role selection (Admin/Member)
- 📁 Project & team management (Admin creates, assigns members)
- ✅ Task creation, assignment & status tracking (todo → in_progress → done)
- 📊 Dashboard with live stats (total, overdue, done, in-progress)
- 🔴 Overdue detection
- 🎨 Clean dark UI

## Role-Based Access
| Feature | Admin | Member |
|---|---|---|
| Create projects | ✅ | ❌ |
| Create tasks | ✅ | ❌ |
| Update task status | ✅ | Only own tasks |
| Delete tasks/projects | ✅ | ❌ |
| View dashboard | ✅ (all) | ✅ (own) |

## Local Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd team-task-manager

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

App runs at: http://localhost:5000

## Deploy to Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Add environment variable: `SECRET_KEY` = any random string
5. Deploy → Get live URL ✅

## Live URL
[Your live URL here]
