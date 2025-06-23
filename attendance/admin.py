from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['mac_address', 'device_name', 'is_active', 'last_seen', 'first_seen']
    list_filter = ['is_active', 'last_seen', 'first_seen']
    search_fields = ['mac_address', 'device_name']
    readonly_fields = ['first_seen']
    ordering = ['-last_seen']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-last_seen')
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} devices marked as active.')
    mark_as_active.short_description = 'Mark selected devices as active'
    
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} devices marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected devices as inactive'