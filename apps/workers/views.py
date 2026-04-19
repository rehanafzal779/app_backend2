from rest_framework import viewsets, status
from rest_framework. decorators import action
from rest_framework. response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework. parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg, F
from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.utils. crypto import get_random_string
from django.utils import timezone
from datetime import datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework_simplejwt.authentication import JWTAuthentication
from . models import Worker, WorkerLocation, WorkerMonthlyStats
from apps.admins.permissions import IsAdmin
from apps.admins.authentication import AdminJWTAuthentication
from . serializers import (
    WorkerListSerializer,
    WorkerDetailSerializer,
    WorkerCreateSerializer,
    WorkerUpdateSerializer,
    WorkerLocationSerializer,
    WorkerMonthlyStatsSerializer
)
import logging

logger = logging.getLogger(__name__)


class WorkerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Worker CRUD operations
    ✅ WITH IMAGE UPLOAD SUPPORT
    ✅ WITH PASSWORD RESET EMAIL
    ✅ WITH PUSH NOTIFICATIONS
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [AdminJWTAuthentication]
    
    # ✅ ADD PARSERS FOR FILE UPLOAD
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Filtering
    filterset_fields = ['is_tracking', 'worker_id__is_active']
    
    # Searching
    search_fields = ['employee_code', 'worker_id__name', 'worker_id__email']
    
    # Ordering
    ordering_fields = ['total_tasks', 'avg_rating', 'worker_id__name']
    ordering = ['-avg_rating']
    
    def get_queryset(self):
        """Get workers with optional filters"""
        queryset = Worker.objects. select_related('worker_id').all()
        
        # Filter by active status
        is_active = self. request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active. lower() in ['true', '1', 'yes']
            queryset = queryset.filter(worker_id__is_active=is_active_bool)
        
        # Filter by tracking status
        is_tracking = self.request. query_params.get('is_tracking')
        if is_tracking is not None: 
            is_tracking_bool = is_tracking.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_tracking=is_tracking_bool)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self. action == 'list':
            return WorkerListSerializer
        elif self.action == 'retrieve':
            return WorkerDetailSerializer
        elif self.action == 'create': 
            return WorkerCreateSerializer
        elif self.action in ['update', 'partial_update']: 
            return WorkerUpdateSerializer
        return WorkerListSerializer
    
    def list(self, request, *args, **kwargs):
        """List workers with pagination"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer. data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success':  True,
            'count': queryset. count(),
            'results': serializer. data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get single worker details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Create new worker - ✅ WITH IMAGE SUPPORT"""
        print("📸 FILES:", request.FILES)
        print("📝 DATA:", request.data)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        worker = serializer.save()
        
        detail_serializer = WorkerDetailSerializer(worker)
        return Response({
            'success': True,
            'message': 'Worker created successfully',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update worker - ✅ WITH IMAGE SUPPORT"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        print("📸 FILES:", request.FILES)
        print("📝 DATA:", request.data)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        worker = serializer.save()
        
        detail_serializer = WorkerDetailSerializer(worker)
        return Response({
            'success': True,
            'message': 'Worker updated successfully',
            'data': detail_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete worker (cascade delete account)"""
        instance = self.get_object()
        employee_code = instance. employee_code
        
        instance.worker_id.delete()
        
        return Response({
            'success': True,
            'message': f'Worker {employee_code} deleted successfully'
        }, status=status.HTTP_200_OK)
    
    # ============================================
    # ✅ PASSWORD RESET ENDPOINT
    # ============================================
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """
        Send password reset email to worker
        POST /api/workers/{id}/reset_password/
        """
        worker = self.get_object()
        account = worker.worker_id
        
        if not account: 
            return Response({
                'success':  False,
                'message': 'Worker has no associated account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not account.email:
            return Response({
                'success': False,
                'message': 'Worker has no email address configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Generate a secure temporary password
            temp_password = get_random_string(
                length=12, 
                allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789! @#$%'
            )
            
            # Set the temporary password
            account. set_password(temp_password)
            account.save()
            
            # Prepare email content
            subject = '🔐 Password Reset - Neat Now Cleanup System'
            
            html_message = f'''
<! DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family:  'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a;">
    <div style="max-width:  600px; margin: 0 auto; padding: 20px;">
        <div style="background:  linear-gradient(135deg, #10b981 0%, #14b8a6 50%, #06b6d4 100%); padding: 40px 30px; border-radius: 16px 16px 0 0; text-align: center;">
            <h1 style="color:  white; margin: 0; font-size: 28px; font-weight: 700;">
                🔐 Password Reset
            </h1>
            <p style="color: rgba(255,255,255,0.9); margin:  10px 0 0 0; font-size: 14px;">
                Neat Now Cleanup System
            </p>
        </div>
        <div style="background:  #1e293b; padding: 40px 30px; border-radius: 0 0 16px 16px;">
            <p style="color: #e2e8f0; font-size: 16px; line-height: 1.6; margin:  0 0 20px 0;">
                Hello <strong style="color: #10b981;">{account.name}</strong>,
            </p>
            <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 0 0 30px 0;">
                Your password has been reset by an administrator.  Please use the temporary password below to log in.
            </p>
            <div style="background:  linear-gradient(135deg, #10b981 0%, #14b8a6 100%); border-radius: 12px; padding: 3px; margin: 0 0 30px 0;">
                <div style="background: #0f172a; border-radius: 10px; padding: 25px; text-align: center;">
                    <p style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 10px 0;">
                        Your Temporary Password
                    </p>
                    <p style="color: #10b981; font-size: 28px; font-weight: 700; letter-spacing: 3px; margin: 0; font-family: 'Courier New', monospace;">
                        {temp_password}
                    </p>
                </div>
            </div>
            <div style="background: rgba(245, 158, 11, 0.1); border:  1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 15px; margin: 0 0 30px 0;">
                <p style="color: #fbbf24; font-size: 14px; margin: 0;">
                    ⚠️ <strong>Important:</strong> Please change your password immediately after logging in.
                </p>
            </div>
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 15px;">
                <p style="color: #f87171; font-size: 13px; margin: 0;">
                    🔒 <strong>Security Notice:</strong> If you did not request this, contact your administrator immediately.
                </p>
            </div>
            <hr style="border: none; border-top: 1px solid #334155; margin: 30px 0;">
            <p style="color: #64748b; font-size: 12px; text-align: center; margin:  0;">
                This is an automated message from Neat Now Cleanup System. 
            </p>
        </div>
    </div>
</body>
</html>
            '''
            
            plain_message = f'''
Hello {account.name},

Your password has been reset by an administrator. 

Your new temporary password is: {temp_password}

IMPORTANT: Please change your password immediately after logging in. 

Best regards,
Neat Now Team
            '''
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'rehanafzal779@gmail.com',
                recipient_list=[account.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f'✅ Password reset email sent to:  {account.email} for worker: {worker.employee_code}')
            
            return Response({
                'success': True,
                'message':  f'Password reset email sent successfully to {account.email}',
                'email':  account.email
            })
            
        except Exception as e:
            logger.error(f'❌ Failed to send password reset email to {account.email}:  {str(e)}')
            return Response({
                'success': False,
                'message': 'Failed to send password reset email.  Please check email configuration.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ============================================
    # ✅ SEND NOTIFICATION ENDPOINT
    # ============================================
    @action(detail=True, methods=['post'])
    def notify(self, request, pk=None):
        """
        Send push notification to worker
        POST /api/workers/{id}/notify/
        
        Request body:
        {
            "title": "Notification Title",
            "body": "Notification message",
            "data": {}  // Optional extra data
        }
        """
        worker = self.get_object()
        account = worker.worker_id
        
        title = request.data.get('title', 'Notification from Admin')
        body = request.data.get('body', '')
        data = request.data.get('data', {})
        
        if not body:
            return Response({
                'success': False,
                'message': 'Notification body is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # ============================================
            # ✅ Store notification in database
            # ============================================
            from apps.notifications.models import Notification
            
            notification = Notification.objects.create(
                recipient_type='worker',
                recipient_id=worker.pk,
                #title=title,
                message=body,
                #data=data,
                is_read=False
            )
            
            logger.info(f'📤 Notification #{notification.notification_id} created for worker {worker.employee_code}')
            
            # ============================================
            # Optional: Send push notification via FCM
            # ============================================
            push_sent = False
            
            # Uncomment if using Firebase
            '''
            try:
                if hasattr(account, 'fcm_token') and account.fcm_token:
                    import firebase_admin
                    from firebase_admin import messaging
                    
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body,
                        ),
                        data={str(k): str(v) for k, v in data. items()},
                        token=account.fcm_token,
                    )
                    response = messaging.send(message)
                    push_sent = True
                    logger.info(f'📤 FCM push sent: {response}')
            except Exception as fcm_error: 
                logger.warning(f'FCM push failed: {fcm_error}')
            '''
            
            # ============================================
            # Optional: Send email as fallback
            # ============================================
            email_sent = False
            
            if account and account.email:
                try:
                    send_mail(
                        subject=f'📢 {title}',
                        message=f'{body}\n\n---\nThis notification was sent from the Neat Now admin panel.',
                        from_email='rehanafzal779@gmail.com',
                        recipient_list=[account.email],
                        fail_silently=True,
                    )
                    email_sent = True
                    logger.info(f'📧 Email notification sent to {account.email}')
                except Exception as email_error:
                    logger.warning(f'Email notification failed: {email_error}')
            
            return Response({
                'success': True,
                'message': f'Notification sent to {account.name if account else "worker"}',
                'notification_id': notification.notification_id,
                'email':  account.email if account else None,
                'details': {
                    'stored_in_db': True,
                    'push_sent': push_sent,
                    'email_sent':  email_sent
                }
            }, status=status.HTTP_201_CREATED)
            
        except ImportError:
            # Notification app not installed, fall back to email only
            logger.warning('Notification app not installed, sending email only')
            
            if account and account.email:
                try:
                    send_mail(
                        subject=f'📢 {title}',
                        message=f'{body}\n\n---\nThis notification was sent from the Neat Now admin panel.',
                        from_email='rehanafzal779@gmail.com',
                        recipient_list=[account.email],
                        fail_silently=False,
                    )
                    
                    return Response({
                        'success': True,
                        'message': f'Notification sent via email to {account.email}',
                        'email': account.email
                    })
                except Exception as e:
                    logger.error(f'Failed to send email: {e}')
                    return Response({
                        'success': False,
                        'message': 'Failed to send notification',
                        'error': str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'success': False,
                    'message': 'Worker has no email and notification system not configured'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e: 
            logger.error(f'❌ Failed to send notification to worker {pk}: {str(e)}')
            return Response({
                'success': False,
                'message': 'Failed to send notification',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ============================================
    # ✅ SEND EMAIL ENDPOINT
    # ============================================
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """
        Send custom email to worker
        POST /api/workers/{id}/send_email/
        """
        worker = self.get_object()
        account = worker.worker_id
        
        if not account or not account.email:
            return Response({
                'success':  False,
                'message': 'Worker has no email address configured'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subject = request.data.get('subject', 'Message from Neat Now Admin')
        message = request.data. get('message', '')
        
        if not message:
            return Response({
                'success': False,
                'message': 'Email message content is required'
            }, status=status. HTTP_400_BAD_REQUEST)
        
        try: 
            html_message = f'''
<! DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background-color: #0f172a; padding: 20px;">
    <div style="max-width:  600px; margin: 0 auto; background:  #1e293b; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #10b981, #14b8a6); padding: 30px; text-align: center;">
            <h1 style="color:  white; margin: 0;">📧 Message from Admin</h1>
        </div>
        <div style="padding: 30px;">
            <p style="color:  #e2e8f0; font-size:  16px;">Hello <strong>{account.name}</strong>,</p>
            <div style="color: #94a3b8; font-size: 14px; line-height:  1.8; white-space: pre-wrap;">{message}</div>
            <hr style="border: none; border-top:  1px solid #334155; margin:  30px 0;">
            <p style="color: #64748b; font-size: 12px; text-align: center;">
                This email was sent from the Neat Now admin panel.
            </p>
        </div>
    </div>
</body>
</html>
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL or 'rehanafzal779@gmail. com',
                recipient_list=[account. email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger. info(f'✅ Email sent to worker {worker.employee_code} at {account.email}')
            
            return Response({
                'success': True,
                'message':  f'Email sent successfully to {account.email}'
            })
            
        except Exception as e: 
            logger.error(f'❌ Failed to send email to {account.email}: {str(e)}')
            return Response({
                'success':  False,
                'message': 'Failed to send email',
                'error': str(e)
            }, status=status. HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ============================================
    # ✅ GET WORKER ASSIGNMENTS
    # ============================================
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """
        Get worker's current assignments
        GET /api/workers/{id}/assignments/
        """
        worker = self.get_object()
        
        try:
            from apps.reports.models import Report
            
            # Get active assignments (not resolved)
            assignments = Report.objects.filter(
                worker_id=worker,
                status__in=['Assigned', 'In Progress', 'Pending']
            ).order_by('-assigned_at')
            
            data = []
            for report in assignments:
                data.append({
                    'id':  str(report.id),
                    'report_id': report.report_id if hasattr(report, 'report_id') else str(report.id),
                    'location': report.location if hasattr(report, 'location') else '',
                    'address': report.address if hasattr(report, 'address') else '',
                    'status': report.status,
                    'waste_type': report.waste_type if hasattr(report, 'waste_type') else 'General',
                    'category': report.category if hasattr(report, 'category') else '',
                    'priority': report.priority if hasattr(report, 'priority') else 'normal',
                    'created_at': report. created_at.isoformat() if report.created_at else None,
                    'assigned_at': report.assigned_at.isoformat() if hasattr(report, 'assigned_at') and report.assigned_at else None,
                    'due_date': report.due_date.isoformat() if hasattr(report, 'due_date') and report.due_date else None,
                })
            
            return Response({
                'success': True,
                'count': len(data),
                'data': data
            })
            
        except ImportError:
            logger.warning('Report model not available')
            return Response({
                'success':  True,
                'count': 0,
                'data': []
            })
        except Exception as e: 
            logger.error(f'Error fetching assignments: {str(e)}')
            return Response({
                'success': True,
                'count': 0,
                'data': []
            })
    
    # ============================================
    # ✅ GET WORKER ACTIVITY LOG
    # ============================================
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """
        Get worker's activity log
        GET /api/workers/{id}/activity/
        """
        worker = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        
        try:
            # Try to get from ActivityLog model if it exists
            from apps.core.models import ActivityLog
            
            activities = ActivityLog.objects.filter(
                user=worker.worker_id
            ).order_by('-created_at')[:limit]
            
            data = [{
                'id':  str(log.id),
                'action': log.action,
                'description': log.description if hasattr(log, 'description') else log.action,
                'timestamp': log.created_at.isoformat(),
                'created_at': log.created_at.isoformat(),
                'report_id': str(log.report_id) if hasattr(log, 'report_id') and log.report_id else None,
            } for log in activities]
            
            return Response({
                'success': True,
                'count':  len(data),
                'data': data
            })
            
        except ImportError:
            # ActivityLog model doesn't exist, return report history as activity
            try:
                from apps.reports.models import Report
                
                reports = Report.objects.filter(
                    worker_id=worker
                ).order_by('-updated_at')[:limit]
                
                data = []
                for report in reports: 
                    action = f"Report {report.status}"
                    if report.status == 'Resolved':
                        action = f"Completed cleanup at {report.address if hasattr(report, 'address') else 'location'}"
                    elif report.status == 'Assigned':
                        action = f"Assigned to cleanup task"
                    elif report.status == 'In Progress':
                        action = f"Started working on task"
                    
                    data.append({
                        'id': str(report.id),
                        'action': action,
                        'description': f"Report #{report.id} - {report.status}",
                        'timestamp': report. updated_at.isoformat() if report.updated_at else report.created_at. isoformat(),
                        'created_at': report.created_at.isoformat(),
                        'report_id':  str(report.id),
                    })
                
                return Response({
                    'success': True,
                    'count': len(data),
                    'data': data
                })
                
            except Exception as e:
                logger.error(f'Error fetching activity from reports: {str(e)}')
        
        except Exception as e:
            logger.error(f'Error fetching activity log: {str(e)}')
        
        # Return empty if nothing works
        return Response({
            'success':  True,
            'count': 0,
            'data':  []
        })
    
    # ============================================
    # EXISTING ENDPOINTS
    # ============================================
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        """✅ DEDICATED ENDPOINT FOR PHOTO UPLOAD"""
        worker = self.get_object()
        
        if 'photo' not in request.FILES: 
            return Response({
                'success': False,
                'message': 'No photo provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        photo = request.FILES['photo']
        
        if worker.worker_id. profile_photo: 
            worker.worker_id.profile_photo.delete(save=False)
        
        worker. worker_id.profile_photo = photo
        worker.worker_id.save()
        
        return Response({
            'success': True,
            'message': 'Photo uploaded successfully',
            'photo_url': request.build_absolute_uri(worker.worker_id. profile_photo.url) if worker.worker_id.profile_photo else None
        })
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle worker active status"""
        worker = self.get_object()
        worker.worker_id.is_active = not worker. worker_id.is_active
        worker.worker_id. save()
        
        return Response({
            'success': True,
            'message': f'Worker status changed to {"active" if worker. worker_id.is_active else "inactive"}',
            'is_active': worker. worker_id.is_active
        })
    
    @action(detail=True, methods=['post'])
    def start_tracking(self, request, pk=None):
        """Start GPS tracking for worker"""
        worker = self. get_object()
        worker.is_tracking = True
        worker.save()
        
        return Response({
            'success': True,
            'message': 'Tracking started',
            'is_tracking': True
        })
    
    @action(detail=True, methods=['post'])
    def stop_tracking(self, request, pk=None):
        """Stop GPS tracking for worker"""
        worker = self.get_object()
        worker.is_tracking = False
        worker.save()
        
        return Response({
            'success': True,
            'message':  'Tracking stopped',
            'is_tracking': False
        })
    
    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        """Get worker's assigned reports"""
        worker = self.get_object()
        
        from apps.reports.models import Report
        from apps.reports.serializers import ReportListSerializer
        
        reports = Report.objects. filter(worker_id=worker)
        
        status_filter = request. query_params.get('status')
        if status_filter: 
            reports = reports.filter(status=status_filter)
        
        serializer = ReportListSerializer(reports, many=True)
        
        return Response({
            'success': True,
            'count': reports.count(),
            'data':  serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get worker statistics"""
        worker = self.get_object()
        
        from apps.reports.models import Report
        from django.db.models import Avg
        from django.utils import timezone
        from datetime import timedelta
        
        days = int(request.query_params.get('days', 30))
        start_date = timezone. now() - timedelta(days=days)
        
        reports = Report.objects. filter(
            worker_id=worker, 
            resolved_at__gte=start_date, 
            status='Resolved'
        )
        
        performance = {
            'total_resolved': reports.count(),
            'avg_rating': reports.aggregate(Avg('rating'))['rating__avg'] or 0,
            'period_days': days
        }
        
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_stat = WorkerMonthlyStats.objects.filter(
            worker_id=worker,
            month_year=current_month. strftime('%Y-%m')
        ).first()
        
        monthly = {
            'resolved_tasks': monthly_stat.resolved_tasks if monthly_stat else 0,
            'avg_rating': float(monthly_stat. avg_rating) if monthly_stat else 0,
            'badge':  monthly_stat.badge if monthly_stat else 'None',
            'monthly_rank': monthly_stat. monthly_rank if monthly_stat else None
        }
        
        lifetime = {
            'total_tasks': worker.total_tasks,
            'avg_rating': float(worker.avg_rating),
            'employee_code': worker.employee_code
        }
        
        return Response({
            'success': True,
            'data': {
                'performance': performance,
                'monthly': monthly,
                'lifetime': lifetime
            }
        })
    
    @action(detail=True, methods=['get'])
    def location_history(self, request, pk=None):
        """Get worker's location history"""
        worker = self.get_object()
        
        hours = int(request. query_params.get('hours', 24))
        
        from django.utils import timezone
        from datetime import timedelta
        
        start_time = timezone.now() - timedelta(hours=hours)
        locations = WorkerLocation.objects.filter(
            worker_id=worker,
            recorded_at__gte=start_time
        ).order_by('-recorded_at')
        
        serializer = WorkerLocationSerializer(locations, many=True)
        
        return Response({
            'success': True,
            'count': locations.count(),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing workers"""
        limit = int(request. query_params.get('limit', 10))
        
        workers = Worker.objects. select_related('worker_id').filter(
            worker_id__is_active=True
        ).order_by('-avg_rating', '-total_tasks')[:limit]
        
        serializer = WorkerListSerializer(workers, many=True)
        
        return Response({
            'success': True,
            'count': workers.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get workers with low workload"""
        max_tasks = int(request.query_params.get('max_tasks', 3))
        
        from apps.reports.models import Report
        
        workers = Worker. objects.select_related('worker_id').filter(
            worker_id__is_active=True
        ).annotate(
            active_tasks=Count(
                'assigned_reports', 
                filter=Q(assigned_reports__status__in=['Assigned', 'In Progress'])
            )
        ).filter(
            active_tasks__lte=max_tasks
        ).order_by('active_tasks', '-avg_rating')
        
        serializer = WorkerListSerializer(workers, many=True)
        
        return Response({
            'success': True,
            'count': workers.count(),
            'results':  serializer.data
        })


# ==================== WORKER RANKINGS API ====================

class WorkerRankingsView(APIView):
    """
    GET /api/workers/rankings/
    Get worker rankings/leaderboard based on monthly stats
    Accessible by authenticated workers
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @staticmethod
    def _assign_badge_from_rating(avg_rating):
        """Assign badge based on average rating"""
        rating = float(avg_rating) if avg_rating else 0.0
        if rating >= 4.5:
            return 'Diamond'
        elif rating >= 4.0:
            return 'Gold'
        elif rating >= 3.5:
            return 'Silver'
        else:
            return 'Bronze'
    
    def get(self, request):
        """Get worker rankings for current month or specified month"""
        try:
            # Get month parameter (format: YYYY-MM) or use current month
            month_param = request.query_params.get('month')
            if month_param:
                try:
                    year, month = month_param.split('-')
                    target_month = datetime(int(year), int(month), 1).date()
                except (ValueError, AttributeError):
                    return Response({
                        'success': False,
                        'message': 'Invalid month format. Use YYYY-MM format.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Use current month
                target_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
            
            # Get limit (default: 50)
            limit = int(request.query_params.get('limit', 50))
            
            # Get worker monthly stats for the specified month
            monthly_stats = WorkerMonthlyStats.objects.filter(
                month=target_month
            ).select_related(
                'worker_id__worker_id'
            )
            
            # Build rankings data with points calculation and badge assignment
            # ✅ Use lifetime total_tasks instead of monthly resolved_tasks
            from apps.reports.models import Report
            rankings_data = []
            for stat in monthly_stats:
                worker = stat.worker_id
                # ✅ Calculate lifetime resolved tasks directly from database (most accurate)
                lifetime_tasks = Report.objects.filter(worker_id=worker, status='Resolved').count()
                
                # ✅ Update worker.total_tasks if it's different (keep cache in sync)
                if worker.total_tasks != lifetime_tasks:
                    worker.total_tasks = lifetime_tasks
                    worker.save(update_fields=['total_tasks'])
                
                # ✅ Calculate points: 5 points per lifetime resolved task
                calculated_points = lifetime_tasks * 5
                # Use stored points if available, otherwise use calculated
                final_points = stat.points if stat.points > 0 else calculated_points
                
                # ✅ Update points if calculated points are higher (lifetime based)
                if calculated_points > final_points:
                    final_points = calculated_points
                
                # Assign badge based on avg_rating (use lifetime avg_rating from Worker model)
                worker_avg_rating = float(worker.avg_rating) if worker.avg_rating else float(stat.avg_rating)
                assigned_badge = self._assign_badge_from_rating(worker_avg_rating)
                
                # Update badge if different (optional - can be done via management command)
                if stat.badge != assigned_badge:
                    stat.badge = assigned_badge
                    stat.save(update_fields=['badge'])
                
                # Get profile image URL
                profile_image_url = None
                if stat.worker_id.worker_id.profile_image:
                    if hasattr(stat.worker_id.worker_id.profile_image, 'url'):
                        profile_image_url = request.build_absolute_uri(stat.worker_id.worker_id.profile_image.url)
                    elif isinstance(stat.worker_id.worker_id.profile_image, str):
                        if stat.worker_id.worker_id.profile_image.startswith(('http://', 'https://')):
                            profile_image_url = stat.worker_id.worker_id.profile_image
                        else:
                            profile_image_url = request.build_absolute_uri(f'/media/{stat.worker_id.worker_id.profile_image}')
                
                rankings_data.append({
                    'worker_id': stat.worker_id.worker_id.account_id,
                    'employee_code': stat.worker_id.employee_code,
                    'name': stat.worker_id.worker_id.name,
                    'profile_image': profile_image_url,
                    'points': final_points,
                    'resolved_tasks': lifetime_tasks,  # ✅ Lifetime count
                    'avg_rating': worker_avg_rating,  # ✅ Lifetime avg_rating
                    'badge': assigned_badge,
                    'monthly_rank': stat.monthly_rank,
                    'month': stat.month.strftime('%Y-%m')
                })
            
            # Sort by points (desc), then resolved_tasks, then avg_rating
            rankings_data.sort(key=lambda x: (-x['points'], -x['resolved_tasks'], -x['avg_rating']))
            
            # Assign ranks
            current_rank = 0
            previous_points = None
            for index, entry in enumerate(rankings_data, start=1):
                # Handle ties: same rank if same points
                if previous_points is not None and entry['points'] == previous_points:
                    entry['rank'] = current_rank
                else:
                    entry['rank'] = index
                    current_rank = index
                    previous_points = entry['points']
            
            # Apply limit if specified
            if limit > 0:
                rankings_data = rankings_data[:limit]
            
            # Get current worker's info
            current_worker_info = None
            current_worker_rank = None
            try:
                user = request.user
                if hasattr(user, 'account_id'):
                    from apps.workers.models import Worker
                    try:
                        worker = Worker.objects.get(worker_id=user)
                        current_stat = WorkerMonthlyStats.objects.filter(
                            worker_id=worker,
                            month=target_month
                        ).first()
                        
                        if current_stat:
                            # ✅ Calculate lifetime resolved tasks directly from database (most accurate)
                            from apps.reports.models import Report
                            lifetime_tasks = Report.objects.filter(worker_id=worker, status='Resolved').count()
                            
                            # ✅ Update worker.total_tasks if it's different (keep cache in sync)
                            if worker.total_tasks != lifetime_tasks:
                                worker.total_tasks = lifetime_tasks
                                worker.save(update_fields=['total_tasks'])
                            
                            # ✅ Calculate points: 5 points per lifetime resolved task
                            calculated_points = lifetime_tasks * 5
                            final_points = current_stat.points if current_stat.points > 0 else calculated_points
                            
                            # ✅ Update points if calculated points are higher (lifetime based)
                            if calculated_points > final_points:
                                final_points = calculated_points
                            
                            # ✅ Use lifetime avg_rating from Worker model
                            worker_avg_rating = float(worker.avg_rating) if worker.avg_rating else float(current_stat.avg_rating)
                            assigned_badge = self._assign_badge_from_rating(worker_avg_rating)
                            
                            # Get profile image URL
                            profile_image_url = None
                            if worker.worker_id.profile_image:
                                if hasattr(worker.worker_id.profile_image, 'url'):
                                    profile_image_url = request.build_absolute_uri(worker.worker_id.profile_image.url)
                                elif isinstance(worker.worker_id.profile_image, str):
                                    if worker.worker_id.profile_image.startswith(('http://', 'https://')):
                                        profile_image_url = worker.worker_id.profile_image
                                    else:
                                        profile_image_url = request.build_absolute_uri(f'/media/{worker.worker_id.profile_image}')
                            
                            # Find rank for current worker (based on lifetime tasks and points)
                            all_stats = WorkerMonthlyStats.objects.filter(month=target_month).select_related('worker_id')
                            better_count = 0
                            for other_stat in all_stats:
                                other_worker = other_stat.worker_id
                                other_lifetime_tasks = other_worker.total_tasks
                                other_calculated_points = other_lifetime_tasks * 5
                                other_points = other_stat.points if other_stat.points > 0 else other_calculated_points
                                if other_calculated_points > other_points:
                                    other_points = other_calculated_points
                                
                                if other_points > final_points:
                                    better_count += 1
                                elif other_points == final_points:
                                    if other_lifetime_tasks > lifetime_tasks:
                                        better_count += 1
                                    elif other_lifetime_tasks == lifetime_tasks:
                                        other_avg_rating = float(other_worker.avg_rating) if other_worker.avg_rating else float(other_stat.avg_rating)
                                        if other_avg_rating > worker_avg_rating:
                                            better_count += 1
                            current_worker_rank = better_count + 1
                            
                            current_worker_info = {
                                'worker_id': worker.worker_id.account_id,
                                'employee_code': worker.employee_code,
                                'name': worker.worker_id.name,
                                'profile_image': profile_image_url,
                                'points': final_points,
                                'resolved_tasks': lifetime_tasks,  # ✅ Lifetime count
                                'avg_rating': worker_avg_rating,  # ✅ Lifetime avg_rating
                                'badge': assigned_badge,
                                'rank': current_worker_rank,
                            }
                    except Worker.DoesNotExist:
                        pass
            except Exception as e:
                logger.warning(f"Could not get current worker info: {e}")
            
            return Response({
                'success': True,
                'month': target_month.strftime('%Y-%m'),
                'count': len(rankings_data),
                'current_worker': current_worker_info,
                'current_worker_rank': current_worker_rank,
                'data': rankings_data
            })
            
        except Exception as e:
            logger.error(f"Error fetching worker rankings: {e}")
            return Response({
                'success': False,
                'message': 'Error fetching rankings',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkerStatsView(APIView):
    """
    GET /api/workers/stats/
    Get worker statistics (pending, done, average time)
    Accessible by authenticated workers
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """Get worker stats: pending, done, average resolution time"""
        try:
            user = request.user
            
            # Get worker from authenticated user
            try:
                worker = Worker.objects.get(worker_id=user)
            except Worker.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Only workers can view their stats'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Import Report model
            from apps.reports.models import Report
            from django.db.models import Avg, Count, Q
            from datetime import timedelta
            
            # Get all reports assigned to this worker
            worker_reports = Report.objects.filter(worker_id=worker)
            
            # Calculate pending reports (status = 'Pending' or 'Assigned')
            pending_count = worker_reports.filter(
                Q(status='Pending') | Q(status='Assigned')
            ).count()
            
            # Calculate done/resolved reports
            done_count = worker_reports.filter(status='Resolved').count()
            
            # Calculate average resolution time (in hours)
            # Time from accepted_at to resolved_at for resolved reports
            resolved_reports = worker_reports.filter(
                status='Resolved',
                accepted_at__isnull=False,
                resolved_at__isnull=False
            )
            
            avg_resolution_time_hours = 0.0
            if resolved_reports.exists():
                # Calculate time difference for each resolved report
                time_differences = []
                for report in resolved_reports:
                    if report.accepted_at and report.resolved_at:
                        time_diff = report.resolved_at - report.accepted_at
                        time_diff_hours = time_diff.total_seconds() / 3600.0
                        time_differences.append(time_diff_hours)
                
                if time_differences:
                    avg_resolution_time_hours = sum(time_differences) / len(time_differences)
            
            # Format average time (show hours and minutes)
            avg_hours = int(avg_resolution_time_hours)
            avg_minutes = int((avg_resolution_time_hours - avg_hours) * 60)
            
            # Total reports assigned to this worker
            total_reports = worker_reports.count()
            
            # In progress reports
            in_progress_count = worker_reports.filter(status='In Progress').count()
            
            return Response({
                'success': True,
                'data': {
                    'total_reports': total_reports,
                    'pending_reports': pending_count,
                    'done_reports': done_count,  # Resolved reports
                    'in_progress_reports': in_progress_count,
                    'avg_resolution_time_hours': round(avg_resolution_time_hours, 2),
                    'avg_resolution_time_formatted': f'{avg_hours}h {avg_minutes}m' if avg_hours > 0 or avg_minutes > 0 else '0h 0m',
                    'resolution_rate': round((done_count / total_reports * 100) if total_reports > 0 else 0, 2),
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching worker stats: {e}")
            return Response({
                'success': False,
                'message': 'Error fetching stats',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkerAnalyticsView(APIView):
    """
    GET /api/workers/analytics/
    Get comprehensive analytics data for worker (Total, Done, Rate, Time, graphs, etc.)
    Accessible by authenticated workers
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """Get worker analytics: metrics, weekly data, daily activity, waste distribution, top locations"""
        try:
            user = request.user
            
            # Get worker from authenticated user
            try:
                worker = Worker.objects.get(worker_id=user)
            except Worker.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Only workers can view their analytics'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Import Report model
            from apps.reports.models import Report
            from django.db.models import Count, Q
            from datetime import timedelta
            from collections import defaultdict
            
            # Get period parameter (week, month, year) - default to month
            period = request.query_params.get('period', 'month')
            
            # Calculate date range based on period
            now = timezone.now()
            if period == 'week':
                start_date = now - timedelta(days=7)
            elif period == 'year':
                start_date = now - timedelta(days=365)
            else:  # month (default)
                start_date = now - timedelta(days=30)
            
            # Get all reports assigned to this worker
            worker_reports = Report.objects.filter(worker_id=worker)
            
            # Filter by period
            period_reports = worker_reports.filter(submitted_at__gte=start_date)
            
            # ==================== METRICS ====================
            total_tasks = period_reports.count()
            done_tasks = period_reports.filter(status='Resolved').count()
            pending_tasks = period_reports.filter(Q(status='Pending') | Q(status='Assigned')).count()
            in_progress_tasks = period_reports.filter(status='In Progress').count()
            
            # Calculate completion rate (Done / Total * 100)
            completion_rate = round((done_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
            
            # Calculate average resolution time (in hours)
            resolved_reports = worker_reports.filter(
                status='Resolved',
                accepted_at__isnull=False,
                resolved_at__isnull=False
            )
            
            avg_resolution_time_hours = 0.0
            if resolved_reports.exists():
                time_differences = []
                for report in resolved_reports:
                    if report.accepted_at and report.resolved_at:
                        time_diff = report.resolved_at - report.accepted_at
                        time_diff_hours = time_diff.total_seconds() / 3600.0
                        time_differences.append(time_diff_hours)
                
                if time_differences:
                    avg_resolution_time_hours = sum(time_differences) / len(time_differences)
            
            # Format average time (in minutes for display)
            avg_resolution_time_minutes = int(avg_resolution_time_hours * 60)
            
            # ==================== WEEKLY DATA (Last 7 days) ====================
            weekly_data = []
            for i in range(7):
                date = (now - timedelta(days=6-i)).date()
                day_count = period_reports.filter(
                    submitted_at__date=date
                ).count()
                weekly_data.append(day_count)
            
            # ==================== DAILY ACTIVITY (Last 7 days) ====================
            daily_resolved = []
            daily_reported = []
            for i in range(7):
                date = (now - timedelta(days=6-i)).date()
                resolved_count = period_reports.filter(
                    status='Resolved',
                    resolved_at__date=date
                ).count()
                reported_count = period_reports.filter(
                    submitted_at__date=date
                ).count()
                daily_resolved.append(resolved_count)
                daily_reported.append(reported_count)
            
            # ==================== WASTE DISTRIBUTION ====================
            waste_distribution = {}
            waste_types = period_reports.values('waste_type').annotate(
                count=Count('report_id')
            )
            for item in waste_types:
                waste_type = item['waste_type'] or 'Other'
                waste_distribution[waste_type] = item['count']
            
            # Map to standard categories
            plastic_tasks = waste_distribution.get('Plastic', 0) + waste_distribution.get('Plastic Waste', 0)
            organic_tasks = waste_distribution.get('Organic', 0) + waste_distribution.get('Organic Waste', 0)
            electronic_tasks = waste_distribution.get('Electronic', 0) + waste_distribution.get('Electronic Waste', 0)
            hazardous_tasks = waste_distribution.get('Hazardous', 0) + waste_distribution.get('Hazardous Waste', 0)
            other_tasks = total_tasks - (plastic_tasks + organic_tasks + electronic_tasks + hazardous_tasks)
            
            # ==================== TOP LOCATIONS ====================
            # Get top locations by report count (group by rounded coordinates)
            top_locations_data = []
            location_groups = defaultdict(int)
            location_coords = {}  # Store coordinates for each location group
            location_samples = {}  # Store a sample report for each location (for geocoding)
            
            # Group reports by rounded coordinates (to cluster nearby reports)
            for report in period_reports:
                if report.latitude and report.longitude:
                    # Round to 3 decimal places (~100m precision) for grouping
                    lat_key = round(float(report.latitude), 3)
                    lng_key = round(float(report.longitude), 3)
                    location_key = f"{lat_key},{lng_key}"
                    location_groups[location_key] += 1
                    if location_key not in location_coords:
                        location_coords[location_key] = {
                            'latitude': float(report.latitude),
                            'longitude': float(report.longitude),
                        }
                        location_samples[location_key] = report  # Store sample for geocoding
            
            # Sort and get top 5
            sorted_locations = sorted(location_groups.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # ✅ Import geocoding function
            from apps.reports.serializers import get_location_from_coordinates
            
            for idx, (loc_key, count) in enumerate(sorted_locations, start=1):
                lat, lng = loc_key.split(',')
                coords = location_coords.get(loc_key, {})
                sample_report = location_samples.get(loc_key)
                
                # ✅ Get location name using geocoding
                location_name = f'Location {idx}'
                if sample_report and sample_report.latitude and sample_report.longitude:
                    try:
                        geocoded_name = get_location_from_coordinates(
                            float(sample_report.latitude),
                            float(sample_report.longitude)
                        )
                        if geocoded_name and geocoded_name != 'Unknown Location':
                            # Use first part of address (e.g., "D Ground" from "D Ground, Civil Lines...")
                            location_parts = geocoded_name.split(',')
                            location_name = location_parts[0].strip() if location_parts else geocoded_name
                            # Truncate if too long
                            if len(location_name) > 30:
                                location_name = location_name[:27] + '...'
                    except Exception as e:
                        logger.warning(f"Geocoding error for {loc_key}: {e}")
                        location_name = f'Location {idx}'
                
                top_locations_data.append({
                    'name': location_name,  # ✅ Use geocoded name
                    'reports': count,  # ✅ Use 'reports' instead of 'count'
                    'count': count,  # Keep for backward compatibility
                    'latitude': coords.get('latitude', float(lat)),
                    'longitude': coords.get('longitude', float(lng)),
                })
            
            # ==================== REPORTS OVER TIME (For graphs) ====================
            # Generate data for the selected period
            if period == 'week':
                labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                data_points = weekly_data
            elif period == 'year':
                # Monthly data for year
                labels = []
                data_points = []
                for i in range(12):
                    month_start = now.replace(day=1) - timedelta(days=30 * (11-i))
                    month_end = month_start + timedelta(days=30)
                    month_count = period_reports.filter(
                        submitted_at__gte=month_start,
                        submitted_at__lt=month_end
                    ).count()
                    labels.append(month_start.strftime('%b'))
                    data_points.append(month_count)
            else:  # month
                # Weekly data for month (4 weeks)
                labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
                data_points = []
                for i in range(4):
                    week_start = start_date + timedelta(days=7*i)
                    week_end = week_start + timedelta(days=7)
                    week_count = period_reports.filter(
                        submitted_at__gte=week_start,
                        submitted_at__lt=week_end
                    ).count()
                    data_points.append(week_count)
            
            # ==================== PERFORMANCE METRICS ====================
            # Calculate efficiency score (based on completion rate and average time)
            efficiency_score = int(completion_rate * 0.7 + (100 - min(avg_resolution_time_hours * 10, 100)) * 0.3)
            efficiency_score = max(0, min(100, efficiency_score))  # Clamp between 0-100
            
            # Get worker rating
            worker_rating = float(worker.avg_rating) if worker.avg_rating else 4.5
            
            # Calculate growth rate (compare with previous period)
            previous_start = start_date - (now - start_date)
            previous_period_reports = worker_reports.filter(
                submitted_at__gte=previous_start,
                submitted_at__lt=start_date
            )
            previous_done = previous_period_reports.filter(status='Resolved').count()
            
            growth_rate = 0.0
            if previous_done > 0:
                growth_rate = round(((done_tasks - previous_done) / previous_done * 100), 2)
            
            return Response({
                'success': True,
                'data': {
                    # Metrics (for 4 cards)
                    'total_reports': total_tasks,
                    'resolved_reports': done_tasks,
                    'pending_reports': pending_tasks,
                    'in_progress_reports': in_progress_tasks,
                    'completion_rate': completion_rate,  # Rate percentage
                    'avg_resolution_time_hours': round(avg_resolution_time_hours, 2),
                    'avg_resolution_time_minutes': avg_resolution_time_minutes,  # For display
                    
                    # Performance metrics
                    'performance_metrics': {
                        'efficiency_score': efficiency_score,
                        'response_time_avg': avg_resolution_time_minutes,
                        'customer_satisfaction': worker_rating,
                    },
                    
                    # Weekly data (for performance chart)
                    'weekly_data': weekly_data,
                    
                    # Daily activity (for weekly activity chart)
                    'daily_activity': {
                        'resolved': daily_resolved,
                        'reported': daily_reported,
                    },
                    
                    # Waste distribution
                    'waste_distribution': {
                        'Plastic Waste': plastic_tasks,
                        'Organic Waste': organic_tasks,
                        'Electronic Waste': electronic_tasks,
                        'Hazardous Waste': hazardous_tasks,
                        'Mixed Waste': other_tasks,
                    },
                    
                    # Task breakdown by type
                    'plastic_tasks': plastic_tasks,
                    'organic_tasks': organic_tasks,
                    'electronic_tasks': electronic_tasks,
                    'hazardous_tasks': hazardous_tasks,
                    'other_tasks': other_tasks,
                    
                    # Reports over time (for graphs)
                    'reports_over_time': {
                        'labels': labels,
                        'data': data_points,
                    },
                    
                    # Top locations
                    'top_locations': top_locations_data,
                    
                    # Additional metrics
                    'efficiency': efficiency_score,
                    'user_rating': worker_rating,
                    'growth_rate': growth_rate,
                    'resolution_rate': completion_rate,
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching worker analytics: {e}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': 'Error fetching analytics',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)