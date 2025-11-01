import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamifiededucation.settings')
django.setup()

from course.models import Course, Assignment, Task, AssignmentTask, CourseClass

with open('tests.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for c in data:
    course, _ = Course.objects.get_or_create(
        code=c["code"],
        defaults={"name": c["course"], "description": c["description"]}
    )

    for a in c["assignments"]:
        assignment, _ = Assignment.objects.get_or_create(course=course, name=a["name"])

        for t in a["tasks"]:
            task, _ = Task.objects.get_or_create(
                course=course,
                name=t["name"],
                defaults={"description": t["description"]}
            )

            course_class = CourseClass.objects.filter(course=course).first()
            if course_class:
                AssignmentTask.objects.get_or_create(
                    assignment=assignment,
                    task=task,
                    course_class=course_class
                )
print("✅ Данные успешно импортированы!")
