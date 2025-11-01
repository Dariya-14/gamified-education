import os
import django
from django.contrib.auth import get_user_model

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamifiededucation.settings')
django.setup()

User = get_user_model()

# Пароль для всех пользователей
DEFAULT_PASSWORD = 'password123' 

def create_users():
    """Создает 6 админов/преподавателей и 20 студентов."""
    
    # ----------------------------------------------------
    # 1. Администраторы/Преподаватели (PK 1-6)
    # ----------------------------------------------------
    print("Создание 6 административных/преподавательских учетных записей (PK 1-6)...")
    for i in range(1, 7):
        username = f'admin_or_teacher{i}'
        email = f'{username}@edu.kz'
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=DEFAULT_PASSWORD
            )
            print(f"  -> Создан Superuser: {username} (PK: {user.pk})")
        else:
            print(f"  -> Пользователь {username} уже существует.")

    # ----------------------------------------------------
    # 2. Студенты (PK 7-26)
    # ----------------------------------------------------
    print("\nСоздание 20 студенческих учетных записей (PK 7-26)...")
    for i in range(1, 21):
        username = f'student{i}'
        email = f'{username}@edu.kz'
        
        if not User.objects.filter(username=username).exists():
            # Создаем обычного пользователя
            user = User.objects.create_user(
                username=username,
                email=email,
                password=DEFAULT_PASSWORD
            )
            print(f"  -> Создан User: {username} (PK: {user.pk})")
        else:
            print(f"  -> Пользователь {username} уже существует.")

    print("\n✅ Создание пользователей завершено. Всего должно быть 26 пользователей.")

if __name__ == '__main__':
    # ВНИМАНИЕ: Перед запуском удалите db.sqlite3 и запустите python manage.py migrate
    create_users()