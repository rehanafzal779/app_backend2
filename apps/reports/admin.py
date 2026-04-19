from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_id', 
        'citizen_id',  # ✅ Will show the Account object (uses __str__)
        'worker_id',   # ✅ Will show the Worker object (uses __str__)
        'status', 
        'waste_type', 
        'ai_confidence',
        'submitted_at'
    ]
    list_filter = ['status', 'ai_result', 'waste_type', 'submitted_at']
    search_fields = ['report_id', 'citizen_id__name', 'citizen_id__email']
    readonly_fields = ['report_id', 'submitted_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_id', 'citizen_id', 'worker_id', 'status')
        }),
        ('AI Analysis', {
            'fields':  ('ai_result', 'waste_type', 'ai_confidence')
        }),
        ('Location', {
            'fields': ('gps_coords',)
        }),
        ('Images', {
            'fields': ('image_before', 'image_after')
        }),
        ('Timestamps', {
            'fields': ('submitted_at',)
        }),
    )