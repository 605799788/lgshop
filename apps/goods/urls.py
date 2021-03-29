from django.urls import path, re_path
from .views import GoodsListView, HotGoodsView, DetailGoodsView
from .views import DetailVisitView

app_name = "goods"

urlpatterns = [
    # 商品列表页面
    re_path(r"^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$", GoodsListView.as_view(), name='list'),
    # 商品热销排行
    re_path(r"^hot/(?P<category_id>\d+)/$", HotGoodsView.as_view()),
    # 商品详情
    re_path(r"^detail/(?P<sku_id>\d+)/$", DetailGoodsView.as_view(), name="detail"),
    # 统计商品访问量
    re_path(r"^detail/visit/(?P<category_id>\d+)/$", DetailVisitView.as_view()),

]