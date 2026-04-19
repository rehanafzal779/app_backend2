from rest_framework import serializers
from .models import Account, UserSession, LoginHistory
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class AccountSerializer(serializers. ModelSerializer):
    """Basic Account serializer"""
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'account_id', 'email', 'name', 'role',
            'phone_number', 'profile_image', 'profile_image_url',
            'created_at', 'last_login', 'is_active'
        ]
        read_only_fields = ['account_id', 'created_at', 'last_login']
    
    def get_profile_image_url(self, obj):
        return obj.get_profile_image_url()


class AccountDetailSerializer(serializers.ModelSerializer):
    """Detailed Account serializer with session info"""
    profile_image_url = serializers. SerializerMethodField()
    active_sessions_count = serializers.SerializerMethodField()
    total_login_count = serializers.IntegerField(source='login_count', read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'account_id', 'email', 'name', 'role',
            'phone_number', 'profile_image', 'profile_image_url',
            'google_id', 'created_at', 'last_login', 'last_activity',
            'is_active', 'active_sessions_count', 'total_login_count'
        ]
        read_only_fields = [
            'account_id', 'created_at', 'last_login', 
            'last_activity', 'total_login_count'
        ]
    
    def get_profile_image_url(self, obj):
        return obj.get_profile_image_url()
    
    def get_active_sessions_count(self, obj):
        return obj.sessions.filter(is_active=True).count()


class AccountRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Account
        fields = [
            'email',
            'name',
            'password',
            'password_confirm',
            'role',
            'phone_number',
            'profile_image',
        ]

    def validate_email(self, value):
        value = value.lower()
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Account with this email already exists."
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({
                "password": list(e.messages)
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Force lowercase email
        validated_data['email'] = validated_data['email'].lower()

        account = Account(**validated_data)
        account.set_password(password)
        account.save()

        return account


class AccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating account"""
    
    class Meta:
        model = Account
        fields = ['name', 'phone_number', 'profile_image']


class AccountLoginSerializer(serializers. Serializer):
    """Serializer for account login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    device_type = serializers.ChoiceField(
        choices=['mobile', 'tablet', 'desktop', 'unknown'],
        default='unknown',
        required=False
    )
    device_name = serializers.CharField(required=False, allow_blank=True)


class PasswordChangeSerializer(serializers. Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers. CharField(
        required=True,
        style={'input_type':  'password'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth"""
    google_token = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=['Citizen', 'Worker'], default='Citizen')
    device_type = serializers.ChoiceField(
        choices=['mobile', 'tablet', 'desktop', 'unknown'],
        default='unknown',
        required=False
    )
    device_name = serializers.CharField(required=False, allow_blank=True)


# ✅ NEW: Session Serializers
class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    is_current = serializers.SerializerMethodField()
    is_expired_flag = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'session_id', 'device_type', 'device_name',
            'ip_address', 'location', 'created_at',
            'last_activity', 'expires_at', 'is_active',
            'is_current', 'is_expired_flag'
        ]
        read_only_fields = ['session_id', 'created_at']
    
    def get_is_current(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'session_obj'):
            return obj.session_id == request.session_obj.session_id
        return False
    
    def get_is_expired_flag(self, obj):
        return obj.is_expired()


class LoginHistorySerializer(serializers. ModelSerializer):
    """Serializer for login history"""
    
    class Meta:
        model = LoginHistory
        fields = [
            'history_id', 'status', 'ip_address',
            'user_agent', 'device_type', 'location',
            'failure_reason', 'attempted_at'
        ]
        read_only_fields = ['history_id', 'attempted_at']