# coding=utf-8
from django.conf.urls import url
import views.index
import views.statistic
import views.edu_logs
import views.system

urlpatterns = [

    # 乡镇街道>教学点>教室 联动信息
    url(r'^node-tree/list/?$', views.index.get_node_trees),

    # 教师授课>教学点教室使用统计
    url(r'statistic/classroom-use/by-town/?$', views.statistic.classroom_use_by_town),
    url(r'statistic/classroom-use/by-unit/?$', views.statistic.classroom_use_by_unit),
    url(r'statistic/classroom-use/by-unit-class/?$', views.statistic.classroom_use_by_unit_class),
    url(r'statistic/classroom-use/by-town/export/?$', views.statistic.classroom_use_by_town_export),
    url(r'statistic/classroom-use/by-unit/export/?$', views.statistic.classroom_use_by_unit_export),
    url(r'statistic/classroom-use/by-unit-class/export/?$', views.statistic.classroom_use_by_unit_class_export),

    # 教师授课>教学点桌面使用日志
    url(r'screenshot/node-info/?$', views.edu_logs.screenshot_node),
    url(r'screenshot/node-timeline/?$', views.edu_logs.screenshot_timeline),
    url(r'screenshot/details/?$', views.edu_logs.screenshot_data),

    # 教师授课>教学点终端使用日志
    url(r'terminal-use/details/?$', views.edu_logs.terminal_use),

    # 资源使用>卫星资源接收统计
    url(r'statistic/resource-store/by-town/?$', views.statistic.resource_store_by_town),
    url(r'statistic/resource-store/by-unit/?$', views.statistic.resource_store_by_unit),
    url(r'statistic/resource-store/by-town/export/?$', views.statistic.resource_store_by_town_export),
    url(r'statistic/resource-store/by-unit/export/?$', views.statistic.resource_store_by_unit_export),

    # 资源使用>卫星资源接收日志
    url(r'resource-store/details/?$', views.edu_logs.resource_store),

    # 资源使用>教学点终端开机统计
    url(r'statistic/terminal-boot/by-town/?$', views.statistic.terminal_boot_by_town),
    url(r'statistic/terminal-boot/by-unit/?$', views.statistic.terminal_boot_by_unit),
    url(r'statistic/terminal-boot/by-unit-class/?$', views.statistic.terminal_boot_by_unit_class),
    url(r'statistic/terminal-boot/by-town/export/?$', views.statistic.terminal_boot_by_town_export),
    url(r'statistic/terminal-boot/by-unit/export/?$', views.statistic.terminal_boot_by_unit_export),

    # 资源使用>教学点终端开机日志
    url(r'terminal-boot/details/?$', views.edu_logs.terminal_boot),

    # 系统设置>教学点管理
    url(r'^manage/node/add/?$', views.system.edu_node.add),
    url(r'^manage/node/delete/?$', views.system.edu_node.delete),
    url(r'^manage/node/edit/?$', views.system.edu_node.edit),
    url(r'^manage/node/list/?$', views.system.edu_node.list),

    # 系统设置>教学点资源接收目录管理
    url(r'^manage/node/resource-catalog/list/?$', views.system.edu_node.resource_catalog_list),
    url(r'^manage/node/resource-catalog/add/?$', views.system.edu_node.resource_catalog_add),
    url(r'^manage/node/resource-catalog/delete/?$', views.system.edu_node.resource_catalog_delete),

    url(r'^manage/node/resource-catalog/list/new/?$', views.system.edu_node.resource_catalog_list_new),
    url(r'^manage/node/resource-catalog/add/new/?$', views.system.edu_node.resource_catalog_add_new),
    url(r'^manage/node/resource-catalog/delete/new/?$', views.system.edu_node.resource_catalog_delete_new),

    # 系统设置>服务器汇聚管理>教学点终端管理
    url(r'^manage/receiver/list/?$', views.system.leest),
    url(r'^manage/receiver/unbind/?$', views.system.unbind),
    url(r'^manage/client/list/?$', views.system.leest),
    url(r'^manage/client/unbind/?$', views.system.unbind),
    url(r'^manage/items-inherit/?$', views.system.inherit_items),
]
