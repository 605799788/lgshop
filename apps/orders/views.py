from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


class OrderSettlementView(LoginRequiredMixin, View):
    """结算订单"""

    def get(self, request):
        context = {
            'addresses': '',
            'skus': '',
            'total_count': '',   # 购物车商品总件数
            'total_amount': '',    # 总金额
            'freight': '',          # 运费
            'payment_amount': ''       # 实际付款
        }
        return render(request, 'place_order.html', context=context)