from django.db import models


# Create your models here.
class Department(models.Model):
    deptCode = models.CharField(unique=True, max_length=50,
                                verbose_name='部门代码')
    deptName = models.CharField(unique=True, max_length=50,
                                verbose_name='部门名称')

    class Meta:
        db_table = 'department'
