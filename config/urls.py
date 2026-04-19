from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ==================== HEALTH CHECK ====================

@csrf_exempt
def health_check(request):
    """Simple health check endpoint for Flutter app"""
    return JsonResponse({
        'status': 'ok',
        'message': 'Server is running',
        'debug':  settings.DEBUG,
    })

# ==================== URL PATTERNS ====================

urlpatterns = [
    # ==================== DJANGO ADMIN ====================
    path('admin/', admin.site.urls),
    
    # ==================== HEALTH CHECK ====================
    path('api/health/', health_check, name='health-check'),
    path('health/', health_check, name='health-check-root'),  # Alternative path
    
    # ==================== JWT TOKEN ====================
    path('api/token/refresh/', TokenRefreshView. as_view(), name='token_refresh'),
    
    # ==================== ACCOUNTS (Citizens & Workers Authentication) ====================
    path('api/accounts/', include('apps.accounts.urls')),  # ✅ Main auth endpoints
    # path('api/accounts/', include('apps.accounts.session_urls')),  # ✅ Session management (if created)
    
    # ==================== ADMIN PANEL ====================
    path('api/admin/', include('apps.admins.urls')),
    
    # ==================== WORKERS ====================
    path('api/workers/', include('apps.workers.urls')),
    
    # ==================== REPORTS ====================
    path('api/reports/', include('apps.reports.urls')),
    
    # ==================== FEEDBACK ====================
    path('api/feedback/', include('apps.feedback.urls')),
    
    # ==================== TRACKING ====================
    #path('api/tracking/', include('apps.tracking.urls')),
    
    # ==================== NOTIFICATIONS ====================
    path('api/notifications/', include('apps.notifications.urls')),
  
    path('admin/', admin. site.urls),
    path('/', include('apps.accounts.urls')),  # ← This is what I need to see
    # ==================== ANALYTICS & DASHBOARD ====================
    path('api/dashboard/', include('apps.analytics.urls')),
    path('api/analytics/', include('apps.analytics.urls')),  # Alternative path
]

# ==================== MEDIA & STATIC FILES (Development) ====================

if settings.DEBUG:
    # Serve media files (user uploads:  profile images, report photos)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Serve static files (CSS, JS, admin panel assets)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar (install with: pip install django-debug-toolbar)
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# ==================== CUSTOM ADMIN SITE BRANDING ====================

admin.site.site_header = 'NeatNow Waste Management System'
admin.site.site_title = 'NeatNow Admin Portal'
admin.site.index_title = 'Welcome to NeatNow Administration'

# ==================== CUSTOM ERROR HANDLERS ====================

# handler404 = 'core.views.custom_404'
# handler500 = 'core.views.custom_500'
# handler403 = 'core. views.custom_403'
# handler400 = 'core. views.custom_400'