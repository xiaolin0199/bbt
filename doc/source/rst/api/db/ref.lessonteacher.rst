========
授课教师
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

新建授课教师
------------

+------------+---------------+------+--------+------+------+
|    键值    |      类型     | 非空 | 默认值 | 长度 | 说明 |
+============+===============+======+========+======+======+
|    term    |   ForeignKey  |  √   |        |      |      |
+------------+---------------+------+--------+------+------+
|  sequence  |  IntegerField |  √   |        |      |      |
+------------+---------------+------+--------+------+------+
| start_time |   TimeField   |  √   |        |      |      |
+------------+---------------+------+--------+------+------+
|  end_time  |   TimeField   |  √   |        |      |      |
+------------+---------------+------+--------+------+------+

前端请求: ``POST /system/lesson_teacher/add/``

.. literalinclude:: /static/json/api/db/lesson_teacher.create.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_teacher.create.ret.json
    :language: json


授课教师列表
------------

前端请求: ``GET /system/lesson_teacher/list/?page={page}&limit={limit}``

后端回应:

.. literalinclude:: /static/json/api/db/lesson_teacher.list.json
    :language: json


编辑授课教师
------------

前端请求: ``POST /system/lesson_teacher/edit/``

.. literalinclude:: /static/json/api/db/lesson_teacher.update.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_teacher.update.ret.json
    :language: json

删除授课教师
------------

前端请求: ``POST /system/lesson_teacher/delete/``

.. literalinclude:: /static/json/api/db/lesson_teacher.delete.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_teacher.delete.ret.json
    :language: json


导入授课教师
------------

前端请求: ``POST /system/lesson_teacher/import/``

.. note:: 导入的文件模板参考导出得到的文件

.. include:: /static/json/api/db/lesson_teacher.import.json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_teacher.import.ret.json
    :language: json


导出授课教师
------------

前端请求: ``GET /system/lesson_teacher/export/``

后端回应:

.. literalinclude:: /static/json/api/db/lesson_teacher.export.ret.json
    :language: json

