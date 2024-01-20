from django.contrib import admin
from apps.video.models import Video
# Register your models here.


class VideoAdmin(admin.ModelAdmin):
    list_display = ('videoName', 'videoUrl', 'createdAt', 'lastModifiedAt', 'status')


admin.site.register(Video, VideoAdmin)