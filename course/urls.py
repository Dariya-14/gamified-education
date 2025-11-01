from django.urls import re_path, include
from django.contrib.auth import views as auth_views

from . import views

app_name = 'course'
urlpatterns = [
    # --- СУЩЕСТВУЮЩИЕ МАРШРУТЫ ---
    re_path(r'^classes/?$', views.classes, name='classes'),
    
    # (Мы удалим дублирующийся re_path(r'^$', views.index, name='index') отсюда, так как он есть в конце)
    
    # re_path(r'^([^/]+)/([^/]+)/?$', views.home, name='home'),
    # ^^^^ Этот маршрут (home) ПЕРЕКРЫВАЕТ ваши новые маршруты. 
    # Давайте сделаем маршруты более конкретными и поместим 'home' ПОСЛЕ них.

    re_path(r'^(?P<course_code>[^/]+)/(?P<class_code>[^/]+)/assignments/?(?P<student_id>[\d]+)?/?$', views.assignments, name='assignments'),
    
    # --- НОВЫЕ МАРШРУТЫ ДЛЯ ДИАГНОСТИКИ (ИСПРАВЛЕННЫЕ С ИМЕНАМИ) ---
    
    # 1. URL для отображения диагностического теста
    re_path(
        r'^(?P<course_code>[^/]+)/(?P<class_code>[^/]+)/diagnostic/(?P<assignment_task_id>[\d]+)/?$', 
        views.show_diagnostic_test, 
        name='show_diagnostic_test'
    ),

    # 2. URL для обработки (отправки) теста
    re_path(
        r'^(?P<course_code>[^/]+)/(?P<class_code>[^/]+)/diagnostic/(?P<assignment_task_id>[\d]+)/submit/?$', 
        views.submit_diagnostic_test, 
        name='submit_diagnostic_test'
    ),
    
    # --- СУЩЕСТВУЮЩИЙ МАРШРУТ 'HOME' (ТЕПЕРЬ В КОНЦЕ) ---
    re_path(r'^(?P<course_code>[^/]+)/(?P<class_code>[^/]+)/?$', views.home, name='home'),
    
    # --- Маршрут по умолчанию (Главная/Вход) ---
    re_path(r'^$', views.index, name='index'), 
]