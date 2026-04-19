# Replit Deployment Guide

## Overview
This Django application is configured for deployment on Replit with the following setup:

- **Framework**: Django 5.0.1
- **API**: Django REST Framework
- **Database**: SQLite (no external DB needed on free tier)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **CORS**: Configured for Replit domain
- **Security**: Production-ready with SSL redirect and security headers

## Prerequisites
- Replit account (free tier is sufficient)
- GitHub repository with this code (for easy import to Replit)

## Deployment Steps

### 1. Import to Replit
1. Go to [replit.com](https://replit.com)
2. Click "Create" → "Import from GitHub"
3. Paste your repository URL
4. Replit will auto-detect Python and create the environment

### 2. Set Environment Variables (if needed)
In Replit Secrets (gear icon):
```
DEBUG=False
ALLOWED_HOSTS=your-replit-username.repl.co
SECRET_KEY=your-secret-key-here
```

### 3. Install Dependencies
The `.replit` file and `replit.nix` will automatically install dependencies.

Run in Replit shell (if not automatic):
```bash
pip install -r requirements/replit.txt
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Collect Static Files (if using production)
```bash
python manage.py collectstatic --noinput
```

### 6. Create Superuser (optional, for admin panel)
```bash
python manage.py createsuperuser
```

### 7. Start Server
Click the "Run" button in Replit. The server will start at:
```
https://your-replit-username.repl.co
```

## Important Notes

### ML Models (PyTorch, YOLO)
The free Replit tier (~1GB storage) cannot accommodate PyTorch and YOLO models due to size constraints. 
- If you need ML features: Consider upgrading to Replit Pro or using external ML APIs
- Current setup uses lightweight dependencies suitable for free tier

### Database
- Using SQLite for simplicity (no external database required)
- To upgrade to PostgreSQL: Update `config/settings/replit.py`

### Celery/Redis
- Disabled on free tier (no Redis available)
- Task queueing is disabled with `CELERY_TASK_ALWAYS_EAGER = True`
- For background jobs, upgrade to Replit Pro or use external service

### Email
- Currently uses console backend (emails print to logs)
- To enable actual email: Add credentials to environment variables and update settings

## API Documentation

### Health Check
```
GET /health/
```

### Admin Panel
```
https://your-replit-username.repl.co/admin/
```

## Updating the Code
Simply push changes to your GitHub repository. Replit will auto-pull on refresh.

## Troubleshooting

### Port Already in Use
Replit automatically assigns ports. The app uses port 8000 by default.

### Database Locked
If you see SQLite database locked errors:
```bash
python manage.py migrate --verbosity 2
```

### Import Errors
If you see import errors after deployment:
```bash
pip install -r requirements/replit.txt --force-reinstall
```

### Static Files Not Loading
Run:
```bash
python manage.py collectstatic --clear --noinput
```

## Limitations of Free Replit Tier
- ~1GB storage
- ~128MB RAM
- Cannot run memory-intensive tasks (ML models)
- No persistent background processes
- Server stops after 1 hour of inactivity (no premium)

## Next Steps
- Set up frontend domain in `CORS_ALLOWED_ORIGINS` in `config/settings/replit.py`
- Configure email backend for production
- Add database backups (SQLite exports)
- Consider Replit Pro for better performance and persistent uptime
