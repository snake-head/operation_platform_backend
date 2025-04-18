from django.db import models
from django.db.models import Count, Sum, Case, When, IntegerField, F
from django.db.models.functions import Cast

class RecaptchaRecord(models.Model):
    """记录用户验证码回答数据"""
    
    # 用户标识
    openid = models.CharField(max_length=128, db_index=True, verbose_name='用户OpenID')
    
    # 虚假图片的名称
    imgname = models.CharField(max_length=255, verbose_name='验证码图片名称')
    
    # 验证结果
    iscorrect = models.BooleanField(default=False, verbose_name='是否回答正确')
    
    # 前端返回的选择理由
    reason = models.TextField(null=True, blank=True, verbose_name='用户选择原因')
    
    # 自动记录创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')
    
    class Meta:
        verbose_name = '验证码记录'
        verbose_name_plural = '验证码记录'
        ordering = ['-created_at']  # 默认按时间倒序排列
    
    def __str__(self):
        return f"{self.openid} - {'正确' if self.iscorrect else '错误'} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

class RecaptchaStats(models.Model):
    """验证码图片统计数据"""
    
    # 图片名称 (唯一)
    imgname = models.CharField(max_length=255, unique=True, db_index=True, 
                             verbose_name='验证码图片名称')
    
    # 统计数据
    total_judgments = models.IntegerField(default=0, verbose_name='总判断次数')
    correct_judgments = models.IntegerField(default=0, verbose_name='正确判断次数')
    
    # 各个理由的选择次数
    reason1_count = models.IntegerField(default=0, verbose_name='理由1选择次数')
    reason2_count = models.IntegerField(default=0, verbose_name='理由2选择次数')
    reason3_count = models.IntegerField(default=0, verbose_name='理由3选择次数')
    reason4_count = models.IntegerField(default=0, verbose_name='理由4选择次数')
    
    # 最后更新时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')
    
    class Meta:
        verbose_name = '验证码统计'
        verbose_name_plural = '验证码统计'
        ordering = ['-total_judgments']  # 默认按总判断次数排序
    
    def __str__(self):
        success_rate = (self.correct_judgments / self.total_judgments * 100) if self.total_judgments > 0 else 0
        return f"{self.imgname} - 判断{self.total_judgments}次, 正确率{success_rate:.1f}%"
    
    @property
    def success_rate(self):
        """计算成功率"""
        if self.total_judgments > 0:
            return (self.correct_judgments / self.total_judgments) * 100
        return 0
    
    @classmethod
    def update_stats(cls):
        """从RecaptchaRecord表更新所有统计数据"""
        
        # 1. 获取所有图片名称
        unique_images = RecaptchaRecord.objects.values_list('imgname', flat=True).distinct()
        updated_count = 0
        
        # 2. 对每个图片单独处理
        for imgname in unique_images:
            cls.update_single_stat(imgname)
            updated_count += 1
            
        return updated_count

    @classmethod
    def update_single_stat(cls, imgname):
        """更新单个图片的统计数据"""
        # 获取所有与该图片相关的记录
        records = RecaptchaRecord.objects.filter(imgname=imgname)
        
        # 初始化计数器
        total_judgments = records.count()
        correct_judgments = records.filter(iscorrect=True).count()
        reason1_count = 0
        reason2_count = 0
        reason3_count = 0
        reason4_count = 0
        
        # 手动统计不同理由的次数
        for record in records:
            # 处理逗号分隔的理由
            if record.reason:
                reasons = record.reason.split(',')
                for reason in reasons:
                    reason = reason.strip()
                    if reason == '1':
                        reason1_count += 1
                    elif reason == '2':
                        reason2_count += 1
                    elif reason == '3':
                        reason3_count += 1
                    elif reason == '4':
                        reason4_count += 1
        
        # 更新或创建统计记录
        if total_judgments > 0:
            stats_obj, created = cls.objects.update_or_create(
                imgname=imgname,
                defaults={
                    'total_judgments': total_judgments,
                    'correct_judgments': correct_judgments,
                    'reason1_count': reason1_count,
                    'reason2_count': reason2_count,
                    'reason3_count': reason3_count,
                    'reason4_count': reason4_count,
                }
            )
            return {
                'total_judgments': total_judgments,
                'correct_judgments': correct_judgments,
                'reason1_count': reason1_count,
                'reason2_count': reason2_count,
                'reason3_count': reason3_count,
                'reason4_count': reason4_count,
                'created': created
            }
        return None