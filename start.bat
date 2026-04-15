@echo off
echo Starting DJIB Exchange...
set DJANGO_SETTINGS_MODULE=djib_exchange.settings
cd /d "%~dp0"
python manage.py runserver 8000
pause
