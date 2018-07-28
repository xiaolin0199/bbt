========
作息时间
========


字段说明
--------

+------------+---------------+------+--------+------+------+
|    键值    |      类型     | 非空 | 默认值 | 长度 | 说明 |
+============+===============+======+========+======+======+
|    uuid    | CharField(PK) |  √   |        |  40  |      |
+------------+---------------+------+--------+------+------+
|    term    |   ForeignKey  |  √   |        |      |      |
+------------+---------------+------+--------+------+------+
|  sequence  |  IntegerField |  √   |        |      |      |
+------------+---------------+------+--------+------+------+
| start_time |   TimeField   |  √   |        |      |      |
+------------+---------------+------+--------+------+------+
|  end_time  |   TimeField   |  √   |        |      |      |
+------------+---------------+------+--------+------+------+

新建作息时间
------------

前端请求: ``POST /system/lesson_period/add/``

+------------+--------------+------+----------+
| 键值       | 类型         | 非空 | 说明     |
+============+==============+======+==========+
| sequence   | IntegerField | √    | 节次     |
+------------+--------------+------+----------+
| start_time | TimeField    | √    | 开始时间 |
+------------+--------------+------+----------+
| end_time   | TimeField    | √    | 结束时间 |
+------------+--------------+------+----------+

.. literalinclude:: /static/json/api/db/lesson_period.create.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_period.create.ret.json
    :language: json


作息时间列表
------------

前端请求: ``GET /system/lesson_period/list/``

后端回应:

.. literalinclude:: /static/json/api/db/lesson_period.list.json
    :language: json


编辑作息时间
------------

+------------+---------------+------+----------+
| 键值       | 类型          | 非空 | 说明     |
+============+===============+======+==========+
| uuid       | CharField(PK) | √    | 主键     |
+------------+---------------+------+----------+
| sequence   | IntegerField  | √    | 节次     |
+------------+---------------+------+----------+
| start_time | TimeField     | √    | 开始时间 |
+------------+---------------+------+----------+
| end_time   | TimeField     | √    | 结束时间 |
+------------+---------------+------+----------+

前端请求: ``POST /system/lesson_period/edit/``

.. literalinclude:: /static/json/api/db/lesson_period.update.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_period.update.ret.json
    :language: json


删除作息时间
------------

前端请求: ``POST /system/lesson_period/delete/``

.. literalinclude:: /static/json/api/db/lesson_period.delete.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_period.delete.ret.json
    :language: json
