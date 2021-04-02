from django.shortcuts import render
from django.views import View
from django import http
from django_redis import get_redis_connection

from utils.response_code import RETCODE
from goods.models import SKU

import pickle
import base64
import json


class CartsSelectAllView(View):
    """全选"""
    def put(self, request):
        """

        :param request:
        :return:
        """
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')

        # 校验参数
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden("参数selected错误")
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection("carts")
            pl = redis_conn.pipeline()
            redis_cart = pl.hgetall("cart_{}".format(user.id))
            redis_sku_ids = redis_cart.keys()
            if selected:
                # for redis_sku_id in redis_sku_ids:
                #     pl.sadd("selected_{}".format(user.id), redis_sku_id)
                pl.sadd("selected_{}".format(user.id), *redis_sku_ids)

            else:
                for redis_sku_id in redis_sku_ids:
                    pl.srem("selected_{}".format(user.id), redis_sku_id)
            pl.execute()
            return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
        else:
            # 未登录存储cookie
            cart_str = request.COOKIES.get("carts")
            response = http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})

            if cart_str and cart_str != "":
                # 转byte类型字符串
                cart_str_bytes = cart_str.encode()
                # 转byte类型字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转字典
                cart_dict = pickle.loads(cart_dict_bytes)

                for sku_id in cart_dict:
                    cart_dict[sku_id]["selected"] = selected

                # 重新签名加密
                cart_dict_bytes = pickle.dumps(cart_dict)
                cart_str_bytes = base64.b64encode(cart_dict_bytes)
                cookie_cart_str = cart_str_bytes.decode()
                # 将新的购物车数据重新保存到cookie
                # response = http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
                response.set_cookie("carts", cookie_cart_str)
            return response


class CartsView(View):

    def post(self, request):
        """

        :param request:
        :return:
        """
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get("sku_id")
        count = json_dict.get("count")
        selected = json_dict.get('selected', True)  # 可选参数
        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("参数sku_id错误")

        try:
            if count < 0:
                raise ValueError("参数count错误")
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden("参数count错误")

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden("参数selected错误")
        # 是否登陆
        user = request.user
        if user.is_authenticated:
            # 已登录操作redis购物车
            redis_conn = get_redis_connection("carts")
            pl = redis_conn.pipeline()
            # hash存储  以增量计算的形式保存商品数据
            # 查询是否已有数据 sku_idd对应count数量
            shop = redis_conn.hget("cart_{}".format(user.id), sku_id)
            # if shop:
            #     count = int(shop) + count
            #     redis_conn.hset("cart_{}".format(user.id), sku_id, count)
            # else:
            #     redis_conn.hset("cart_{}".format(user.id), sku_id, count)
            # 优化50-54
            pl.hincrby("cart_{}".format(user.id), sku_id, count)
            if selected:
                pl.sadd("selected_{}".format(user.id), sku_id)
            pl.execute()
            return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
        else:
            # 未登录存储cookie
            cart_str = request.COOKIES.get("carts")
            if cart_str:
                # 转byte类型字符串
                cart_str_bytes = cart_str.encode()
                # 转byte类型字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                # cookies已存在购物车, 增量计算
                origin_count = cart_dict[sku_id]["count"]
                count += origin_count
            #     cart_dict[sku_id] = {
            #         'count': count,
            #         'selected': selected,
            #     }
            # else:
            #     cart_dict[sku_id] = {
            #         'count': count,
            #         'selected': selected,
            #     }
            # 优化79--87
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected,
            }
            # 重新签名加密
            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_cart_str = cart_str_bytes.decode()
            # 将新的购物车数据重新保存到cookie
            response = http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
            response.set_cookie("carts", cookie_cart_str)
            return response

            # 响应结果ajax-json
            # return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})

    def get(self, request):
        """

        :param request:
        :return:
        """
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection("carts")

            redis_cart = redis_conn.hgetall("cart_{}".format(user.id))
            redis_selected = redis_conn.smembers("selected_{}".format(user.id))

            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    "count": int(count),
                    "selected": sku_id in redis_selected,
                }
        else:
            # 未登录存储cookie
            cart_str = request.COOKIES.get("carts")
            if cart_str:
                # 转byte类型字符串
                cart_str_bytes = cart_str.encode()
                # 转byte类型字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),  # True => 'True'
                'name': sku.name,
                'default_image_url': sku.default_image_url.url,
                'price': str(sku.price),
                'amount': str(sku.price * cart_dict.get(sku.id).get('count'))
            })
        # print(cart_skus)
        context = {
            "cart_skus": cart_skus,
        }
        return render(request, "carts.html", context=context)

    def put(self, request):
        """
        购物车更改数据
        :param request:
        :return:
        """
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get("sku_id")
        count = json_dict.get("count")
        selected = json_dict.get('selected', True)   # 可选参数
        # 校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("参数sku_id错误")

        try:
            if count < 0:
                raise ValueError("参数count错误")
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden("参数count错误")

        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden("参数selected错误")

        user = request.user
        if user.is_authenticated:
            # 已登录
            redis_conn = get_redis_connection("carts")
            pl = redis_conn.pipeline()
            # 覆盖已有数据   操作哈希
            pl.hset("cart_{}".format(user.id), sku_id, count)
            if selected:
                pl.sadd("selected_{}".format(user.id), sku_id)
            else:
                pl.srem("selected_{}".format(user.id), sku_id)
            pl.execute()
            cart_sku = {
                'id': sku_id,
                'default_image_url': sku.default_image_url.url,
                "name": sku.name,
                "price": sku.price,
                "count": count,
                "amount": sku.price * count,
                "selected": selected,
            }
            return http.JsonResponse({"code": RETCODE.OK,
                                      "errmsg": "ok",
                                      "cart_sku": cart_sku})
        else:
            # 未登录
            cart_str = request.COOKIES.get("carts")
            if cart_str:
                # 转byte类型字符串
                cart_str_bytes = cart_str.encode()
                # 转byte类型字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}

            cart_dict[sku_id] = {
                "count": count,
                "selected": selected,
            }
            cart_sku = {
                'id': sku_id,
                'default_image_url': sku.default_image_url.url,
                "name": sku.name,
                "price": sku.price,
                "count": count,
                "amount": sku.price * count,
                "selected": selected,
            }
            cart_dict_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            cookie_cart_str = cart_str_bytes.decode()

            response = http.JsonResponse({"code": RETCODE.OK,
                                          "errmsg": "ok",
                                          "cart_sku": cart_sku})
            response.set_cookie("carts", cookie_cart_str)
            return response

    def delete(self, request):
        """
        删除购物车
        :param request:
        :return:
        """
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get("sku_id")
        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden("参数sku_id错误")
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection("carts")
            pl = redis_conn.pipeline()
            pl.hdel("cart_{}".format(user.id), sku_id)
            pl.srem("selected_{}".format(user.id), sku_id)
            pl.execute()
            return http.JsonResponse({"code": RETCODE.OK, "errmsg": "ok"})
        else:
            # 未登录
            cart_str = request.COOKIES.get("carts")
            if cart_str:
                # 转byte类型字符串
                cart_str_bytes = cart_str.encode()
                # 转byte类型字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 转字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
            response = http.JsonResponse({"code": RETCODE.OK,
                                          "errmsg": "ok"})
            if sku_id in cart_dict:
                del cart_dict[sku_id]

                cart_dict_bytes = pickle.dumps(cart_dict)
                cart_str_bytes = base64.b64encode(cart_dict_bytes)
                cookie_cart_str = cart_str_bytes.decode()

                # response = http.JsonResponse({"code": RETCODE.OK,
                #                               "errmsg": "ok"})
                response.set_cookie("carts", cookie_cart_str)
            return response





