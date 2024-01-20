from django.contrib import admin
from apps.knowledge.models import Knowledge
# Register your models here.


class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('pageName', 'createdAt', 'lastModifiedAt', 'courseTypeId')


admin.site.register(Knowledge, KnowledgeAdmin)