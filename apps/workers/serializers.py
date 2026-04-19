from rest_framework import serializers
from django. db.models import Avg
from django.utils import timezone
from datetime import timedelta

from .models import Worker, WorkerLocation, WorkerMonthlyStats
from apps. accounts.models import Account
from apps.reports.models import Report
from apps.feedback.models import Feedback


# =========================
# WORKER LIST SERIALIZER
# =========================

class WorkerListSerializer(serializers.ModelSerializer):
    """Serializer for worker list view"""

    account_id = serializers.IntegerField(source='worker_id.account_id', read_only=True)
    name = serializers.CharField(source='worker_id.name', read_only=True)
    email = serializers.EmailField(source='worker_id.email', read_only=True)
    phone_number = serializers.CharField(source='worker_id.phone_number', read_only=True)
    
    # ✅ FIXED: Use SerializerMethodField to handle both string and ImageField
    profile_image = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='worker_id.is_active', read_only=True)

    class Meta:
        model = Worker
        fields = [
            'worker_id',
            'employee_code',
            'total_tasks',
            'avg_rating',
            'is_tracking',
            'created_at',
            'updated_at',
            'account_id',
            'name',
            'email',
            'phone_number',
            'profile_image',
            'is_active'
        ]
    
    def get_profile_image(self, obj):
        """✅ FIXED: Handle both CharField (string) and ImageField"""
        request = self.context.get('request')
        profile_image = obj.worker_id.profile_image
        
        if not profile_image:
            return None
        
        # ✅ Check if it's an ImageField (has . url attribute)
        if hasattr(profile_image, 'url'):
            if request:
                return request.build_absolute_uri(profile_image.url)
            return profile_image.url
        
        # ✅ If it's a string (CharField), return as-is or build URL
        if isinstance(profile_image, str):
            # If it's already a full URL
            if profile_image.startswith(('http://', 'https://')):
                return profile_image
            # If it's a relative path, build absolute URL
            if request:
                return request.build_absolute_uri(f'/media/{profile_image}')
            return f'/media/{profile_image}'
        
        return None


# =========================
# WORKER DETAIL SERIALIZER
# =========================

class WorkerDetailSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()
    current_assignments = serializers.SerializerMethodField()
    monthly_performance = serializers.SerializerMethodField()
    lifetime_avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = '__all__'

    def get_account(self, obj):
        """✅ FIXED: Handle both CharField and ImageField"""
        request = self.context.get('request')
        profile_image = obj.worker_id.profile_image
        profile_image_url = None
        
        if profile_image:
            # ✅ Check if it's an ImageField
            if hasattr(profile_image, 'url'):
                if request:
                    profile_image_url = request. build_absolute_uri(profile_image.url)
                else:
                    profile_image_url = profile_image.url
            # ✅ If it's a string
            elif isinstance(profile_image, str):
                if profile_image.startswith(('http://', 'https://')):
                    profile_image_url = profile_image
                else:
                    if request:
                        profile_image_url = request.build_absolute_uri(f'/media/{profile_image}')
                    else:
                        profile_image_url = f'/media/{profile_image}'
        
        return {
            'account_id': obj.worker_id. account_id,
            'name': obj.worker_id.name,
            'email': obj. worker_id.email,
            'phone_number': obj.worker_id.phone_number,
            'profile_image': profile_image_url,
            'is_active': obj.worker_id.is_active,
            'created_at': obj.worker_id.created_at,
        }

    def get_current_assignments(self, obj):
        return Report.objects.filter(
            worker_id=obj,
            status__in=['Assigned', 'In Progress']
        ).count()

    def get_monthly_performance(self, obj):
        thirty_days_ago = timezone.now() - timedelta(days=30)

        reports = Report.objects.filter(
            worker_id=obj,
            submitted_at__gte=thirty_days_ago,
            status='Resolved'
        )

        avg_rating = Feedback.objects.filter(
            worker_id=obj,
            report_id__in=reports
        ).aggregate(avg=Avg('rating'))['avg'] or 0

        return {
            'resolved_count': reports.count(),
            'avg_rating': float(avg_rating),
        }

    def get_lifetime_avg_rating(self, obj):
        avg_rating = Feedback.objects. filter(
            worker_id=obj
        ).aggregate(avg=Avg('rating'))['avg'] or 0

        return float(avg_rating)


# =========================
# WORKER CREATE SERIALIZER
# =========================

class WorkerCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    employee_code = serializers.CharField(max_length=50)
    
    # ✅ ADD IMAGE FIELD FOR CREATION
    profile_image = serializers.ImageField(required=False, allow_null=True)

    def validate_email(self, value):
        value = value.lower().strip()
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_employee_code(self, value):
        value = value.strip()
        if Worker.objects.filter(employee_code=value).exists():
            raise serializers.ValidationError("A worker with this employee code already exists.")
        return value

    def create(self, validated_data):
        from django.db import transaction

        password = validated_data.pop('password')
        profile_image = validated_data.pop('profile_image', None)

        with transaction.atomic():
            account = Account.objects.create_user(
                email=validated_data['email'],
                password=password,
                name=validated_data['name'],
                phone_number=validated_data.get('phone', ''),
                role='worker',
                is_active=True
            )
            
            # ✅ SAVE PROFILE IMAGE
            if profile_image:
                account.profile_image = profile_image
                account.save()

            worker = Worker.objects.create(
                worker_id=account,
                employee_code=validated_data['employee_code']
            )

            return worker


# =========================
# WORKER UPDATE SERIALIZER
# =========================

class WorkerUpdateSerializer(serializers. Serializer):
    name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    employee_code = serializers.CharField(max_length=50, required=False)
    
    # ✅ ADD IMAGE FIELD FOR UPDATE
    profile_image = serializers.ImageField(required=False, allow_null=True)

    def validate_employee_code(self, value):
        worker = self.instance
        if Worker.objects.filter(employee_code=value).exclude(worker_id=worker.worker_id).exists():
            raise serializers.ValidationError("A worker with this employee code already exists.")
        return value. strip()

    def update(self, instance, validated_data):
        from django.db import transaction
        from apps.tracking.models import ActivityLog

        request = self.context.get('request')
        admin_id = getattr(getattr(request, 'user', None), 'id', 0)

        with transaction.atomic():
            # ✅ UPDATE ACCOUNT FIELDS
            if 'name' in validated_data:
                instance.worker_id.name = validated_data['name']
            if 'phone' in validated_data:
                instance.worker_id.phone_number = validated_data['phone']
            
            # ✅ UPDATE PROFILE IMAGE
            if 'profile_image' in validated_data:
                profile_image = validated_data['profile_image']
                if profile_image:
                    # ✅ Check if old field is ImageField and delete
                    if hasattr(instance. worker_id.profile_image, 'delete'):
                        try:
                            instance.worker_id.profile_image.delete(save=False)
                        except Exception:
                            pass
                    instance.worker_id.profile_image = profile_image
                elif profile_image is None:
                    # Explicitly remove image
                    if hasattr(instance.worker_id.profile_image, 'delete'):
                        try:
                            instance.worker_id.profile_image.delete(save=False)
                        except Exception: 
                            pass
                    instance.worker_id.profile_image = None
            
            instance.worker_id. save()

            # ✅ UPDATE WORKER FIELDS
            if 'employee_code' in validated_data:
                instance.employee_code = validated_data['employee_code']
            instance.save()

            # ✅ LOG ACTIVITY
            try:
                ActivityLog.objects.create(
                    activity_type='worker_updated',
                    description=f'Worker {instance.employee_code} updated',
                    actor_id=admin_id,
                    target_type='worker',
                    target_id=instance.worker_id. account_id
                )
            except Exception:
                pass

            return instance


# =========================
# WORKER LOCATION SERIALIZER
# =========================

class WorkerLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerLocation
        fields = '__all__'


# =========================
# WORKER MONTHLY STATS
# =========================

class WorkerMonthlyStatsSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source='worker_id.worker_id.name', read_only=True)
    employee_code = serializers.CharField(source='worker_id.employee_code', read_only=True)

    class Meta:
        model = WorkerMonthlyStats
        fields = '__all__'