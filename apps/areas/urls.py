from django.urls import path
from .views import AreasView

app_name = 'area'

urlpatterns = [
    # 三级联动
    path('areas/', AreasView.as_view()),
]