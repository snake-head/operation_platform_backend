from django.contrib import admin
from apps.department.models import Department
# Register your models here.


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('deptCode', 'deptName')


admin.site.register(Department, DepartmentAdmin)