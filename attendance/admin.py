from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('mac_address', 'last_seen')
    search_fields = ('mac_address',)
