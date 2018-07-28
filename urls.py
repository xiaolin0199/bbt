# coding=utf-8
from django.conf.urls import include, url
from django.views import static
from django.conf import settings

urlpatterns = [
    url(r'', include('BanBanTong.urls', namespace='base')),  # BanBanTong
    # url(r'^django-rq/', include('django_rq.urls')),

    url(r'^terminal/', include('machine_time_used.urls', namespace='machine')),  # 机器时长
    url(r'^edu-unit/', include('edu_point.urls', namespace='eduunit')),  # 教学点
    url(r'^activation/', include('activation.urls', namespace='activate')),  # 授权信息
    url(r'^install/', include('BanBanTong.views.install.urls', namespace='install')),  # 初始化安装
    url(r'^api/', include('BanBanTong.views.api.urls', namespace='api')),  # 客户端

    url(r'^system/', include('BanBanTong.views.system.urls', namespace='system')),  # 系统设置
    url(r'^activity/', include('BanBanTong.views.activity.urls', namespace='activity')),  # 教师授课
    url(r'^statistic/', include('BanBanTong.views.statistic.urls', namespace='statistic')),  # 授权信息
    url(r'^global/', include('BanBanTong.views.global_view.urls', namespace='global')),  # 实时概况>登录状态 桌面预览
    url(r'^global_statistic/', include('BanBanTong.views.global_view.urls', namespace='global_statistic')),  # 实时概况>全局数据
    url(r'^global-statistic/', include('BanBanTong.views.global_view.urls', namespace='global-statistic')),  # 实时概况>全局数据
    url(r'^asset/', include('BanBanTong.views.asset.urls', namespace='asset')),  # 资产管理
    url(r'^maintain/', include('BanBanTong.views.maintain.urls', namespace='maintain')),  # 调试API
    # url(r'^commands/', include('BanBanTong.views.commands.urls', namespace='commands')),  # 脚本命令
    url(r'^doc/json/(?P<path>.*)/?$', static.serve, {'document_root': settings.DOC_JSON_ROOT, 'show_indexes': True}),
]
