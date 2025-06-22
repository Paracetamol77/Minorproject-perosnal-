from django.contrib import admin
from django.urls import path
from attendance.views import attendance_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', attendance_list, name='attendance_list'),
]
