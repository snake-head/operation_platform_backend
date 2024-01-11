from django.db import models

from django.db import models


# Create your models here.
class Knowledge(models.Model):
    pageName = models.CharField(max_length=100)
    pageContent = models.JSONField(default=dict)
    createdAt = models.DateTimeField(auto_now_add=True)
    lastModifiedAt = models.DateTimeField(auto_now=True)
    courseTypeId = models.IntegerField()

    class Meta:
        db_table = 'knowledge'
