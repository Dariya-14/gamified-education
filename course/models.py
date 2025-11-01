import re
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator 
from django.db.models import Sum, F, IntegerField, Case, When
from django.core.exceptions import ValidationError
# Убедитесь, что этот импорт есть:
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import datetime
import markdown2

# Create your models here.

def convert_hex_to_rgba(color_hex, alpha):
    rgb_text = color_hex.lstrip('#')
    rgb_values = tuple( int(rgb_text[i:i+2], 16) for i in (0, 2, 4) )
    rgba_text = 'rgba(%d, %d, %d, %f)' % (rgb_values + (alpha,))
    return rgba_text

def validate_hex_color(value):
    if not re.search(r'^#[0-9a-fA-F]{6}$', value):
        raise ValidationError(
            _('Color format must be a # followed by 6 hexadecimal digits'),
        )
    
def create_class_permissions(model):
    model_no_space = model.replace(' ', '')
    return [
        (f"add_{model_no_space}_to_my_classes", f"Can add {model} to my classes"),
        (f"change_{model_no_space}_from_my_classes", f"Can change {model} from my classes"),
        (f"view_{model_no_space}_from_my_classes", f"Can view {model} from my classes"),
        (f"delete_{model_no_space}_from_my_classes", f"Can delete {model} from my classes"),
    ] 

class ModelWithIcon(models.Model):
    icon_file_name = models.ImageField(blank=True)
    icon_external_url = models.URLField(max_length=2000, blank=True)
    
    class Meta:
        abstract = True
    
    @property
    def default_icon(self):
        return ''
    
    @property
    def icon_url(self):
        if self.icon_file_name != '':
            return settings.MEDIA_URL + str(self.icon_file_name)
        elif self.icon_external_url != '':
            return self.icon_external_url
        else:
            return self.default_icon
            

class Course(ModelWithIcon):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=100, blank=True)
    primary_hex_color = models.CharField(max_length=7, default='#0062b2', validators=[validate_hex_color])
    secondary_hex_color = models.CharField(max_length=7, default='#ff9800', validators=[validate_hex_color])

    @property
    def light_primary_color(self):
        return convert_hex_to_rgba(self.primary_hex_color, 0.2)

    @property
    def light_secondary_color(self):
        return convert_hex_to_rgba(self.secondary_hex_color, 0.1)
    
    def __str__(self):
        return self.code + ' – ' + self.name

    def default_icon(self):
        # icon from https://pixabay.com/p-2268948/?no_redirect
        return '/static/course/course-default-icon.png'
    
    class Meta:
        verbose_name = _("Курс")         
        verbose_name_plural = _("Курсы")
        ordering = ["code", "name"]


class CourseClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    ranking_size = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    total_of_lives = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        # ИСПРАВЛЕНО: Добавлен verbose_name и исправлен verbose_name_plural
        verbose_name = _("Класс Курса")      
        verbose_name_plural = _("Классы Курсов") 
        db_table = 'course_class'
        unique_together = ('code', 'course')
        ordering = ['-end_date', 'code']

    def __str__(self):
        return self.course.code + ' – ' + self.code

    def clean(self):
        super(CourseClass, self).clean()
        # Проверка дат
        if hasattr(self, 'start_date') and hasattr(self, 'end_date') and self.end_date < self.start_date:
            raise ValidationError(
                {'end_date': _('End date cannot be earlier than start date')},
                code='invalid'
            )


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, blank=True)
    id_number = models.CharField(max_length=15, blank=True)
    
    # ДОБАВЛЕНО ПОЛЕ ДЛЯ ДИАГНОСТИКИ (из предыдущих шагов)
    diagnostic_completed = models.BooleanField(default=False, verbose_name=_("Диагностика пройдена"))
    
    def __str__(self):
        # Используем имя из User, если full_name пусто
        if self.full_name:
             return self.full_name
        elif self.user:
             return self.user.get_full_name() or self.user.username
        return f"Student {self.pk}"

    def enrollments(self):
        return ", ".join(str(x.course_class) for x in self.enrollment_set.all())
    
    class Meta:
        verbose_name = _("Студент")        
        verbose_name_plural = _("Студенты")
        ordering = ["full_name", "user__username"] # Добавлена сортировка по username


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    lost_lives = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return "%s (%s)" % (self.student, self.course_class)

    @property
    def remaining_lives(self):
        remaing_lives = self.course_class.total_of_lives - self.lost_lives
        return remaing_lives if remaing_lives >= 0 else 0
    
    def clean(self):
        if self.course_class is not None and self.lost_lives > self.course_class.total_of_lives:
            raise ValidationError(
                {'lost_lives': _('Lost lives cannot be greater than the total of lives of the course class')},
                code='invalid'
            )
        super().clean()

    def total_score(self):
        # ... (ваш код расчета total_score) ...
        score = self.grade_set.filter(is_canceled=False).aggregate( # Исключаем отмененные
             score = Sum(
                 Case(
                     When(assignment_task__points=None, then=F('score')),
                     default=F('score') * F('assignment_task__points'),
                     output_field=IntegerField()
                 )
             )
         )['score'] or 0 # Возвращаем 0, если None
        return score

    class Meta:
        verbose_name = _("Запись на курс")      
        verbose_name_plural = _("Записи на курсы")
        unique_together = ('student', 'course_class')
        permissions = create_class_permissions('enrollment')
        

class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        # Используем имя из User, если full_name пусто
        if self.full_name:
             return self.full_name
        elif self.user:
             return self.user.get_full_name() or self.user.username
        return f"Instructor {self.pk}"
    
    class Meta:
        verbose_name = _("Преподаватель")      
        verbose_name_plural = _("Преподаватели")
        

class ClassInstructor(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    
    def __str__(self):
        return "%s (%s)" % (self.instructor, self.course_class)
        
    class Meta:
        # ДОБАВЛЕН ПЕРЕВОД
        verbose_name = _("Преподаватель Класса")
        verbose_name_plural = _("Преподаватели Классов")
        unique_together = ('instructor', 'course_class')


class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    def __str__(self):
        return "%s (%s)" % (self.name, self.course.code)

    class Meta:
        verbose_name = _("Задача")      
        verbose_name_plural = _("Задачи")
        unique_together = ('name', 'course')
        ordering = ["course__code", "name"]


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000, blank=True)
    is_optional = models.BooleanField(default=False)
    # ДОБАВЛЕНО ПОЛЕ ДЛЯ ДИАГНОСТИКИ (из предыдущих шагов)
    is_diagnostic = models.BooleanField(default=False, verbose_name=_("Диагностическое задание"))
    tasks = models.ManyToManyField(Task, through='AssignmentTask')

    def __str__(self):
        return "%s (%s)" % (self.name, self.course.code)
    
    class Meta:
        verbose_name = _("Задание")         
        verbose_name_plural = _("Задания")
        ordering = ["course__code", "name"]

    def points (self, course_class):
        # ... (ваш код расчета points) ...
        total = self.assignmenttask_set.filter(
            is_optional=False,
            course_class=course_class
        ).aggregate(
            total = Sum('points')
        )['total'] or 0
        return total

    def ordered_assignment_tasks(self, course_class):
        return self.assignmenttask_set.filter(course_class=course_class).order_by('is_optional', 'id').all()


class AssignmentTask(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    points = models.IntegerField(null=True, blank=True, verbose_name=_("Баллы (XP)")) # Добавлен verbose_name
    enrollments = models.ManyToManyField(Enrollment, through='Grade')
    is_optional = models.BooleanField(default=False)

    def __str__(self):
        return "%s – %s" % (self.assignment.name, self.task.name)

    class Meta:
        verbose_name = _("Задача к заданию") 
        verbose_name_plural = _("Задачи к заданиям") 
        db_table = 'course_assignment_task'
        unique_together = ('assignment', 'task', 'course_class')
        permissions = create_class_permissions('assignment task')

    def clean(self):
        super(AssignmentTask, self).clean()
        # Проверка принадлежности к одному курсу
        if hasattr(self, 'assignment') and hasattr(self, 'task') and hasattr(self, 'course_class'):
            if self.assignment.course != self.task.course or self.assignment.course != self.course_class.course:
                error_message = _('Assignment, Task and Class must be from the same course')
                raise ValidationError(
                    {'assignment': error_message, 'task': error_message, 'course_class': error_message},
                    code='invalid'
                )


class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    assignment_task = models.ForeignKey(AssignmentTask, on_delete=models.CASCADE)
    score = models.FloatField(verbose_name=_("Оценка (0-1)")) # Добавлен verbose_name
    is_canceled = models.BooleanField(default=False, verbose_name=_('Отменено'))

    class Meta:
        verbose_name = _("Оценка") # ДОБАВЛЕНО
        verbose_name_plural = _("Оценки") # ДОБАВЛЕНО
        unique_together = ('enrollment', 'assignment_task')

    @property
    def points(self):
        # ... (ваш код расчета points) ...
        if self.is_canceled: return 0
        if self.score is None: return None
        if self.assignment_task.points is None: return round(self.score)
        return round(self.score * self.assignment_task.points)
    
    def __str__(self):
        points_val = self.points
        if points_val is not None and self.assignment_task_id is not None and self.enrollment is not None:
            return f"{points_val} XP : {self.assignment_task}, by {self.enrollment.student}"
        return _("Оценка")

    def clean(self):
        super(Grade, self).clean()
        # Проверка значения score
        if self.score is not None:
             if self.assignment_task.points is None and not float(self.score).is_integer():
                 raise ValidationError({'score': _('Score must be an integer value, since the assignment task has no points')}, code='invalid')
             elif self.assignment_task.points is not None and not (0 <= self.score <= 1):
                 raise ValidationError({'score': _('Score must be a value between 0 and 1, representing the percentage of the assignment task points')}, code='invalid')
        

class Post(models.Model):
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    markdown_text = models.TextField()
    html_code = models.TextField(blank=True) # Возможно, стоит убрать, если генерируется автоматически
    post_datetime = models.DateTimeField(default=timezone.now)
    is_pinned_to_the_top = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
        
    def is_scheduled(self):
        return self.post_datetime >= timezone.now()
    
    class Meta:
        verbose_name = _("Публикация")         
        verbose_name_plural = _("Публикации")
        permissions = create_class_permissions('post')


class Widget(models.Model):
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    markdown_text = models.TextField()
    order = models.IntegerField()
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _("Виджет")         
        verbose_name_plural = _("Виджеты")
        permissions = create_class_permissions('widget')
    
    @property
    def html_code(self):
        # ... (ваш код генерации html_code) ...
        final_text = self.markdown_text
        # ... (остальной код) ...
        final_html_code = markdown2.markdown(final_text, extras=["tables", "fenced-code-blocks"])
        return final_html_code


class Badge(ModelWithIcon):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = _("Значок")        
        verbose_name_plural = _("Значки")
        unique_together = ('course', 'name')
        ordering = ["course__code", "name"]
    
    @property
    def default_icon(self):
        return '/static/course/trophy.svg'
    
    def __str__(self):
        return "%s (%s)" % (self.name, self.course.code)
        
        
class ClassBadge(models.Model):
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    description = models.CharField(max_length=2000, blank=True)
    show_progress = models.BooleanField(default=True)
    show_info_before_completion = models.BooleanField(default=True)
        
    # >>> ПЕРЕМЕСТИТЕ ЭТИ СТРОКИ СЮДА (ВНУТРЬ КЛАССА, ДО ПОЛЯ) <<<
    AND = 'AND' 
    OR = 'OR'
    AGGREGATION_TYPES = ((AND, _('AND')), (OR, _('OR')))
    
    # Теперь поле может использовать AGGREGATION_TYPES
    aggregation_type_for_criteria = models.CharField(choices=AGGREGATION_TYPES, max_length=3, default=AND) 
    
    class Meta:
        verbose_name = _("Значок Класса")     
        verbose_name_plural = _("Значки Классов")
        unique_together = ('badge', 'course_class')
        permissions = create_class_permissions('class badge')
        
    def __str__(self):
        return "%s (%s)" % (self.badge.name, self.course_class)

    def clean(self):
        super(ClassBadge, self).clean()
        if hasattr(self, 'badge') and hasattr(self, 'course_class'):
            if self.badge.course != self.course_class.course:
                 raise ValidationError({'badge': _('Badge and Class must be from the same course'), 'course_class': _('Badge and Class must be from the same course')}, code='invalid')


class ClassBadgeCriteria(models.Model):
    class_badge = models.ForeignKey(ClassBadge, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    goal = models.FloatField(validators=[MinValueValidator(0)])
    
    PERCENTAGE = 'PERCENTAGE'
    XP = 'XP'
    GOAL_TYPES = ((PERCENTAGE, _('percentage')), (XP, _('xp')))
    goal_type = models.CharField(choices=GOAL_TYPES, max_length=10, default=PERCENTAGE)

    accepts_partial_goal = models.BooleanField(default=True)

    class Meta: # ДОБАВЛЕН ПЕРЕВОД
         verbose_name = _("Критерий Значка Класса")
         verbose_name_plural = _("Критерии Значков Классов")

    def clean(self):
        super(ClassBadgeCriteria, self).clean()
        # ... (ваш код проверок) ...
        # Добавлена проверка hasattr для избежания ошибок до сохранения
        if not hasattr(self, 'class_badge'): return
        
        if self.assignment is None and self.task is None:
            raise ValidationError({'assignment': _('Assignment and Task cannot be empty at the same time'), 'task': _('Assignment and Task cannot be empty at the same time')}, code='invalid')
        elif self.assignment is not None and self.class_badge.course_class.course != self.assignment.course:
            raise ValidationError({'class_badge': _('Assignment and Class Badge must be from the same course'), 'assignment': _('Assignment and Class Badge must be from the same course')}, code='invalid')
        elif self.task is not None and self.class_badge.course_class.course != self.task.course:
            raise ValidationError({'class_badge': _('Task and Class Badge must be from the same course'), 'task': _('Task and Class Badge must be from the same course')}, code='invalid')
        elif self.assignment is not None and self.task is not None:
             if not AssignmentTask.objects.filter(assignment=self.assignment, task=self.task, course_class=self.class_badge.course_class).exists():
                 raise ValidationError({'assignment': _('There is no Assignment Task with this Assignment and this Task for this Course Class'), 'task': _('There is no Assignment Task with this Assignment and this Task for this Course Class')}, code='invalid')
    
    
class Achievement(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    class_badge = models.ForeignKey(ClassBadge, on_delete=models.CASCADE)
    percentage = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    is_canceled = models.BooleanField(default=False, verbose_name=_('Отменено'))
    
    class Meta:
        verbose_name = _("Достижение") # ДОБАВЛЕНО
        verbose_name_plural = _("Достижения") # ДОБАВЛЕНО
        unique_together = ('enrollment', 'class_badge')

    def clean(self):
        super(Achievement, self).clean()
        # Проверка принадлежности к одному классу
        if hasattr(self, 'enrollment') and hasattr(self, 'class_badge'):
            if self.enrollment.course_class != self.class_badge.course_class:
                 raise ValidationError({'enrollment': _('Enrollment and Class Badge must be from the same Course Class'), 'class_badge': _('Enrollment and Class Badge must be from the same Course Class')}, code='invalid')


class Question(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='questions', verbose_name=_("Задача"))
    text = models.TextField(verbose_name=_("Текст вопроса"))
    correct_answer = models.CharField(max_length=255, verbose_name=_("Правильный ответ")) 

    class Meta:
        verbose_name = _("Вопрос к тесту")
        verbose_name_plural = _("Вопросы к тестам")

    def __str__(self):
        return self.text[:50]