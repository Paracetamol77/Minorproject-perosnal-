from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Routine, Attendance, Note

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    routines = Routine.objects.all()
    attendances = Attendance.objects.all()
    notes = Note.objects.all()

    return render(request, 'core/dashboard.html', {
        'routines': routines,
        'attendances': attendances,
        'notes': notes,
    })


def register_view(request):
    from django.contrib.auth.models import User

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'core/register.html')

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Registration successful. Please log in.')
        return redirect('login')

    return render(request, 'core/register.html')
