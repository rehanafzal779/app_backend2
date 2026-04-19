# Quick Deployment Checklist

## ✅ Files Created for Replit Deployment

### Configuration Files
- ✓ `.replit` - Main Replit configuration (runs Django server)
- ✓ `replit.nix` - Python environment dependencies  
- ✓ `config/settings/replit.py` - Replit-specific Django settings
- ✓ `wsgi_replit.py` - Alternative WSGI entry point

### Dependencies & Setup
- ✓ `requirements/replit.txt` - Lightweight dependencies (no PyTorch/YOLO)
- ✓ `.gitignore` - Git ignore rules for Django/Replit
- ✓ `setup_replit.sh` - Automated setup script

### Documentation
- ✓ `REPLIT_DEPLOYMENT.md` - Complete deployment guide
- ✓ `QUICK_REFERENCE.md` - This file

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Setup Replit deployment"
git push origin main
```

### Step 2: Create Replit Project
1. Go to https://replit.com
2. Click "Create" → "Import from GitHub"
3. Paste your repo URL
4. Click "Import"

### Step 3: Run Setup (in Replit Shell)
```bash
bash setup_replit.sh
```

### Step 4: Start Server
Click the **"Run"** button in Replit

### Step 5: Access Your App
```
https://your-username.repl.co
Admin: https://your-username.repl.co/admin/
```

---

## 📋 What's Configured

| Component | Status | Notes |
|-----------|--------|-------|
| Django | ✓ | v5.0.1 |
| REST API | ✓ | DRF configured |
| Authentication | ✓ | JWT tokens |
| Database | ✓ | SQLite (free tier) |
| Static Files | ✓ | Configured |
| CORS | ✓ | Replit domain included |
| Email | ⚠️ | Console backend (dev mode) |
| Background Tasks | ⚠️ | Disabled (no Redis) |
| ML Models | ❌ | Too large for free tier |

---

## ⚠️ Important Limitations (Free Tier)

- **Storage**: ~1GB (no PyTorch/YOLO models)
- **RAM**: ~128MB (lightweight ops only)
- **Uptime**: Auto-sleeps after 1 hour inactivity
- **Background Jobs**: Not available (Celery disabled)
- **Database**: SQLite only (no PostgreSQL)

---

## 🔧 Manual Commands (if needed)

### Install Dependencies
```bash
pip install -r requirements/replit.txt
```

### Run Migrations
```bash
python manage.py migrate
```

### Create Admin User
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Start Server
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 📝 Environment Variables

If needed, add these in Replit **Secrets** (🔒 icon):

```
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-username.repl.co
```

---

## 🔐 Security Notes

✓ SSL redirect enabled
✓ Security headers configured
✓ CSRF protection enabled
✓ XSS protection enabled

⚠️ Default admin password: Change immediately!
⚠️ SECRET_KEY: Update in production

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| 502 Bad Gateway | Check recent changes, click "Run" again |
| Database Locked | Clear data: `rm db.sqlite3` then migrate |
| Import Errors | Reinstall: `pip install -r requirements/replit.txt --force-reinstall` |
| Static Files Missing | Run: `python manage.py collectstatic --noinput` |
| Port in Use | Replit handles this automatically |

---

## 🎯 Next Steps

1. **Update Frontend Domain**: Modify `CORS_ALLOWED_ORIGINS` in `config/settings/replit.py`
2. **Email Service**: Configure email backend for production
3. **Database Backups**: Periodically export SQLite database
4. **Upgrade to Replit Pro** (if needed):
   - Persistent uptime (24/7)
   - More storage & RAM
   - Background processes
   - Better performance

---

## 📚 Useful Links

- [Replit Docs](https://docs.replit.com)
- [Django Docs](https://docs.djangoproject.com)
- [DRF Docs](https://www.django-rest-framework.org)
- [JWT Docs](https://django-rest-framework-simplejwt.readthedocs.io)

---

**Setup by**: Django Deployment Assistant
**Date**: 2024
**Status**: ✅ Ready for deployment
