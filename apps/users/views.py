from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.contrib.auth.hashers import check_password
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings

# from users.models import User
from .forms import RegisterForm, LoginForm
from .models import User, Address
from utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email

from utils.response_code import RETCODE
from .utils import generate_verify_email_url, check_verify_email_token
from .constants import USER_ADDRESS_COUNT
from goods.models import SKU

import json, re, logging

logger = logging.getLogger('django')


class UserBrowseHistory(LoginRequiredJSONMixin, View):
    """浏览记录"""
    def post(self, request):
        """保存用户浏览记录"""
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')

        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return HttpResponseForbidden('sku_id不存在')

        redis_conn = get_redis_connection('history')
        user = request.user
        pl = redis_conn.pipeline()
        # 去重复
        pl.lrem('history_%s' % user.id, 0, sku_id)
        # 保存
        pl.lpush('history_%s' % user.id, sku_id)
        # 截取
        pl.ltrim('history_%s' % user.id, 0, 4)
        # 执行
        pl.execute()

        # 响应结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """查询用户商品浏览器记录"""

        redis_conn = get_redis_connection('history')
        user = request.user
        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, -1)
        # print(sku_ids)

        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url,

            })

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


class ChangPWDView(LoginRequiredMixin, View):
    """更改密码"""

    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        # 获取参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')
        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return HttpResponseForbidden('参数不完整')
        if new_password != new_password2:
            return HttpResponseForbidden('两次输入的密码不一致')
        # user = authenticate(username=request.user, password=old_password)
        # if user is None:
        #     return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        try:
            # from django.contrib.auth.hashers import check_password
            # request.user.check_password(old_password)
            # print(request.user.check_password(old_password))
            user = request.user.check_password(old_password)
            if not user:
                return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return HttpResponseForbidden('密码最少8位，最长20位')

            # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

        # 清理状态保持信息
        logout(request)
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')

        # # 响应密码修改结果：重定向到登录界面
        return response


class DefaultAddressView(LoginRequiredJSONMixin, View):
    """设置默认地址"""
    def put(self, request, address_id):
        """
        更改 default_address_id
        :param request:
        :param address_id:
        :return:
        """
        try:
            address = Address.objects.get(id=address_id)
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateDestoryAddressView(LoginRequiredMixin, View):
    """更改/删除地址"""

    def put(self, request, address_id):
        """

        :param request:
        :param address_id:
        :return:
        """
        # 接收参数  校验参数
        json_str = request.body.decode()  # 字节
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        # 更新数据
        try:
            # update 返回受影响的行数
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
        except Exception as e:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '修改地址失败'})
        address = Address.objects.get(id=address_id)

        address_dict = {
            'id': address.id,
            'receiver': address.title,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }
        # 响应新的地址给前端渲染
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '修改地址成功', 'address': address_dict})

    def delete(self, request, address_id):
        """
        删除地址
        :param request:
        :param address_id:
        :return:
        """
        # 逻辑删除(修改is_delete状态)
        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()
        except Exception as e:
            return JsonResponse({"code": RETCODE.DBERR, 'errmsg': "删除地址失败"})
        return JsonResponse({"code": RETCODE.OK, 'errmsg': "删除地址成功"})


class AddressCreateView(LoginRequiredJSONMixin, View):
    """新增地址"""

    def post(self, request):
        """
        新增地址逻辑
        :param request:
        :return:
        """
        # 查询已存储地址数量<20
        count = Address.objects.filter(user=request.user).count()

        # print(count)
        if count > USER_ADDRESS_COUNT:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '地址数量超过上限'})

        # 接收参数  校验参数
        json_str = request.body.decode()  # 字节
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')
        # 保存用户传入的数据
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email,
            )
            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            return JsonResponse({"code": RETCODE.DBERR, 'errmsg': "新增地址失败"})

        address_dict = {
            'id': address.id,
            "title": address.title,
            'receiver': address.title,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """
        收货地址页面
        :param request:
        :return:
        """
        # 查询
        addresses = Address.objects.filter(user=request.user, is_deleted=False)

        address_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_list.append(address_dict)
        context = {
            'addresses': address_list,
            'default_address_id': request.user.default_address_id,
        }

        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """
        更改页面
        :param request:
        :return:
        """
        pass


class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        # 1. 接收
        token = request.GET.get('token')
        if not token:
            return HttpResponseForbidden('缺少token')
        # 2.解密  对比加密参数
        user = check_verify_email_token(token)
        if user.email_active == 0:
            user.email_active = True
            user.save()
        else:
            return HttpResponseForbidden("邮箱已经激活")
        # 3.查询用户判断是否唯一  更改email_active是否已经激活为True，没有则激活

        # 4.响应结果
        return redirect(reverse('users:info'))


class EmailView(LoginRequiredJSONMixin, View):
    """邮箱发送"""

    def put(self, request):
        """
        put请求内容在body里
        :param request:
        :return:
        """
        # print(request)
        # 接受参数
        json_str = request.body.decode()
        # print(json_str) # 此时是一个字符串
        json_dict = json.loads(json_str)
        email = json_dict.get('email')
        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('参数邮箱格式有误')
        # 保存
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        # 发送邮件
        # subject = "商城邮箱验证"
        # html_message = '<p>尊敬的用户您好！</p>' \
        #                '<p>感谢您使用商城。</p>' \
        #                '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
        #                '<p><a href="%s">%s<a></p>' % (email, 'www.baidu.com', 'www.baidu.com')
        # send_mail(subject, '', from_email=settings.EMAIL_FROM, recipient_list=[email], html_message=html_message)
        verify_url = generate_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)
        # 激活成功
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})


class UserInfotView(LoginRequiredMixin, View):
    # 未登录跳转的地址
    login_url = '/users/login/'

    # 登录后要跳转的地址

    def get(self, request):
        # print(request)
        content = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        return render(request, 'user_center_info.html', context=content)

        # if request.user.is_authenticated:
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect(reverse('users:login'))


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """
        实现退出登录逻辑
        :param request:
        :return:
        """
        logout(request)
        # 重定向
        response = redirect(reverse('contents:index'))
        # 删除cookie
        response.delete_cookie('username')
        return response


class LoginView(View):
    """用户登录"""

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 接收参数
        # login_form = LoginForm(request.POST)
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            remembered = login_form.cleaned_data.get('remembered')

            if not all([username, password]):
                return HttpResponseForbidden('缺少必传参数')

            # 认证登录用户
            # user = User.objects.get(username=username)
            # pwd = user.password  # 密文
            # user.check_password()
            # if check_password(password, pwd):
            #     print('密码正确')
            # else:
            #     print('密码错误')
            user = authenticate(username=username, password=password)
            # print(user)
            if user is None:
                return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
            # 状态保持
            login(request, user)

            if remembered != True:
                # 没有记住登录  浏览器关闭就销毁
                request.session.set_expiry(0)
            else:
                # 记住登录  状态保持默认为2周
                request.session.set_expiry(None)
            next = request.GET.get('next')
            if next:
                response = redirect(next)
                # return redirect(next)
            else:
                response = redirect(reverse('contents:index'))
            # 将用户名设置到cookie中

            # 响应结果 重定向到首页；
            # return redirect(reverse('content:index'))
            # response = redirect(reverse('content:index'))
            response.set_cookie('username', user.username, max_age=3600)

            # 登陆成功后合并购物车
            from carts.utils import merge_carts_cookies_redis
            merge_carts_cookies_redis(request, user, response)

            return response
        else:
            # print(login_form.errors)
            # print(login_form.errors.get_json_data())
            context = {
                'forms_errors': login_form.errors
            }
            return render(request, 'login.html', context=context)

        # 校验参数
        # if login_form.is_valid():
        #     username = login_form.cleaned_data.get('username')
        #     password = login_form.cleaned_data.get('password')
        #     remembered = login_form.cleaned_data.get('remembered')
        #     # print(username, password)
        #     if not all([username, password]):
        #         return HttpResponseForbidden("缺少毕传参数(账号或密码)")
        #
        #     # 认证登陆用户
        #     # user = User.objects.get(username=username)
        #     # pwd = user.password  # 密文
        #     # user.check_password()
        #     # if check_password(password, pwd):
        #     #     print("密码正确")
        #     # else:
        #     #     print("密码错误")
        #     # 认证用户
        #     user = authenticate(username=username, password=password)
        #     # print(user)
        #     if user is None:
        #         return render(request, 'login.html', {"account_errmsg": "账号或密码错误"})
        #     login(request, user)
        #
        #     if remembered != True:
        #         # 设置过期时间，0表示关闭浏览器就过期,None表示默认联合国周
        #         request.session.set_expiry(0)
        #     else:
        #         # 默认保持两周
        #         request.session.set_expiry(None)
        #
        #     # 重定向
        #     return redirect(reverse("content:index"))


class RegisterView(View):
    """注册页面"""

    def get(self, request):
        """提供用户注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """用户注册逻辑
        """
        # 校验参数
        register_form = RegisterForm(request.POST)

        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            mobile = register_form.cleaned_data.get('mobile')
            # 短信验证码
            sms_code_client = register_form.cleaned_data.get('sms_code')
            redis_conn = get_redis_connection('verify_code')
            sms_code_server = redis_conn.get('sms_{}'.format(mobile))

            if sms_code_server is None:
                return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
            # 对比
            if sms_code_client != sms_code_server.decode():
                return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码错误'})

            # 保存到数据库
            try:
                user = User.objects.create_user(username=username, password=password, mobile=mobile)

            except Exception as e:
                return render(request, 'register.html', {"register_errmsg": "注册失败"})
            # return HttpResponse("注册成功")
            # 状态保持
            login(request, user)
            next = request.GET.get('next')
            if next:
                response = redirect(next)
                # return redirect(next)
            else:
                response = redirect(reverse('content:index'))
            # 将用户名设置到cookie中

            # 响应结果 重定向到首页；
            # return redirect(reverse('content:index'))
            # response = redirect(reverse('content:index'))
            response.set_cookie('username', user.username, max_age=3600)
            # return redirect(reverse('content:index'))
            return response
        else:
            print(register_form.errors.get_json_data())
            context = {
                'forms_error': register_form.errors.get_json_data()
            }
            return render(request, 'register.html', context=context)


class UsernameCountView(View):
    """用户名是否重复注册"""

    def get(self, request, username):
        """
        ajax请求
        :param request:
        :param username: 用户名
        :return: 返回判断用户名是否重复
        """
        count = User.objects.filter(username=username).count()
        content = {
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'count': count,
        }
        return JsonResponse(content)
