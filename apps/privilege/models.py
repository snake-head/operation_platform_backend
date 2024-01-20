from django.db import models


# Create your models here.
class Privilege(models.Model):
    privilegeCode = models.CharField(
        unique=True,
        null=False,
        blank=False,
        max_length=20,
        verbose_name="权限代码"  # 添加中文 verbose_name
    )

    privilegeName = models.CharField(
        unique=True,
        null=False,
        blank=False,
        max_length=30,
        verbose_name="权限名称"  # 添加中文 verbose_name
    )

    class Meta:
        db_table = 'privilege'
