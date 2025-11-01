import os
import django
import json

# --- НАСТРОЙКА DJANGO ---
# Убедитесь, что 'gamifiededucation' - это имя папки с вашим settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamifiededucation.settings') 
django.setup()

# --- ИМПОРТ МОДЕЛЕЙ ---
from course.models import Question, Task
from django.utils.translation import gettext_lazy as _ # Импорт для _()

# --- ДАННЫЕ ВОПРОСОВ ---
# Список вопросов для Task с PK=1 ("Тапсырма 1.1: Ақпарат Көздерін Тексеру")
QUESTIONS_DATA = [
  {
    "task_pk": 1, 
    "text": _("Представьте, что вы прочитали новость: 'Ученые доказали, что шоколад улучшает память'. Какие ДВА вопроса вы бы задали, чтобы критически оценить это утверждение?"),
    "correct_answer": _("Кто проводил исследование? Каков был размер выборки?") 
  },
  {
    "task_pk": 1, 
    "text": _("Ваш друг говорит: 'Все политики лгут'. Является ли это утверждение фактом или мнением? Почему?"),
    "correct_answer": _("Мнение. Это обобщение без доказательств.") 
  },
  {
    "task_pk": 1, 
    "text": _("Реклама утверждает: 'Наш шампунь – лучший! 9 из 10 парикмахеров рекомендуют его!' Какой важной информации не хватает в этом утверждении для его проверки?"),
    "correct_answer": _("Сколько всего парикмахеров опросили?") 
  },
  {
    "task_pk": 1, 
    "text": _("Если А больше Б, а Б больше В, то что можно точно сказать об отношении А и В?"),
    "correct_answer": _("А больше В") 
  },
  {
    "task_pk": 1, 
    "text": _("Вам предлагают инвестировать деньги в проект, который обещает 100% прибыли за месяц. Какой первый шаг вы сделаете, чтобы критически оценить это предложение?"),
    "correct_answer": _("Проверить репутацию компании/человека.") 
  }
]

def add_questions():
    """Добавляет диагностические вопросы в базу данных."""
    print("Добавление диагностических вопросов...")

    question_count = 0
    for q_data in QUESTIONS_DATA:
        # Находим Задачу (Task), к которой привязать вопрос
        try:
            target_task = Task.objects.get(pk=q_data["task_pk"])
        except Task.DoesNotExist:
            print(f"ОШИБКА: Задача (Task) с PK={q_data['task_pk']} не найдена. Пропускаем вопрос.")
            continue

        # Используем get_or_create, чтобы избежать дубликатов
        question, created = Question.objects.get_or_create(
            task=target_task,
            text=str(q_data["text"]), # Преобразуем lazy proxy в строку
            defaults={'correct_answer': str(q_data["correct_answer"])}
        )
        if created:
            print(f"  -> Добавлен вопрос: {str(question.text)[:30]}...")
            question_count += 1
        else:
            print(f"  -> Вопрос '{str(question.text)[:30]}...' уже существует.")

    print(f"\n✅ Добавлено {question_count} новых вопросов.")

if __name__ == '__main__':
    # Убедитесь, что база данных существует и миграции применены
    add_questions()