from django.shortcuts import render
from django.views import View
from django import http
from django.core.paginator import Paginator
from django.utils import timezone

from contents.utils import get_category
from .models import GoodsCategory, SKU, SPUSpecification, SKUSpecification, GoodsVisitCount
from .utils import get_breadcrumb
from utils.response_code import RETCODE


class DetailVisitView(View):
    """统计分类商品的访问量"""
    def post(self, request, category_id):
        """

        :param request:
        :param category_id:
        :return:
        """
        # 校验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return http.HttpResponseForbidden("category_id不存在")

        # 获取当天日期
        t = timezone.localtime()
        today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)
        try:
            # 查询
            counts_data = GoodsVisitCount.objects.get(date=today_str, category_id=category.id)
        except GoodsVisitCount.DoesNotExist:
            # 不存在--》新增
            counts_data = GoodsVisitCount()
        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.date = today_str
            counts_data.save()
        except Exception as e:
            print(e)
            return http.HttpResponseServerError("统计失败")

        # 相应结果
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})


class DetailGoodsView(View):
    """商品详情页"""
    def get(self, request, sku_id):
        """

        :param sku_id:
        :return:
        """
        # 验证sku_id
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return render(request, "404.html")


        # 商品分类
        categories = get_category()
        # 面包屑
        breadcrumb = get_breadcrumb(sku.category)
        # 热销排行

        # 构建当前商品的规格键  当前sku id为1的默认的规格
        sku_specs = SKUSpecification.objects.filter(sku__id=sku_id).order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # [1, 4, 7]
        # print(sku_key)

        # 获取当前商品的所有SKU
        spu_id = sku.spu_id
        skus = SKU.objects.filter(spu_id=spu_id)

        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')

            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # print(spec_sku_map)

        # 获取当前商品的规格信息
        goods_specs = SPUSpecification.objects.filter(spu_id=spu_id).order_by('id')
        # print(goods_specs)
        # 若当前sku的规格信息不完整，则不再继续
        # if len(sku_key) < len(goods_specs):
        #     return

        for index, spec in enumerate(goods_specs):
            # print(index, spec)
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                # [1,4,7]
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        context = {
            "categories": categories,
            "breadcrumb": breadcrumb,
            "sku": sku,
            'specs': goods_specs
        }

        return render(request, "detail.html", context=context)


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