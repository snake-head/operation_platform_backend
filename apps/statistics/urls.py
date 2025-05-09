from django.urls import path
from .views import UserVisitLogView, DailyVisitCountView, HourlyActivityView

urlpatterns = [
    path('user-visit/', UserVisitLogView.as_view(), name='user-visit-log'),
    path('daily-visits/', DailyVisitCountView.as_view(), name='daily-visit-counts'),
    path('hourly-activity/', HourlyActivityView.as_view(), name='hourly-activity'),
]