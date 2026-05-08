import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

try:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"Senha do usuário '{username}' redefinida com sucesso.")
except User.DoesNotExist:
    User.objects.create_superuser(
        username=username,
        password=password,
        email=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
    )
    print(f"Usuário '{username}' criado com sucesso.")