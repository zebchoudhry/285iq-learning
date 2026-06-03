@echo off
echo ========================================
echo  285IQ - First Time Setup
echo ========================================

echo Installing dependencies...
py -m pip install -r requirements.txt

echo Running migrations...
py manage.py migrate --run-syncdb

echo Seeding subjects and questions...
py manage.py seed_exam_boards
py manage.py bootstrap_gcse
py manage.py seed_computer_science
py manage.py seed_extended_questions
py manage.py seed_flashcards
py manage.py seed_mock_exams

echo Creating test account...
py manage.py shell -c "from django.contrib.auth import get_user_model; from django.utils import timezone; from datetime import timedelta; User = get_user_model(); u, _ = User.objects.get_or_create(username='testuser', defaults={'email':'test@285iq.com','display_name':'Test Student'}); u.set_password('Test285IQ!'); u.subscription_status='pro_monthly'; u.subscription_expires_at=timezone.now()+timedelta(days=365); u.save(); print('Test account ready: testuser / Test285IQ!')"

echo ========================================
echo  Setup complete! Run start.bat to launch
echo ========================================
pause
