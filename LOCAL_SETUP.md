# Local Environment Setup Guide

## ✅ Current Status

Your local environment is now connected to the GitHub repository:
- **Repository:** https://github.com/Waleed4203/LLM-Inference-System
- **Branch:** main
- **Remote:** origin

## 🔒 Protected Files (Not Tracked by Git)

The following files/folders are protected and won't be pushed to GitHub:
- `venv/` - Your Python virtual environment
- `.env` - Your environment variables (API keys, configs)
- `logs/` - Application logs
- `__pycache__/` - Python cache files

## 📥 Getting Updates from GitHub

To pull the latest changes from the repository:

```bash
# Fetch and merge changes
git pull origin main

# If there are conflicts, you can:
# 1. Keep your local version:
git checkout --ours <file>

# 2. Keep remote version:
git checkout --theirs <file>

# 3. Then commit the merge:
git add .
git commit -m "Merged updates from remote"
```

## 📤 Pushing Your Changes

To push your local changes to GitHub:

```bash
# Check what's changed
git status

# Add files you want to commit
git add <file>
# OR add all changes
git add .

# Commit with a message
git commit -m "Your commit message"

# Push to GitHub
git push origin main
```

## 🔄 Syncing Workflow

### Daily Workflow:
```bash
# 1. Pull latest changes
git pull origin main

# 2. Make your changes
# ... edit files ...

# 3. Check status
git status

# 4. Stage changes
git add .

# 5. Commit
git commit -m "Description of changes"

# 6. Push
git push origin main
```

## 🚀 Running the System

Your environment is preserved! To run the system:

```bash
# Start Redis (if not running)
sudo systemctl start redis-server

# Start Celery Worker (Terminal 1)
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info --pool=solo

# Start FastAPI Server (Terminal 2)
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🌐 Network Access

Your server is accessible at:
- **Local:** http://localhost:8000
- **Network:** http://192.168.1.195:8000

## 🔧 Git Configuration

Current git configuration for this repository:
```bash
# View config
git config --list

# Your identity (local to this repo)
user.email=waleed4203@example.com
user.name=Waleed
```

## 📝 Important Notes

1. **Never commit `.env` file** - It contains sensitive information
2. **Virtual environment is local** - Each machine needs its own `venv/`
3. **Logs are local** - They won't be synced to GitHub
4. **Dependencies** - Always run `pip install -r requirements.txt` after pulling updates

## 🆘 Troubleshooting

### If you accidentally committed sensitive files:
```bash
# Remove from git but keep locally
git rm --cached .env
git commit -m "Remove sensitive file"
git push origin main
```

### If you want to reset to remote version:
```bash
# WARNING: This will discard local changes
git fetch origin
git reset --hard origin/main
```

### If you want to see what changed:
```bash
# Compare with remote
git diff origin/main

# See commit history
git log --oneline
```

## 🎯 Quick Commands Reference

```bash
# Status
git status

# Pull updates
git pull

# Push changes
git push

# View remote
git remote -v

# View branches
git branch -a

# Discard local changes to a file
git checkout -- <file>
```

---

**Your environment is safe and connected! Happy coding! 🚀**
