from collections import OrderedDict

from .models import ContentCategory, Content
from goods.models import GoodsCategory, GoodsChannel


def get_category():

    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    categories = OrderedDict()

    for channel in channels:
        # 37频道  11组
        group_id = channel.group_id
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}

        cat1 = channel.category
        categories[group_id]['channels'].append(
            {
                'id': cat1.id,
                "name": cat1.name,
                'url': channel.url,
            }
        )
        # 查询二级和三级类别
        # 查询二级条件是parent_id = cat1.id
        # for cat2 in cat1.subs.all()
        for cat2 in GoodsCategory.objects.filter(parent_id=cat1.id):
            cat2.sub_cats = []
            categories[group_id]['sub_cats'].append({
                "id": cat2.id,
                "name": cat2.name,
                "sub_cats": cat2.sub_cats,
            })

            for cat3 in GoodsCategory.objects.filter(parent_id=cat2.id):
                cat2.sub_cats.append({
                    "id": cat3.id,
                    "name": cat3.name
                })

    return categories
