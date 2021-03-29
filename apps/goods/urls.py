from django.urls import path, re_path
from .views import GoodsListView, HotGoodsView

app_name = "goods"

urlpatterns = [
    # 商品列表页面
    re_path(r"^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$", GoodsListView.as_view(), name='list'),
    # 商品热销排行
    re_path(r"^hot/(?P<category_id>\d+)/$", HotGoodsView.as_view())

]