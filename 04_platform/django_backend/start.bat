@echo off
echo Starting 285IQ server...
echo Open http://localhost:8000/login/ in your browser
echo Username: testuser   Password: Test285IQ!
echo Press Ctrl+C to stop
echo.
python manage.py runserver
