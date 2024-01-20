from django.contrib import admin
from apps.course.models import Course, CourseType
# Register your models here.


class CourseAdmin(admin.ModelAdmin):
    list_display = ('courseId', 'courseName', 'courseDescription', 'courseType', 'department')


class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'label')


admin.site.register(Course, CourseAdmin)
admin.site.register(CourseType, CourseTypeAdmin)