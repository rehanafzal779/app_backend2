#!/bin/bash
# Replit Setup Script
# Run this script on first deployment: bash setup_replit.sh

echo "=========================================="
echo "Django Replit Setup Script"
echo "=========================================="

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements/replit.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if superuser exists
echo "Setting up admin user..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✓ Superuser 'admin' created (username: admin, password: admin123)")
    print("  IMPORTANT: Change this password in production!")
else:
    print("✓ Admin user already exists")
END

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Start the server by clicking the 'Run' button"
echo "Or manually run: python manage.py runserver 0.0.0.0:8000"
echo ""
echo "Access your app at: https://YOUR-USERNAME.repl.co"
echo "Admin panel: https://YOUR-USERNAME.repl.co/admin/"
echo ""
echo "Default credentials (if created):"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "IMPORTANT: Change these credentials immediately in production!"
