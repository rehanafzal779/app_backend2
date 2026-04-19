from django. urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkerViewSet, WorkerRankingsView, WorkerStatsView, WorkerAnalyticsView

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = DefaultRouter()
router.register(r'', WorkerViewSet, basename='worker')

# ============================================
# URL PATTERNS
# ============================================

urlpatterns = [
    # Worker ViewSet routes (all CRUD + custom actions)
    # GET    /api/workers/              - List workers
    # POST   /api/workers/              - Create worker
    # GET    /api/workers/{id}/         - Get worker detail
    # PUT    /api/workers/{id}/         - Update worker (full)
    # PATCH  /api/workers/{id}/         - Update worker (partial)
    # DELETE /api/workers/{id}/         - Delete worker
    # POST   /api/workers/{id}/toggle_active/      - Toggle active status
    # POST   /api/workers/{id}/start_tracking/     - Start GPS tracking
    # POST   /api/workers/{id}/stop_tracking/      - Stop GPS tracking
    # GET    /api/workers/{id}/reports/            - Get worker's reports
    # GET    /api/workers/{id}/statistics/         - Get worker stats
    # GET    /api/workers/{id}/location_history/   - Get location history
    # GET    /api/workers/top_performers/          - Get top performers
    # GET    /api/workers/available/               - Get available workers
    # GET    /api/workers/rankings/                - Get worker rankings/leaderboard
    # GET    /api/workers/stats/                   - Get worker stats (pending, done, average time)
    # GET    /api/workers/analytics/                - Get worker analytics (Total, Done, Rate, Time, graphs)
    path('rankings/', WorkerRankingsView.as_view(), name='worker-rankings'),
    path('stats/', WorkerStatsView.as_view(), name='worker-stats'),
    path('analytics/', WorkerAnalyticsView.as_view(), name='worker-analytics'),
    path('', include(router.urls)),
]