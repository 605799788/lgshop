from django.shortcuts import render
from django.views import View
from django import http
from django.core.cache import cache

from django_redis import get_redis_connection

from .models import Area
from utils.response_code import RETCODE
# Create your views here.


class AreasView(View):
    """省市区三级联动"""
    def get(self, request):
        # 判断当前查询是省份数据还是市区数据
        area_id = request.GET.get('area_id')
        if not area_id:
            # 将数据缓存到redis中
            province_list = cache.get('province_list')
            if not province_list:
                try:
                    # 查询省级数据  parent_id   null
                    province_model_list = Area.objects.filter(parent_id__isnull=True)
                    # print(province_model_list)
                    province_list = []
                    for province_model in province_model_list:
                        province_dict = {
                            'id': province_model.id,
                            'name': province_model.name
                        }
                        province_list.append(province_dict)
                    # print(province_list)
                    cache.set('province_list', province_list, 3600)
                    # return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok",
                    #                           'province_list': province_list})
                except Exception as e:
                    return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "查询省份信息错误"})
            # else:
            return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok",
                                      'province_list': province_list})
        else:
            sub_data = cache.get('sub_data_' + area_id)
            if not sub_data:
                try:
                    # 查询市区数据
                    # 根据area_id 一查多
                    # 省份id  area_id
                    # parent_id = Area.objects.filter(parent_id=area_id)
                    parent_model = Area.objects.get(id=area_id)  # 获取省份的id
                    sub_model_list = parent_model.subs.all()
                    # print(sub_model_list)

                    subs = []
                    for sub_model in sub_model_list:
                        sub_dict = {
                            'id': sub_model.id,
                            'name': sub_model.name
                        }
                        subs.append(sub_dict)
                    sub_data = {
                        'id': parent_model.id,
                        'name': parent_model.name,
                        'subs': subs
                    }
                    # return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok",
                    #                           'sub_data': sub_data})
                    cache.set('sub_data_' + area_id, sub_data, 3600)
                    # print(sub_data)
                except Exception as e:
                    return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "查询市区信息错误"})
            return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok",
                                      'sub_data': sub_data})