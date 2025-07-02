from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),  # ✅ Root URL (http://127.0.0.1:8000/) redirects to login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
