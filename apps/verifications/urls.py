from django.urls import path, re_path

from .views import ImageVIew, SMSCodeView
# app_name = 'verification'

urlpatterns = [
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$', ImageVIew.as_view()),

    # re_path(r'^sms_codes/$', SMSCodeView.as_view()),
    re_path(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', SMSCodeView.as_view()),

]