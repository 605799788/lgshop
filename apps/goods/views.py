from django.shortcuts import render
from django.views import View
from django import http
from django.core.paginator import Paginator

from contents.utils import get_category
from .models import GoodsCategory, SKU
from .utils import get_breadcrumb
from utils.response_code import RETCODE


class HotGoodsView(View):
    """热销商品"""
    def get(self, request, category_id):

        # 查询指定分类 必须是上架的 排序销量最好的order_by
        skus = SKU.objects.filter(category_id=category_id,
                                  is_launched=True).order_by('-sales')[:2]
        # 模型转字典
        hot_skus = []
        for sku in skus:
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url
            }
            hot_skus.append(sku_dict)
        return http.JsonResponse({"code": RETCODE.OK,
                                  "errmsg": "OK",
                                  "hot_skus": hot_skus})


class GoodsListView(View):
    """商品列表页面"""
    def get(self, request, category_id, page_num):
        """

        :param request:
        :param category_id:
        :param page_num:
        :return:
        """
        # category_id先校验此参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden("参数category_id不存在")

        sort = request.GET.get('sort', 'default')
        if sort == "price":
            sort_field = "price"
        elif sort == "hot":
            sort_field = "sales"
        else:
            sort = 'default'
            sort_field = 'create_time'
        categories = get_category()

        breadcrumb = get_breadcrumb(category)
        # 一级
        # if category.parent is None:
        #     breadcrumb["cat1"] = category
        # elif GoodsCategory.objects.filter(parent_id=category.id).count() == 0:
        #     # 三级
        #     breadcrumb["cat1"] = category.parent.parent
        #     breadcrumb["cat2"] = category.parent
        #     breadcrumb["cat3"] = category
        # else:
        #     # 二级
        #     breadcrumb["cat1"] = category.parent
        #     breadcrumb["cat2"] = category
        # print(breadcrumb)
        # 查询面包屑
        # breadcrumb = {
        #     'cat1': category.parent.parent,
        #     'cat2': category.parent,
        #     'cat3': category,
        # }
        # 分页和排序
        skus = SKU.objects.filter(is_launched=True,
                                  category_id=category.id).order_by(sort_field)
        # print(skus)
        # Paginator("要分页的数据", "每页的条数")
        pageinator = Paginator(skus, 5)
        try:
            # 获取要看的那一页数据  page_num
            page_skus = pageinator.page(page_num)
        except Exception as e:
            return http.HttpResponseNotFound("empty page")
        # 总页数
        total_page = pageinator.num_pages
        context = {
            'categories': categories,
            "breadcrumb": breadcrumb,
            "page_skus": page_skus,
            "total_page": total_page,
            "sort": sort,
            "category_id": category_id,
            "page_num": page_num,
                    }

        return render(request, 'list.html', context=context)