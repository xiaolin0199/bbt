/**
 * 班班通校级管理配置
 */
var bbtConfig = bbtConfig || {};
Ext.apply(bbtConfig, {
    bbtUsageLog: {
        login: {
            grid: {
                title: '班班通使用记录',
                apiKey: 'teacher_using_history_grid_data',
                tools: ['qdate', 'startDate', 'endDate', 'course', 'teacherName', 'query'],
                fields: ['teacher', 'started_at', 'stopped_at', 'lesson_no', 'grade', 'class', 'lesson_name', 'resource_using_histories'],
                headers: ['教师姓名', '开始时间', '结束时间', '节次', '年级', '班级', '科目', '资源类型'],
                pagination: true, 
                status: '{year}年{level}所有科目共有{count}次登录记录'
            }
        },
        unlogin: {
            grid: {
                title: '班班通未使用记录',
                apiKey: 'teacher_not_using_history_grid_data',
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'teacherName', 'query'],
                fields: ['no', 'username', 'register_at', 'age', 'sex', 'edu_background', 'title'],
                headers: ['注册编号', '教师姓名', '注册时间', '年龄', '性别', '教育背景', '职称'],
                pagination: true,
                status: '{year}年{level}共有{count}个教师未登录班班通'
            }
        }
    },
    //班班通分析统计
    bbtAnalyzeStatic: {
        assetlist: {
            grid: {
                title: '资产记录',
                addLevelHeader: true,
                apiKey: 'asset_manage_grid_data',
                headers: ['资产名称', '年级班级', '出厂时间', '设备型号', '资产类型', '资产状态', '申报用户', '申报日期', '申报状态'],
                fields: ['name', 'class_and_grade', 'date_of_manufacture', 'machine_model', 'type', 'status', 'reported_by_user', 'reported_at', 'is_pass'],
                tools: ['town', 'school', 'assetname', 'report_user', 'qdate', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}资产总数：{count}'
            }            
        },
        assetstat: {
            grid: [{
                title: '现存资产',
                addLevelHeader: true,
                apiKey: 'asset_statistic_using_grid_data',
                headers: ['资产名称', '申报用户', '年级', '班级', '申报日期', '资产数量', '资产状态'],
                fields: ['name', 'reported_by_user', 'grade', 'class', 'reported_at', 'num', 'status'],
                tools: ['town', 'school', 'assetname', 'report_user', 'qdate', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}资产总数：{count}'
            }, {
                title: '报废资产',
                addLevelHeader: true,
                apiKey: 'asset_statistic_scrapped_grid_data',
                headers: ['资产名称', '申报用户', '年级', '班级', '申报日期', '资产数量', '资产状态'],
                fields: ['name', 'reported_by_user', 'grade', 'class', 'reported_at', 'num', 'status'],
                tools: ['town', 'school', 'assetname', 'report_user', 'qdate', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}报废资产总数：{count}'
            }]
        },
        assetrepairhistosy: {
            grid: {
                title: '资产维修记录',
                addLevelHeader: true,
                apiKey: 'asset_repaired_history_grid_data',
                headers: ['资产名称', '申报用户', '年级', '班级', '申报日期', '资产状态'],
                fields: ['name', 'reported_by_user', 'grade', 'class', 'reported_at', 'status', 'class_and_grade'],
                tools: ['town', 'school', 'assetname', 'report_user', 'qdate', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}资产维修总次数:{count}'
            }
        },
        //教师授课统计
        teach: {
            title: '教师授课统计',
            grid: {
                apiKey: 'statistic_lesson_by_lesson_name_and_teacher',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['teacher__username', 'lesson_name', 'scheduled_num', 'real_finished_num'],
                headers: ['教师', '科目', '计划授课次数', '实际授课次数'],
                status: '{level}当前授课总次数：{count}'
            },
            chart: {
                apiKey: 'statistic_lesson_by_lesson_name_and_teacher',
                x: 'teacher__username',
                ytitle: '授课数',
                y: ['scheduled_num', 'real_finished_num'],
                //xtitle: '教师',
                seriesTitle: ['计划授课次数', '实际授课次数'],
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['teacher__username', 'scheduled_num', 'real_finished_num']
            }
        },
        //授课次数统计
        teachCount: {
            title: '教师授课次数统计',
            grid: [{
                title: '按学校统计',
                apiKey: 'statistic_lesson_by_school',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['school__name', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['学校', '计划课时', '完成课时', '剩余课时', '课时完成率']
            }, {
                title: '按年级统计',
                apiKey: 'statistic_lesson_by_grade',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['class_and_grade__grade_number', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['年级', '计划课时', '完成课时', '剩余课时', '课时完成率']
            }, {
                title: '按班级统计',
                apiKey: 'statistic_lesson_by_class',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['class_and_grade__grade_number', 'class_and_grade__class_number', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['年级', '班级', '计划课时', '完成课时', '剩余课时', '课时完成率']
            }],
            chart: [{
                title: '按学校统计',
                apiKey: 'statistic_lesson_by_school',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['school__name', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                x: 'school__name',
                //xtitle: '学校',
                ytitle: '课时数',
                y: ['scheduled_num', 'real_finished_num'],
                seriesTitle: ['计划课时', '完成课时']
            }, {
                title: '按年级统计',
                apiKey: 'statistic_lesson_by_grade',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['class_and_grade__grade_number', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                x: 'class_and_grade__grade_number',
                //xtitle: '年级',
                ytitle: '课时数',
                y: ['scheduled_num', 'real_finished_num'],
                seriesTitle: ['计划课时', '完成课时']
            }, {
                title: '按班级统计',
                apiKey: 'statistic_lesson_by_class',
                tools: ['town', 'school', 'year', 'month', 'query'],
                fields: ['class_and_grade__grade_number', 'class_and_grade__class_number', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                x: 'class_and_grade__class_number',
                //xtitle: '班级',
                ytitle: '课时数',
                y: ['scheduled_num', 'real_finished_num'],
                seriesTitle: ['计划课时', '完成课时']
            }]
        },
        //教师人数统计
        teacherCount: {
            grid: {
                apiKey: 'statistic_number_of_teacher_grid_data',
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['school__name', 'teacher_num', 'teaching_teacher_num', 'cha', 'rate'],
                headers: ['学校', '登记教师总数（人）', '授课教师人数（人）', '人数差', '授课教师占登记教师比例（%）']
            },
            chart: [{
                apiKey: 'statistic_number_of_teacher_grid_data',
                x: 'school__name',
                //xtitle: '学校',
                ytitle: '教师数',
                y: ['teacher_num', 'teaching_teacher_num'],
                seriesTitle: ['登记教师人数', '授课教师人数'],
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['school__name', 'teacher_num', 'teaching_teacher_num']
            }]
        },
        resource: {
            title: '资源使用统计',
            grid: [{
                title: '按年级统计',
                apiKey: 'statistic_resource_by_grade',
                tools: ['town', 'school', 'grade', 'mediaType', 'query'],
                headers: ['年级', '资源类型', '访问次数'],
                fields: ['class_and_grade__grade_number', 'resource_using_histories__resource_type', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title: '按班级统计',
                apiKey: 'statistic_resource_by_class',
                tools: ['town', 'school', 'grade', 'class', 'mediaType', 'query'],
                headers: ['年级', '班级', '资源类型', '访问次数'],
                fields: ['class_and_grade__grade_number', 'class_and_grade__class_number', 'resource_using_histories__resource_type', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title: '按教师统计',
                apiKey: 'statistic_resource_by_teacher',
                tools: ['town', 'school', 'teacherName', 'mediaType', 'query'],
                headers: ['学校', '教师姓名', '资源类型', '访问次数'],
                fields: ['teacher__school__name', 'teacher__username', 'resource_using_histories__resource_type', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title : '按科目统计',
                apiKey: 'statistic_resource_by_lesson_name',
                tools: ['town', 'school', 'course', 'mediaType', 'query'],
                headers: ['科目', '资源类型', '访问次数'],
                fields: ['lesson_name', 'resource_using_histories__resource_type', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title: '按学校统计',
                apiKey: 'statistic_resource_by_school',
                tools: ['town', 'school', 'mediaType', 'query'],
                headers: ['学校', '资源类型', '访问次数'],
                fields: ['class_and_grade__school__name', 'resource_using_histories__resource_type', 'number'],
                status: '{level}资源访问总次数：{count}'
            }],
            chart: [{
                title: '按年级统计',
                apiKey: 'statistic_resource_by_grade',
                tools: ['town', 'school', 'grade', 'mediaType', 'query'],
                x: 'class_and_grade__grade_number',
                y: 'number',
                seriesTitle: ['访问次数'],
                //xtitle: '年级',
                ytitle: '访问次数',
                fields: ['class_and_grade__grade_number', 'resource_using_histories__resource_name', 'number']
            }, {
                title: '按班级统计',
                apiKey: 'statistic_resource_by_class',
                tools: ['town', 'school', 'grade', 'class', 'mediaType', 'query'],
                x: 'class_and_grade__class_number',
                y: 'number',
                //xtitle: '班级',
                ytitle: '访问次数',
                seriesTitle: ['访问次数'],
                fields: ['class_and_grade__grade_number', 'class_and_grade__class_number', 'resource_using_histories__resource_name', 'number']
            }, {
                title: '按教师统计',
                apiKey: 'statistic_resource_by_teacher',
                tools: ['town', 'school', 'teacherName', 'mediaType', 'query'],
                x: 'teacher__username',
                y: 'number',
                //xtitle: '教师',
                ytitle: '访问次数',
                seriesTitle: ['访问次数'],
                fields: ['teacher__school__name', 'teacher__username', 'resource_using_histories__resource_name', 'number']
            }, {
                title : '按科目统计',
                apiKey: 'statistic_resource_by_lesson_name',
                tools: ['town', 'school', 'course', 'mediaType', 'query'],
                x: 'lesson_name',
                y: 'number',
                //xtitle: '科目',
                ytitle: '访问次数',
                seriesTitle: ['访问次数'],
                fields: ['lesson_name', 'resource_using_histories__resource_name', 'number']
            }, {
                title: '按学校统计',
                apiKey: 'statistic_resource_by_school',
                tools: ['town', 'school', 'mediaType', 'query'],
                x: 'class_and_grade__school__name',
                y: 'number',
                //xtitle: '学校',
                ytitle: '访问次数',
                seriesTitle: ['访问次数'],
                fields: ['class_and_grade__school__name', 'resource_using_histories__resource_name', 'number']
            }]
        },
        login: {
            grid: {
                apiKey: 'statistic_teacher_using_by_school',
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                headers: ['学校名称', '登录人数'],
                fields: ['school__name', 'number']
            },
            chart: {
                title: '按学校统计',
                apiKey: 'statistic_teacher_using_by_school',
                x: 'school__name',
                //xtitle: '教师名称',
                y: 'number',
                ytitle: '登录次数',
                seriesTitle: ['学校'],
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['school__name', 'number']
            }
        },
        unlogin: {
            grid: {
                apiKey: 'statistic_teacher_not_using_by_school',
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                headers: ['省', '市', '县/区', '乡/镇', '学校名称', '未登录人数'],
                fields: ['province__name', 'city__name', 'country__name', 'town__name', 'school__name', 'number']
            },
            chart: [{
                apiKey: 'statistic_teacher_not_using_by_school',
                x: 'school__name',
                y: 'number',
                //xtitle: '学校',
                ytitle: '未登录人数',
                seriesTitle: ['未登录人数'],
                tools: ['town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['school__name', 'number']
            }]
        }
    }
});
