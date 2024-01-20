from django.contrib import admin
from apps.user.models import UserEntity
# Register your models here.


class VideoAdmin(admin.ModelAdmin):
    list_display = ('uid', 'username', 'email', 'sex', 'phoneNumber', 'privilege', 'department')


admin.site.register(UserEntity, VideoAdmin)