# @ Time    : 2021/3/31 21:38
# @ Author  : JuRan
import base64
import pickle

from django_redis import get_redis_connection


def merge_carts_cookies_redis(request, user, response):
    """
    合并购物车
    相同的商品 用cookie覆盖redis
    redis当中有的 cookie 里面没有 保留redis中的
    勾选状态以cookie为准的

    1.获取cookies中的购物车数据
    2.判断cookies中的购物车数据是否存在
    3.如果存在,需要合并
    4.如果不存在,不需要合并
    5.准备新的数据容器  保存新的数据  sku_id count selected  unselected
    6.遍历出cookies中的购物车数据
    7.根据新的数据结构,合并到redis中   将cookies中的数据调整成redis中一样
    :return:
    """
    # 获取cookies中的购物车数据
    cart_str = request.COOKIES.get('carts')

    if not cart_str and cart_str != 'gAN9cQAu':
        return response

    # 转成bytes类型的字符串
    cookie_cart_str_bytes = cart_str.encode()
    # 转成bytes类型的字典
    cookie_cart_dict_bytes = base64.b64decode(cookie_cart_str_bytes)
    # 转成真正的字典
    cookie_cart_dict = pickle.loads(cookie_cart_dict_bytes)

    # {sku_id:count}  selected=>[]  unselected=>[]
    new_cart_dict = {}
    new_selected_add = []
    new_selected_rem = []

    # cart_dict = {'1': {'count': 10, 'selected': True}, '2': {'count': 20, 'selected': False}}

    for sku_id, cookie_dict in cookie_cart_dict.items():
        new_cart_dict[sku_id] = cookie_dict['count']

        if cookie_dict['selected']:
            new_selected_add.append(sku_id)
        else:
            new_selected_rem.append(sku_id)

    # 写入到redis
    redis_conn = get_redis_connection('carts')

    pl = redis_conn.pipeline()
    pl.hmset('cart_%s' % user.id, new_cart_dict)

    if new_selected_add:
        pl.sadd('selected_%s' % user.id, *new_selected_add)

    if new_selected_rem:
        pl.srem('selected_%s' % user.id, *new_selected_rem)

    pl.execute()

    # 删除cookies
    response.delete_cookie('carts')

    return response

