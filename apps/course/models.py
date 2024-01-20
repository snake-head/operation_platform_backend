from django.db import models
from apps.department.models import Department


class CourseType(models.Model):
    name = models.CharField(unique=True, max_length=50, verbose_name='名称')
    label = models.CharField(unique=True, max_length=50, verbose_name='标签')

    class Meta:
        db_table = 'course_type'


# Create your models here.
class Course(models.Model):
    courseId = models.CharField(unique=True, max_length=50,
                                verbose_name='课程ID')
    courseName = models.CharField(unique=True, max_length=50,
                                  verbose_name='课程名称')
    courseDescription = models.CharField(null=True, blank=True, max_length=500,
                                         verbose_name='课程描述')
    courseCoverUrl = models.CharField(null=True, blank=True, max_length=255,
                                      verbose_name='课程封面URL')
    courseType = models.ForeignKey(CourseType, on_delete=models.SET_NULL,
                                   related_name='courses', null=True,
                                   verbose_name='课程类型')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                   related_name='courses', null=True,
                                   verbose_name='所属部门')

    class Meta:
        db_table = 'course'



