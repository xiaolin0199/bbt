/**
 * 班班通省级管理配置
 */
var bbtConfig = bbtConfig || {};
Ext.apply(bbtConfig, {
    bbtUsageLog: {
        login: {
            grid: {
                title: '班班通使用记录',
                apiKey: 'teacher_using_history_grid_data',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['id', 'provinceName', 'cityName', 'countyName', 'townName', 'schoolName'],
                headers: ['编号', '省', '市', '县/区', '乡/镇', '学校'],
                pagination: true,
                status: '{year}年{province}的所有学校共计登录班班通{times}次'
            }
        },
        unlogin: {
            grid: {
                title: '班班通未使用记录',
                apiKey: 'teacher_not_using_history_grid_data',
                tools: ['city', 'country', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__province__name', 'no', 'username', 'register_at'],
                headers: ['省', '注册编号', '教师姓名', '注册时间'],
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
                apiKey: 'asset_manage_grid_data',
                headers: ['省', '资产名称', '年级班级', '出厂时间', '设备型号', '资产类型', '资产状态', '申报用户', '申报日期', '申报状态'],
                fields: ['class_and_grade__province__name', 'name', 'class_and_grade', 'date_of_manufacture', 'machine_model', 'type', 'status', 'reported_by_user', 'reported_at', 'is_pass'],
                tools: ['city', 'country', 'town', 'school', 'assetname', 'report_user', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}资产总数：{count}'
            }            
        },
        assetstat: {
            grid: [{
                title: '现存资产',
                apiKey: 'asset_statistic_using_grid_data',
                headers: ['省', '资产名称', '申报用户', '年级', '班级', '申报日期', '资产数量'],
                fields: ['class_and_grade__province__name', 'class_and_grade__city__name', 'class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school_name', 'teacher__username', 'class_and_grade__grade_number', 'class_and_grade__class_number', 'date', 'number'],
                tools: ['city', 'country', 'town', 'school', 'assetname', 'report_user', 'assetStatus', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}资产总数：{count}'
            }, {
                title: '报废资产',
                apiKey: 'asset_statistic_scrapped_grid_data',
                headers: ['省', '资产名称', '申报用户', '年级', '班级', '申报日期', '资产数量'],
                fields: ['class_and_grade__province__name', 'class_and_grade__city__name', 'class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school_name', 'teacher__username', 'class_and_grade__grade_number', 'class_and_grade__class_number', 'date', 'number'],
                tools: ['city', 'country', 'town', 'school', 'assetname', 'report_user', 'assetStatus', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}报废资产总数：{count}'
            }]
        },
        assetrepairhistosy: {
            grid: {
                title: '资产维修记录',
                apiKey: 'asset_repaired_history_grid_data',
                headers: ['省', '资产名称', '申报用户', '年级', '班级', '申报日期', '资产状态'],
                fields: ['class_and_grade__province__name', 'class_and_grade__city__name', 'class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school_name', 'teacher__username', 'class_and_grade__grade_number', 'class_and_grade__class_number', 'date', 'asset_status'],
                tools: ['city', 'country', 'town', 'school', 'assetname', 'report_user', 'assetStatus', 'startDate', 'endDate', 'query'],
                pagination: true,
                status: '{level}资产维修总次数:{count}'
            }
        },
        //教师人数统计
        teacherCount: {
            grid: [{
                title: '按市统计',
                apiKey: 'statistic_number_of_teacher_grid_data',
                tools: ['city', 'country', 'town', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__city__name', 'class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'teacher_num', 'teaching_teacher_num', 'cha', 'rate'],
                headers: ['市', '县/区', '乡/镇', '学校', '登记教师总数（人）', '授课教师人数（人）', '人数差', '授课教师占登记教师比例（%）']
            }, {
                title: '按县/区统计',
                apiKey: 'statistic_number_of_teacher_grid_data',
                tools: ['city', 'country', 'town', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'teacher_num', 'teaching_teacher_num', 'cha', 'rate'],
                headers: ['县/区', '乡/镇', '学校', '登记教师总数（人）', '授课教师人数（人）', '人数差', '授课教师占登记教师比例（%）']
            }, {
                title: '按乡/镇统计',
                apiKey: 'statistic_number_of_teacher_grid_data',
                tools: ['city', 'country', 'town', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__town__name', 'class_and_grade__school__name', 'teacher_num', 'teaching_teacher_num', 'cha', 'rate'],
                headers: ['乡/镇', '学校', '登记教师总数（人）', '授课教师人数（人）', '人数差', '授课教师占登记教师比例（%）']
            }, {
                title: '按学校统计',
                apiKey: 'statistic_number_of_teacher_grid_data',
                tools: ['city', 'country', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__school__name', 'teacher_num', 'teaching_teacher_num', 'cha', 'rate'],
                headers: ['学校', '登记教师总数（人）', '授课教师人数（人）', '人数差', '授课教师占登记教师比例（%）']
            }],
            chart: [{
                x: 'townName',
                y: ['regTotal', 'teachTotal'],
                tools: ['city', 'country', 'town', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['townName', 'regTotal', 'teachTotal'],
                status: '登记教师的总和: {regTotalCount}、授课教师的总和: {teachTotalCount}'
            }, {
                x: 'schoolName',
                y: ['regTotal', 'teachTotal'],
                tools: ['city', 'country', 'town', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['schoolName', 'regTotal', 'teachTotal'],
                status: '登记教师的总和: {regTotalCount}、授课教师的总和: {teachTotalCount}'
            }]
        },
        teach: {
            grid: [{
                title: '按市统计',
                apiKey: 'statistic_lesson_by_lesson_name_and_teacher',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__city__name', 'class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'scheduled_num', 'real_finished_num'],
                headers: ['市', '县/区', '乡/镇', '学校', '计划授课次数', '实际授课次数'],
            }, {
                title: '按县/区统计',
                apiKey: 'statistic_lesson_by_lesson_name_and_teacher',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'scheduled_num', 'real_finished_num'],
                headers: ['县/区', '乡/镇', '学校', '计划授课次数', '实际授课次数'],
                status: '{level}当前授课总次数：{count}'
            }, {
                title: '按乡镇统计',
                apiKey: 'statistic_lesson_by_lesson_name_and_teacher',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__town__name', 'class_and_grade__school__name', 'scheduled_num', 'real_finished_num'],
                headers: ['乡/镇', '学校', '计划授课次数', '实际授课次数'],
                status: '{level}当前授课总次数：{count}'
            }, {
                title: '按学校统计',
                apiKey: 'statistic_lesson_by_lesson_name_and_teacher',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__school__name', 'scheduled_num', 'real_finished_num'],
                headers: ['学校', '计划授课次数', '实际授课次数'],
                status: '{level}当前授课总次数：{count}'
            }],
            chart: [{
                x: 'cityName',
                y: ['regTotal', 'teachTotal'],
                tools: ['city', 'qdate', 'date', 'query'],
                fields: ['cityName', 'regTotal', 'teachTotal'],
                status: '登记教师的总和: {regTotalCount}、授课教师的总和: {teachTotalCount}'
            }, {
                x: 'countyName',
                y: ['regTotal', 'teachTotal'],
                tools: ['city', 'qdate', 'date', 'query'],
                fields: ['countyName', 'regTotal', 'teachTotal'],
                status: '登记教师的总和: {regTotalCount}、授课教师的总和: {teachTotalCount}'
            }]
        },
        //授课次数统计
        teachCount: {
            title: '教师授课次数统计',
            grid: [{
                title: '按市统计',
                apiKey: 'statistic_lesson_by_school',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['县/区', '乡/镇', '学校', '计划课时', '完成课时', '剩余课时', '课时完成率'],
                status: '{level}的登记教师总数: {regTotal}、授课教师人数: {teachTotal}、人均授课节次: {aver}、授课教师占登记教师比例: {rate}'
            }, {
                title: '按县/区统计',
                apiKey: 'statistic_lesson_by_school',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['县/区', '乡/镇', '学校', '计划课时', '完成课时', '剩余课时', '课时完成率'],
                status: '{level}的登记教师总数: {regTotal}、授课教师人数: {teachTotal}、人均授课节次: {aver}、授课教师占登记教师比例: {rate}'
            }, {
                title: '按乡镇统计',
                apiKey: 'statistic_lesson_by_school',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__town__name', 'class_and_grade__school__name', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['乡/镇', '学校', '计划课时', '完成课时', '剩余课时', '课时完成率'],
                status: '{level}的登记教师总数: {regTotal}、授课教师人数: {teachTotal}、人均授课节次: {aver}、授课教师占登记教师比例: {rate}'
            }, {
                title: '按学校统计',
                apiKey: 'statistic_lesson_by_school',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                fields: ['class_and_grade__school__name', 'scheduled_num', 'real_finished_num', 'unfinished_num', 'finish_rate'],
                headers: ['学校', '计划课时', '完成课时', '剩余课时', '课时完成率'],
                status: '{level}的登记教师总数: {regTotal}、授课教师人数: {teachTotal}、人均授课节次: {aver}、授课教师占登记教师比例: {rate}'
            }]
        },
        resource: {
            title: '资源使用统计',
            grid: [{
                title: '按市统计',
                apiKey: 'statistic_resource_by_grade',
                tools: ['city', 'country', 'town', 'school', 'query'],
                headers: ['市', '县/区', '乡/镇', '学校', '资源类型', '访问次数'],
                fields: ['class_and_grade__city__name', 'class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'resource_using_histories__resource_name', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title: '按县/区统计',
                apiKey: 'statistic_resource_by_grade',
                tools: ['city', 'country', 'town', 'school', 'query'],
                headers: ['县/区', '乡/镇', '学校', '资源类型', '访问次数'],
                fields: ['class_and_grade__country__name', 'class_and_grade__town__name', 'class_and_grade__school__name', 'resource_using_histories__resource_name', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title: '按乡/镇统计',
                apiKey: 'statistic_resource_by_grade',
                tools: ['city', 'country', 'town', 'school', 'query'],
                headers: ['乡/镇', '学校', '资源类型', '访问次数'],
                fields: ['class_and_grade__town__name', 'class_and_grade__school__name', 'resource_using_histories__resource_name', 'number'],
                status: '{level}资源访问总次数：{count}'
            }, {
                title: '按学校统计',
                apiKey: 'statistic_resource_by_school',
                tools: ['city', 'country', 'town', 'school', 'query'],
                headers: ['学校', '资源类型', '访问次数'],
                fields: ['class_and_grade__school__name', 'resource_using_histories__resource_name', 'number'],
                status: '{level}资源访问总次数：{count}'
            }],
            chart: [{
                x: 'mediaType',
                y: 'useTimes',
                xtitle: '资源类型',
                ytitle: '访问次数',
                tools: ['stattype1'],
                fields: ['mediaType', 'useTimes']
            }, {
                x: 'course',
                y: 'useTimes',
                xtitle: '科目',
                ytitle: '访问次数',
                tools: ['stattype1'],
                fields: ['course', 'useTimes']
            }]
        },
        login: {
            /*grid: [{
                title: '按市统计',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                headers: ['编号', '学校名称', '登录次数'],
                fields: ['id', 'cityName', 'schoolName', 'date', 'useTimes'],
                status: ''
            }, {
                title: '按县/区统计',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                headers: ['编号', '学校名称', '登录次数'],
                fields: ['id', 'cityName', 'schoolName', 'date', 'useTimes'],
                status: ''
            }, {
                title: '按乡/镇统计',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                headers: ['编号', '学校名称', '登录次数'],
                fields: ['id', 'cityName', 'schoolName', 'date', 'useTimes'],
                status: ''
            }{
                title: '按学校统计',
                tools: ['city', 'county', 'town', 'school', 'qdate', 'startDate', 'endDate', 'query'],
                headers: ['编号', '学校名称', '登录次数'],
                fields: ['id', 'cityName', 'schoolName', 'date', 'useTimes'],
                status: ''
            }],*/
            chart: [{
                x: 'cityName',
                y: 'useTimes',
                tools: ['qdate', 'date', 'stattype5', 'query'],  //stattype5 [市，省直学校，学校]
                fields: ['useTimes', 'cityName']
            }, {
                x: 'schoolName',
                y: 'useTimes',
                tools: ['qdate', 'date', 'stattype5', 'query'],
                fields: ['useTimes', 'schoolName']
            }, {
                x: 'grade',
                y: 'useTimes',
                tools: ['qdate', 'date', 'stattype5', 'query'],
                fields: ['useTimes', 'grade']
            }]
        },
        unlogin: {
            grid: [{
                "apiKey": "statistic_teacher_not_using_by_school",
                "tools": [
                    "city",
                    "country",
                    "town",
                    "school",
                    "qdate",
                    "startDate",
                    "endDate",
                    "query"
                ],
                "headers": [
                    "市",
                    "县/区",
                    "乡/镇",
                    "学校",
                    "未登录次数"
                ],
                "fields": [
                    "class_and_grade__city__name",
                    "class_and_grade__country__name",
                    "class_and_grade__town__name",
                    "class_and_grade__school__name",
                    "number"
                ],
                "title": "按市统计"
            }, {
                "apiKey": "statistic_teacher_not_using_by_school",
                "tools": [
                    "country",
                    "town",
                    "school",
                    "qdate",
                    "startDate",
                    "endDate",
                    "query"
                ],
                "headers": [
                    "县/区",
                    "乡/镇",
                    "学校",
                    "未登录次数"
                ],
                "fields": [
                    "class_and_grade__country__name",
                    "class_and_grade__town__name",
                    "class_and_grade__school__name",
                    "number"
                ],
                "title": "按县/区统计"
            }, {
                "apiKey": "statistic_teacher_not_using_by_school",
                "tools": [
                    "town",
                    "school",
                    "qdate",
                    "startDate",
                    "endDate",
                    "query"
                ],
                "headers": [
                    "乡/镇",
                    "学校",
                    "未登录次数"
                ],
                "fields": [
                    "class_and_grade__town__name",
                    "class_and_grade__school__name",
                    "number"
                ],
                "title": "按乡/镇统计"
            }, {
                "apiKey": "statistic_teacher_not_using_by_school",
                "tools": [
                    "school",
                    "qdate",
                    "startDate",
                    "endDate",
                    "query"
                ],
                "headers": [
                    "学校",
                    "未登录次数"
                ],
                "fields": [
                    "class_and_grade__school__name",
                    "number"
                ],
                "title": "按学校统计"
            }],
            chart: [{
                x: 'cityName',
                y: 'useTimes',
                tools: ['qdate', 'date', 'stattype5', 'query'],  //stattype5 [市，省直学校，学校]
                fields: ['useTimes', 'cityName']
            }, {
                x: 'schoolName',
                y: 'useTimes',
                tools: ['qdate', 'date', 'stattype5', 'query'],
                fields: ['useTimes', 'schoolName']
            }, {
                x: 'grade',
                y: 'useTimes',
                tools: ['qdate', 'date', 'stattype5', 'query'],
                fields: ['useTimes', 'grade']
            }]
        }
    }
});