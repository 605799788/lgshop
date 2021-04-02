from django.urls import path
from .views import OrderSettlementView

app_name = "orders"


urlpatterns = [
    # dingdan
    path('settlement/', OrderSettlementView.as_view(), name='settlement'),


]