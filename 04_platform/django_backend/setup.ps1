# 285IQ Local Setup Script for Windows
# Run this ONCE from the django_backend folder:
#   Right-click -> "Run with PowerShell"
# OR in PowerShell terminal: .\setup.ps1

Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 285IQ - First Time Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Set env vars for this session
$env:USE_SQLITE = "True"
$env:SECRET_KEY = "local-dev-secret-key-285iq"
$env:DEBUG = "True"

Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

Write-Host "`nRunning database migrations..." -ForegroundColor Yellow
python manage.py migrate --run-syncdb

Write-Host "`nSeeding subjects and questions..." -ForegroundColor Yellow
python manage.py seed_exam_boards
python manage.py bootstrap_gcse
python manage.py seed_computer_science
python manage.py seed_extended_questions
python manage.py seed_flashcards
python manage.py seed_mock_exams

Write-Host "`nCreating test account (testuser / Test285IQ!)..." -ForegroundColor Yellow
python manage.py shell -c @"
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
User = get_user_model()
u, created = User.objects.get_or_create(username='testuser', defaults={'email':'test@285iq.com','display_name':'Test Student'})
u.set_password('Test285IQ!')
u.subscription_status = 'pro_monthly'
u.subscription_expires_at = timezone.now() + timedelta(days=365)
u.save()
print('Test account ready!')
"@

Write-Host "`n========================================" -ForegroundColor Green
Write-Host " Setup complete!" -ForegroundColor Green
Write-Host " Run: python manage.py runserver" -ForegroundColor Green
Write-Host " Then open: http://localhost:8000/login/" -ForegroundColor Green
Write-Host " Username: testuser   Password: Test285IQ!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nStarting server now..." -ForegroundColor Cyan
python manage.py runserver
