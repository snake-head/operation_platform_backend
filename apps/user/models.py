from django.db import models
from apps.privilege.models import Privilege
from apps.department.models import Department

class UserEntity(models.Model):
    class Meta:
        db_table = 'user'

    class Sex(models.TextChoices):
        MALE = '男'
        FEMAIL = '女'
        UNKNOWN = ''

    uid = models.CharField(unique=True, max_length=100, verbose_name='用户ID')
    avatar = models.CharField(null=True, blank=True, max_length=255,
                              verbose_name='头像')
    email = models.CharField(null=True, blank=True, max_length=50,
                             verbose_name='电子邮件')
    username = models.CharField(max_length=20, verbose_name='用户名')
    sex = models.CharField(choices=Sex.choices, null=True, blank=True,
                           max_length=5, verbose_name='性别')
    privilege = models.ForeignKey(Privilege, on_delete=models.SET_NULL,
                                  null=True, related_name='users',
                                  verbose_name='权限')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                   null=True, related_name='users',
                                   verbose_name='部门')
    phoneNumber = models.CharField(max_length=20, verbose_name='电话号码')
