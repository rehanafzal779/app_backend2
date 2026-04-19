from django.db import models
from django.utils import timezone
from apps.accounts.models import Account
from apps.workers.models import Worker


class Report(models.Model):
    """
    Report model with file upload support
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    )
    
    AI_RESULT_CHOICES = (
        ('Unverified', 'Unverified'),
        ('Waste', 'Waste'),
        ('No Waste', 'No Waste'),
    )
    
    report_id = models.AutoField(primary_key=True)
    
    citizen_id = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='submitted_reports',
        db_column='citizen_id'
    )
    worker_id = models. ForeignKey(
        Worker,
        on_delete=models. SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_reports',
        db_column='worker_id'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_index=True)
    ai_result = models.CharField(max_length=20, choices=AI_RESULT_CHOICES, default='Unverified')
    waste_type = models.CharField(max_length=50, null=True, blank=True)
    ai_confidence = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, db_column='latitude')
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, db_column='longitude')
    
    # ✅ CHANGED: Use ImageField for file uploads
    image_before = models.ImageField(upload_to='reports/before/', max_length=512)
    image_after = models. ImageField(upload_to='reports/after/', max_length=512, null=True, blank=True)
    
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True, db_index=True)  # ✅ When worker accepts the report
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)  # ✅ When worker starts the task (status changes to In Progress)
    resolved_at = models.DateTimeField(null=True, blank=True, db_index=True)  # ✅ When report is resolved
    
    class Meta:
        db_table = 'reports'
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['citizen_id', '-submitted_at']),
            models.Index(fields=['worker_id', '-submitted_at']),
        ]
    
    def __str__(self):
        return f"Report #{self.report_id} - {self.status}"
    
    @property
    def citizen_name(self):
        return self.citizen_id.name if self.citizen_id else 'Unknown'
    
    @property
    def worker_name(self):
        return self.worker_id.worker_id. name if self.worker_id else None
    
    @property
    def location(self):
        if self.latitude and self.longitude:
            return f"{float(self.latitude):.6f}, {float(self.longitude):.6f}"
        return 'Unknown Location'
    
    @property
    def assigned_at(self):
        return None
    