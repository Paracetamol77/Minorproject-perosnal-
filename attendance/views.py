from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Attendance

def attendance_list(request):
    # ✅ Show only devices seen in last 5 minutes
    cutoff_time = timezone.now() - timedelta(minutes=1)
    records = Attendance.objects.filter(last_seen__gte=cutoff_time).order_by('-last_seen')
    return render(request, 'attendance/attendance_list.html', {'records': records})
