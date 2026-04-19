from rest_framework import serializers
from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source='citizen.name', read_only=True)
    worker_name = serializers.CharField(source='worker.worker_id. name', read_only=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['feedback_id', 'created_at']


class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['report', 'citizen', 'worker', 'rating', 'comment']
    
    def create(self, validated_data):
        feedback = super().create(validated_data)
        # Trigger worker rating update
        feedback.worker.update_rating()
        return feedback