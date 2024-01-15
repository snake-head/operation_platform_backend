from django.contrib import admin
from apps.course.models import Course, CourseType
# Register your models here.

admin.site.register(Course)
admin.site.register(CourseType)