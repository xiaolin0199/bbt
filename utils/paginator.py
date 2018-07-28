# coding=utf-8
"""通用分页模块"""

from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Page as DefaultPage,
    Paginator as DefaultPaginator
)


class Paginator(DefaultPaginator):

    def _get_page(self, *args, **kwargs):
        """
        Return an instance of a single page.

        This hook can be used by subclasses to use an alternative to the
        standard :cls:`Page` object.
        """
        return Page(*args, **kwargs)

    def _get_page_info(self, *args, **kwargs):
        """Return page info"""
        return {
            'count': self.count,  # 条目总数
            'per_page': self.per_page,  # 每页条目数
            'num_pages': self.num_pages,  # 页数
        }
    page_info = property(_get_page_info)


class Page(DefaultPage):

    def __getattr__(self, attr):
        # 管理 QuerySet 的属性, 可根据需要添加
        if attr in ['values', ]:
            return getattr(self.object_list, attr)

    def to_dict(self):
        objs = self.object_list
        return [hasattr(o, 'to_dict') and o.to_dict() or o for o in objs]


def paginator(request, objs):
    """
    :param request: django的request对象
    :param objs: 需要分页的目标序列
    :returns: paged_objs（分页之后的一页目标序列），page_info（分页信息）

    ``page_info`` 分页信息是一个dict，结构如下：

    .. code-block:: python

        {
            "count": 20,        # 条目总数
            "num_pages": 10,    # 总页数
            "page": 1,          # 当前页码，从1开始计数
            "per_page": 2,      # 每页条目数，默认25
        }

    使用方法：

        #. 前端request.GET传的参数带上 ``page`` （页数，从1开始）和 ``per_page`` （每页条目数）
        #. 后端正常处理查询，得到结果 ``objs`` （QuerySet）
        #. 后端用此函数对 ``objs`` 进行分页，得到 ``paged_objs`` 和 ``page_info``
        #. 后端回应 ``objs`` 和 ``page_info`` 给前端，一般而言，需要用JSON包装起来

    .. attention::

        如果前端传的request.GET参数里没有分页参数，后端就不分页。参考bug 1908。

    前端示例::

        GET /users?per_page=2&page=1

    后端处理：

    .. code-block:: python

        objs = User.objects.all()
        paged_objs, page_info = paginator(request, objs)
        return JsonResponse({
            'page_info': page_info,
            'users': [i.to_dict() for i in paged_objs]
        })

    返回：

    .. code-block:: json

        {
            "page_info": {
                "count": 20,
                "num_pages": 10,
                "page": 1,
                "per_page": 2
            },
            "users": [
                {
                    "id": 1,
                    "name": "zhangsan"
                },
                {
                    "id": 2,
                    "name": "lisi"
                }
            ]
        }

    """
    page = request.GET.get('page')
    per_page = request.GET.get('per_page', '') or request.GET.get('count', '')
    if page is None:  # 如果前端不带分页参数后端就按一页来分
        page = '1'
        if isinstance(objs, list):
            num = len(objs)
        else:
            try:
                num = objs.count()
            except AttributeError:
                num = len(objs)
        per_page = str(num)

    page = page.isdigit() and int(page) or 1
    per_page = per_page.isdigit() and int(per_page) or 25

    p = Paginator(objs, per_page)
    page_info = p.page_info

    try:
        paged_objs = p.page(page)
    except PageNotAnInteger:
        page = 1
        paged_objs = p.page(1)
    except EmptyPage:
        page = p.num_pages
        paged_objs = p.page(p.num_pages)
    page_info.update({'page': page})

    return paged_objs, page_info
