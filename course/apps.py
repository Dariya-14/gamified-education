from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CourseConfig(AppConfig):

    name = 'course'
    icon = '<i class="material-icons">class</i>'
    verbose_name = _("Курсы и Задания")
