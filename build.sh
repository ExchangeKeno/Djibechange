#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Créer le superuser automatiquement si il n'existe pas
python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
username = "admin"
password = "Djib@2024!"
email = "keno01071@gmail.com"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' créé avec succès.")
else:
    print(f"Superuser '{username}' existe déjà.")
PYEOF
