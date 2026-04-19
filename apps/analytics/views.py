from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db. models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated
from apps.accounts.models import Account
from apps.workers.models import Worker
from apps. reports.models import Report
from .models import UserMonthlyStats, WorkerMonthlyStats

from apps.admins.permissions import IsAdmin
from apps.admins.authentication import AdminJWTAuthentication
class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/
    Get overall dashboard statistics
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            # Reports stats
            total_reports = Report.objects.count()
            pending_reports = Report.objects.filter(status='Pending').count()
            assigned_reports = Report.objects.filter(status='Assigned').count()
            in_progress_reports = Report.objects.filter(status='In Progress').count()
            resolved_reports = Report.objects.filter(status='Resolved').count()
            
            # Workers stats
            total_workers = Worker.objects.count()
            active_workers = Worker.objects.filter(worker_id__is_active=True).count()
            tracking_workers = Worker.objects.filter(is_tracking=True).count()
            
            # Citizens stats
            total_citizens = Account.objects.filter(role='Citizen').count()
            active_citizens = Account.objects.filter(role='Citizen', is_active=True).count()
            
            return Response({
                'success': True,
                'data':  {
                    'reports':  {
                        'total':  total_reports,
                        'pending': pending_reports,
                        'assigned': assigned_reports,
                        'in_progress':  in_progress_reports,
                        'resolved': resolved_reports
                    },
                    'workers': {
                        'total':  total_workers,
                        'active': active_workers,
                        'tracking': tracking_workers
                    },
                    'citizens': {
                        'total':  total_citizens,
                        'active': active_citizens
                    }
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TopCitizensView(APIView):
    """
    GET /api/dashboard/top-citizens/
    Get top citizens by report count
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            
            # Get citizens with their report counts
            top_citizens = Account.objects.filter(
                role='Citizen'
            ).annotate(
                report_count=Count('submitted_reports')
            ).filter(
                report_count__gt=0
            ).order_by('-report_count')[:limit]
            
            # Format response
            data = []
            for citizen in top_citizens:
                # Get verified reports count
                verified_count = Report.objects.filter(
                    citizen_id=citizen,
                    ai_result='Waste'
                ).count()
                
                # ✅ Get profile image URL (not the ImageField object)
                profile_image_url = None
                if citizen.profile_image:
                    request = self.request
                    if request:
                        profile_image_url = request.build_absolute_uri(citizen.profile_image.url)
                    else:
                        profile_image_url = citizen.profile_image.url
                
                data.append({
                    'citizen_id': citizen.account_id,
                    'name': citizen.name,
                    'email': citizen.email,
                    'total_reports': citizen.report_count,
                    'verified_reports': verified_count,
                    'profile_image': profile_image_url,  # ✅ Return URL string, not ImageField object
                    'created_at': citizen.created_at.isoformat()
                })
            
            return Response({
                'success': True,
                'count': len(data),
                'data': data
            })
            
        except Exception as e: 
            return Response({
                'success': False,
                'error':  str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TopWorkersView(APIView):
    """
    GET /api/dashboard/top-workers/
    Get top workers by performance
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
            
            # Get top workers
            top_workers = Worker.objects.select_related('worker_id').order_by(
                '-avg_rating', '-total_tasks'
            )[:limit]
            
            data = []
            for worker in top_workers:
                # Get active tasks
                active_tasks = Report.objects.filter(
                    worker_id=worker,
                    status__in=['Assigned', 'In Progress']
                ).count()
                
                # ✅ Get profile image URL (not the ImageField object)
                profile_image_url = None
                if worker.worker_id.profile_image:
                    request = self.request
                    if request:
                        profile_image_url = request.build_absolute_uri(worker.worker_id.profile_image.url)
                    else:
                        profile_image_url = worker.worker_id.profile_image.url
                
                data.append({
                    'worker_id': worker.worker_id.account_id,
                    'employee_code': worker.employee_code,
                    'name': worker.worker_id.name,
                    'email': worker.worker_id.email,
                    'total_tasks': worker.total_tasks,
                    'avg_rating': float(worker.avg_rating),
                    'active_tasks': active_tasks,
                    'is_tracking': worker.is_tracking,
                    'profile_image': profile_image_url  # ✅ Return URL string, not ImageField object
                })
            
            return Response({
                'success': True,
                'count': len(data),
                'data': data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecentActivitiesView(APIView):
    """
    GET /api/dashboard/activities/
    Get recent activities
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 20))
            
            from apps.tracking.models import ActivityLog
            
            activities = ActivityLog.objects.select_related().order_by('-created_at')[:limit]
            
            data = []
            for activity in activities:
                data.append({
                    'id': activity.log_id,
                    'type': activity.action. lower(),
                    'message': activity.description or f"{activity.actor_type} {activity.action} {activity.target_type}",
                    'timestamp': activity.created_at.isoformat(),
                    'actor_type': activity.actor_type,
                    'actor_id': activity.actor_id,
                    'target_type':  activity.target_type,
                    'target_id': activity. target_id
                })
            
            return Response({
                'success': True,
                'count': len(data),
                'data': data
            })
            
        except Exception as e: 
            return Response({
                'success': False,
                'error':  str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrendDataView(APIView):
    """
    GET /api/dashboard/trends/
    Get trend data for charts
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            days = int(request.query_params.get('days', 7))
            
            data = []
            for i in range(days):
                date = timezone.now().date() - timedelta(days=days - i - 1)
                
                # Count reports submitted on this day
                reports_count = Report.objects.filter(
                    submitted_at__date=date
                ).count()
                
                # Count reports resolved on this day (use __date lookup to avoid naive datetime warning)
                resolved_count = Report.objects.filter(
                    resolved_at__date=date  # ✅ Use __date lookup instead of direct date comparison
                ).count()
                
                data.append({
                    'date': date.strftime('%b %d'),
                    'reports':  reports_count,
                    'resolved': resolved_count
                })
            
            return Response({
                'success': True,
                'data': data
            })
            
        except Exception as e: 
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatusDistributionView(APIView):
    """
    GET /api/dashboard/status-distribution/
    Get report status distribution
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            distribution = Report.objects.values('status').annotate(
                count=Count('report_id')
            )
            
            # Define colors for each status
            status_colors = {
                'Pending': '#ef4444',
                'Assigned': '#f59e0b',
                'In Progress': '#3b82f6',
                'Resolved': '#10b981',
                'Rejected': '#dc2626'
            }
            
            data = []
            for item in distribution:
                data.append({
                    'name': item['status'],
                    'value': item['count'],
                    'color': status_colors.get(item['status'], '#6b7280')
                })
            
            return Response({
                'success': True,
                'data': data
            })
            
        except Exception as e: 
            return Response({
                'success': False,
                'error':  str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ZoneStatsView(APIView):
    """
    GET /api/dashboard/zone-stats/
    Get statistics by zone
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    def get(self, request):
        try:
            # Get reports grouped by zone
            zone_stats = Report.objects.values('zone').annotate(
                total_reports=Count('report_id'),
                pending=Count('report_id', filter=Q(status='Pending')),
                resolved=Count('report_id', filter=Q(status='Resolved'))
            ).order_by('-total_reports')
            
            data = list(zone_stats)
            
            return Response({
                'success': True,
                'count': len(data),
                'data': data
            })
            
        except Exception as e: 
            return Response({
                'success': False,
                'error':  str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)