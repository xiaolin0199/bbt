# coding=utf-8


def pagination(queryset, page_num=1, page_size=30, order_field=None,
               order_direction='desc'):
    '''pagination不再使用，应该用django.core.paginator.Paginator'''
    try:
        record_count = queryset.count()
    except Exception:
        record_count = len(queryset)

    page_count = record_count // page_size
    if record_count % page_size > 0:
        page_count += 1

    if page_num > page_count:
        page_num = 1

    offset = (page_num - 1) * page_size

    if order_field:
        order_fields = []
        if isinstance(order_field, (str, unicode)):
            if order_direction == 'desc':
                order_fields.append('-%s' % order_field)

            else:
                order_fields.append(order_field)

        elif isinstance(order_field, list):
            for f in order_field:
                if order_direction == 'desc':
                    order_fields.append('-%s' % f)

                else:
                    order_fields.append(f)

        if order_fields:
            try:
                queryset = queryset.order_by(*order_fields)
            except Exception:
                pass

    try:
        queryset = queryset.all()[offset:offset + page_size]
    except Exception:
        queryset = queryset[offset:offset + page_size]

    return {
        'record_count': record_count,
        'page_count': page_count,
        'page_num': page_num,
        'page_size': page_size,
        'records': queryset,
    }
