from django.db import models

class Picture(models.Model):
    picturename = models.CharField(max_length=255, verbose_name='图片名称')
    picturelabel = models.CharField(max_length=255, verbose_name='图片标签')
    pictureurl = models.URLField(max_length=255, verbose_name='图片URL')  

    def __str__(self):
        return self.picturename