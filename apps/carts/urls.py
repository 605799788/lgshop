from django.urls import path
from .views import CartsView, CartsSelectAllView

app_name = "carts"


urlpatterns = [
    # 购物车
    path("", CartsView.as_view(), name="info"),
    # 全选
    path("selection/", CartsSelectAllView.as_view())

]