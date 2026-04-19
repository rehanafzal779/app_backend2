from rest_framework import serializers
import json
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer with enhanced fields for permanent storage:
    - Uses database fields (title, status, expires_at, etc.) when available
    - Falls back to message JSON for backward compatibility
    """
    title = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    formatted_message = serializers.SerializerMethodField()  # ✅ Readable message for admin panel
    
    class Meta: 
        model = Notification
        fields = [
            'notification_id',
            'recipient_type',
            'recipient_id',
            'message',
            'title',
            'type',
            'data',
            'formatted_message',  # ✅ Readable message format
            'is_read',
            'created_at',
            # ✅ New fields
            'status',
            'expires_at',
            'task_number',
            'accepted_at',
            'report_id',
        ]
        read_only_fields = ['notification_id', 'created_at']
    
    def get_title(self, obj):
        """Get title from database field, fallback to message JSON"""
        # ✅ Priority: database field > message JSON
        if obj.title:
            return obj.title
        try:
            if obj.message:
                message_data = json.loads(obj.message)
                return message_data.get('title') or message_data.get('message', 'Notification')
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        return 'Notification'
    
    def get_type(self, obj):
        """Extract type from message JSON"""
        try:
            if obj.message:
                message_data = json.loads(obj.message)
                notification_type = message_data.get('type', 'general')
                # Map backend types to frontend types
                type_map = {
                    'report_available': 'task_assignment',  # Worker - citizen submitted report
                    'task_assignment': 'task_assignment',  # Worker - admin assigned task
                    'report_assigned': 'report_assigned',  # Citizen
                    'report_declined': 'report_rejected',  # Citizen
                    'report_resolved': 'report_resolved',  # Citizen
                    'report_in_progress': 'report_in_progress',  # Citizen
                    'feedback': 'feedback_received',  # Worker - feedback received
                }
                return type_map.get(notification_type, notification_type)
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        return 'general'
    
    def get_data(self, obj):
        """Parse message JSON as data, merge with database fields"""
        data = {}
        try:
            if obj.message:
                data = json.loads(obj.message)
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        
        # ✅ Merge database fields into data for frontend
        if obj.report_id:
            data['report_id'] = obj.report_id
        if obj.expires_at:
            data['expires_at'] = obj.expires_at.isoformat()
        if obj.status:
            data['status'] = obj.status
        if obj.task_number:
            data['task_number'] = obj.task_number
        if obj.accepted_at:
            data['accepted_at'] = obj.accepted_at.isoformat()
        
        # ✅ Include reported_by from message JSON if available (for admin vs citizen distinction)
        if 'reported_by' in data:
            pass  # Already in data from message JSON
        elif obj.report_id:
            # ✅ Try to get reported_by from report if not in message
            try:
                from apps.reports.models import Report
                report = Report.objects.filter(report_id=obj.report_id).first()
                if report:
                    # Check if admin-assigned (accepted_at is None and status is 'Assigned')
                    if report.accepted_at is None and report.status == 'Assigned' and report.worker_id is not None:
                        data['reported_by'] = 'Assigned by Admin'
                    elif report.citizen_id:
                        data['reported_by'] = f'Reported by {report.citizen_id.name}'
            except Exception:
                pass  # Ignore if report not found
        
        return data
    
    def get_formatted_message(self, obj):
        """Format message for admin panel - readable format instead of JSON"""
        try:
            if obj.message:
                message_data = json.loads(obj.message)
                
                # ✅ Build readable message from JSON data
                parts = []
                
                # Message
                if message_data.get('message'):
                    parts.append(f"Message: {message_data['message']}")
                
                # Reported by / Assigned by
                reported_by = message_data.get('reported_by') or self.get_data(obj).get('reported_by')
                if reported_by:
                    parts.append(f"Reported by: {reported_by}")
                
                # Admin name
                if message_data.get('admin_name'):
                    parts.append(f"Admin: {message_data['admin_name']}")
                
                # Waste type
                if message_data.get('waste_type'):
                    parts.append(f"Waste Type: {message_data['waste_type']}")
                
                # Location
                if message_data.get('location'):
                    parts.append(f"Location: {message_data['location']}")
                
                # Report ID
                if message_data.get('report_id'):
                    parts.append(f"Report ID: {message_data['report_id']}")
                
                # Type
                if message_data.get('type'):
                    parts.append(f"Type: {message_data['type']}")
                
                return " | ".join(parts) if parts else obj.message
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        
        # ✅ If not JSON, return as is
        return obj.message if obj.message else 'No message'


class SendNotificationSerializer(serializers.Serializer):
    """For POST /api/workers/{id}/notify/"""
    title = serializers.CharField(max_length=255, required=False, default='Notification')
    body = serializers.CharField(required=True)

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message body cannot be empty")
        return value.strip()