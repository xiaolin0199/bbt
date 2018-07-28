======
课程表
======


字段说明
--------
.. include:: /rst/api/db/lessonschedule.dbinfo.rst


导入课表
--------

前端请求: ``POST /system/lesson_schedule/import/``

.. note:: 导入的文件模板参考导出得到的文件


.. literalinclude:: /static/json/api/db/lesson_schedule.import.json
    :language: json

后端回应:

.. literalinclude:: /static/json/api/db/lesson_schedule.import.ret.json
    :language: json


导出课表
--------

前端请求: ``GET /system/lesson-schedule/export/?grade_name={grade_name}&class_name={class_name}``

后端回应:

.. literalinclude:: /static/json/api/db/lesson_schedule.export.ret.json
    :language: json
