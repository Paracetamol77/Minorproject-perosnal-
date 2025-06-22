from django.shortcuts import render
from .models import Attendance

def attendance_list(request):
    records = Attendance.objects.all()
    return render(request, 'attendance/attendance_list.html', {'records': records})
