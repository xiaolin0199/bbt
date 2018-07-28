/**
 * 班班通校级管理配置
 * grid 模板：
 * {
 *   title: '',//
 * }
 */
var bbtConfig = bbtConfig || {};
Ext.apply(bbtConfig, {
    template: {
        grid: {
            title: '',//字符串 - 要显示的表格的标题
            url: '',//字符串 - 要显示的表格的数据源
            tools: null, //数组 - 要显示的表格的过滤条件，条件名参见 app.js 公用工具集合
            pagination: null, //or false是否启用分页
            status: '', //字符串 - 要显示的表格右下角的消息文本
            statusRender: function (template, paginationbar, store) {}, //格式化 status 的函数
            columns: null,//
            sorters: null, //
            enableSummary: false//是否启用汇总
        }
    },
    colorblocks: ['facca8', '98d0dd', 'd2c9de', 'cadaa9', 'eccdcb', 'c9d6e6'],
    getRate: function(op1, op2){
        if(typeof op1 != "number") { op1 = 0; }
        if(typeof op2 != "number") { op2 = 0; }
        if(op2 === 0) {
            return '0.00%';
        } else {
            return (100.0*op1/op2).toFixed(2) + '%';
        }
    },
    humanReadTime: function(v){
        var d, h, m, str = '';
        d = Math.floor(v / 1440);
        h = Math.floor(v % 1440 / 60);
        m = v % 60;
        if(d !== 0) {
            str += d + "天";
        }
        if(h !== 0) {
            str += h + "小时";
        }
        if(m !== 0) {
            str += m + "分钟";
        }
        return str;
    },
    bbtUsageLog: {
        login: {
            title: '教师授课 > 学校终端登录日志',
            grid: [{
                title: '班班通终端',
                url: '/activity/logged-in/',
                tools: ['qdate', 'startDate', 'endDate', 'grade', 'class', 'jieci', 'course', 'iTeacherName', 'query'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师姓名',
                    dataIndex: 'teacher_name'
                }, {
                    text: '节次',
                    dataIndex: 'lesson_period_sequence',
                    width: 50
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '登录时间',
                    width: 155,
                    dataIndex: 'created_at'
                }, {
                    text: '使用时长（分钟）',
                    dataIndex: 'time_used',
                    renderer: function(v,m,r){
                        var msg = '<span style="color: green;">正在上课</span>';
                        if(r.get('teacherlogintimetemp') != null) {
                            return msg;
                        }
                        if(typeof v == "number") {
                            return Math.floor(v/60);
                        }
                    },
                    flex: 1
                }],
                statusTemplate: '合计：登录日志总数{count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            count: store.proxy.reader.rawData.data.total
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }, {
                title: '电脑教室终端',
                url: '/activity/logged-in/computer-class/',
                tools: ['qdate', 'startDate', 'endDate', 'computerclass', 'jieci', 'course', 'iTeacherName', 'query'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '电脑教室',
                    dataIndex: 'computerclass',
                    renderer: function(v){ return v;}
                }, {
                    text: '教师姓名',
                    dataIndex: 'teacher_name'
                }, {
                    text: '节次',
                    dataIndex: 'lesson_period_sequence',
                    width: 50
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '登录时间',
                    width: 155,
                    dataIndex: 'created_at'
                }, {
                    text: '使用时长（分钟）',
                    dataIndex: 'time_used',
                    renderer: function(v,m,r){
                        var msg = '<span style="color: green;">正在上课</span>';
                        if(r.get('teacherlogintimetemp') != null) {
                            return msg;
                        }
                        if(typeof v == "number") {
                            return Math.floor(v/60);
                        }
                    },
                    flex: 1
                }],
                statusTemplate: '合计：登录日志总数{count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            count: store.proxy.reader.rawData.data.total
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }]
        },
        unlogin: {
            grid: {
                title: '使用记录 > 班班通未登录日志',
                url: '/activity/not-logged-in/',
                tools: ['qdate', 'startDate', 'endDate', 'grade', 'class', 'jieci', 'course', 'iTeacherName', 'query'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师姓名',
                    dataIndex: 'teacher_name'
                }, {
                    text: '节次',
                    dataIndex: 'lesson_period_sequence',
                    width: 50
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '未登录时间',
                    width: 155,
                    dataIndex: 'created_at',
                    flex: 1
                }],
                pagination: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }
        }
    },
    //班班通分析统计
    bbtAnalyzeStatic: {
        //授课次数比例统计
        teachCount: {
            title: '教师授课 > 班班通授课次数统计',
            grid: [{
                title: '按班级统计',
                url: '/statistic/teaching-time/by-class/',
                exportUrl: '/statistic/teaching-time/by-class/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'grade', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '实际授课总数',
                    dataIndex: 'finished_time'
                }, {
                    text: '计划达标授课总数（学期）',
                    width: 150,
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v, m, r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }],
                pagination: true,
                statusTemplate: '合计:实际授课总数{finished_time}、计划达标授课总数{schedule_time}、授课达标占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = data.schedule_time ? data.finished_time / data.schedule_time : 0;
                        data = Ext.merge({rate: (100*rate).toFixed(2)+'%'}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按班级教师课程统计',
                url: '/statistic/teaching-time/by-lessonteacher/',
                exportUrl: '/statistic/teaching-time/by-lessonteacher/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['grade', 'class', 'course', 'iTeacherName', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '实际授课总数',
                    dataIndex: 'finished_time'
                }, {
                    text: '计划达标授课总数（学期）',
                    width: 150,
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v, m, r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }],
                pagination: true,
                statusTemplate: '合计:实际授课总数{finished_time}、计划达标授课总数{schedule_time}、授课达标占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = data.schedule_time ? data.finished_time / data.schedule_time : 0;
                        data = Ext.merge({rate: (100*rate).toFixed(2)+'%'}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按教师统计',
                url: '/statistic/teaching-time/by-teacher/',
                exportUrl: '/statistic/teaching-time/by-teacher/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'iTeacherName', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '实际授课总数',
                    dataIndex: 'finished_time'
                }, {
                    text: '计划达标授课总数（学期）',
                    width: 150,
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v, m, r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }],
                pagination: true,
                statusTemplate: '合计:实际授课总数{finished_time}、计划达标授课总数{schedule_time}、授课达标占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = data.schedule_time ? data.finished_time / data.schedule_time : 0;
                        data = Ext.merge({rate: (100*rate).toFixed(2)+'%'}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }]
        },
        //班班通授课时长统计
        timeUsedCount: {
            title: '教师授课 > 班班通授课时长统计',
            grid: [{
                title: '按班级统计',
                url: '/statistic/time-used/by-class/',
                exportUrl: '/statistic/time-used/by-class/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'grade', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '授课节次总数',
                    dataIndex: 'lesson_count',
                    width: 140
                }, {
                    text: '平均时长/节次（分钟）',
                    width: 135,
                    dataIndex: 'xxx',
                    renderer: function(v, m, r){
                        var time = r.get('total_time_used') || 0,
                            count = r.get('lesson_count');
                        time = time / 60;
                        if(!count) { return '0.00'; }
                        else {
                            return (time / count).toFixed(2);
                        }
                    }
                }, {
                    text: '总授课时长（分钟）',
                    width: 150,
                    flex: 1,
                    dataIndex: 'total_time_used',
                    renderer: function(v){
                        return (v ? (v/60).toFixed(2) : '0.00');
                    }
                }],
                statusTemplate: '合计：实际授课总时长 {total_time_used} 分钟',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_time_used: (store.proxy.reader.rawData.data.total_time_used/60).toFixed(2)
                        };
                       return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true
            }, {
                title: '按班级教师课程统计',
                url: '/statistic/time-used/by-lessonteacher/',
                exportUrl: '/statistic/time-used/by-lessonteacher/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'class', 'course', 'iTeacherName', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '授课节次总数',
                    dataIndex: 'lesson_count',
                    width: 140
                }, {
                    text: '平均时长/节次（分钟）',
                    dataIndex: 'xxx',
                    width: 135,
                    renderer: function(v, m, r){
                        var time = r.get('total_time_used') || 0,
                            count = r.get('lesson_count');
                        time = time / 60;
                        if(!count) { return '0.00'; }
                        else {
                            return (time / count).toFixed(2);
                        }
                    }
                }, {
                    text: '总授课时长（分钟）',
                    width: 150,
                    flex: 1,
                    dataIndex: 'total_time_used',
                    renderer: function(v){
                        return (v ? (v/60).toFixed(2) : '0.00');
                    }
                }],
                statusTemplate: '合计：实际授课总时长 {total_time_used} 分钟',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_time_used: (store.proxy.reader.rawData.data.total_time_used/60).toFixed(2)
                        };
                       return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }, {
                title: '按教师统计',
                url: '/statistic/time-used/by-teacher/',
                exportUrl: '/statistic/time-used/by-teacher/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'iTeacherName', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '授课节次总数',
                    dataIndex: 'lesson_count',
                    width: 140
                }, {
                    text: '平均时长/节次（分钟）',
                    dataIndex: 'xxx',
                    width: 135,
                    renderer: function(v, m, r){
                        var time = r.get('total_time_used') || 0,
                            count = r.get('lesson_count');
                        time = time / 60;
                        if(!count) { return '0.00'; }
                        else {
                            return (time / count).toFixed(2);
                        }
                    }
                }, {
                    text: '总授课时长（分钟）',
                    width: 150,
                    flex: 1,
                    dataIndex: 'total_time_used',
                    renderer: function(v){
                        return (v ? (v/60).toFixed(2) : '0.00');
                    }
                }],
                statusTemplate: '合计：实际授课总时长 {total_time_used} 分钟',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_time_used: (store.proxy.reader.rawData.data.total_time_used/60).toFixed(2)
                        };
                       return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true
            }]
        },
        //授课人数比例统计
        teacherNumber: {
            title: '教师授课 > 班班通授课人数统计',
            grid: [{
                title: '按课程年级统计',
                url: '/statistic/teacher-active/by-lessongrade/',
                exportUrl: '/statistic/teacher-active/by-lessongrade/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'grade', 'course', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';},
                    summaryRenderer: function(){
                        return '合计：';
                    }
                }, {
                    text: '授课教师总数',
                    dataIndex: 'active_teachers'
                }, {
                    text: '登记教师总数',
                    dataIndex: 'total_teachers'
                }, {
                    text: '授课占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('active_teachers'), r.get('total_teachers')); }
                }],
                statusTemplate: '合计：授课教师总数{active_teachers}、登记教师总数{total_teachers}、授课占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            total_teachers: 0,
                            active_teachers: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.active_teachers, data.total_teachers);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }, {
                title: '按课程统计',
                url: '/statistic/teacher-active/by-lesson/',
                exportUrl: '/statistic/teacher-active/by-lesson/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name',
                    summaryRenderer: function(){
                        return '合计：';
                    }
                }, {
                    text: '授课教师总数',
                    dataIndex: 'active_teachers'
                }, {
                    text: '登记教师总数',
                    dataIndex: 'total_teachers'
                }, {
                    text: '授课占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('active_teachers'), r.get('total_teachers')); }
                }],
                statusTemplate: '合计：授课教师总数{active_teachers}、登记教师总数{total_teachers}、授课占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            total_teachers: 0,
                            active_teachers: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.active_teachers, data.total_teachers);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }, {
                title: '按年级统计',
                url: '/statistic/teacher-active/by-grade/',
                exportUrl: '/statistic/teacher-active/by-grade/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';},
                    summaryRenderer: function(){
                        return '合计：';
                    }
                }, {
                    text: '授课教师总数',
                    dataIndex: 'active_teachers'
                }, {
                    text: '登记教师总数',
                    dataIndex: 'total_teachers'
                }, {
                    text: '授课占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('active_teachers'), r.get('total_teachers')); }
                }],
                statusTemplate: '合计：授课教师总数{active_teachers}、登记教师总数{total_teachers}、授课占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            total_teachers: 0,
                            active_teachers: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.active_teachers, data.total_teachers);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }]
        },
        //教师未登录班班通统计
        unlogin: {
            title: '教师授课 > 班班通未登录统计',
            grid: [{
                title: '按课程年级统计',
                url: '/statistic/teacher-absent/by-lessongrade/',
                exportUrl: '/statistic/teacher-absent/by-lessongrade/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'grade', 'course', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '未登录教师总数',
                    dataIndex: 'absent_teachers'
                }, {
                    text: '登记教师总数',
                    dataIndex: 'total_teachers'
                }, {
                    text: '未授课占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('absent_teachers'), r.get('total_teachers')); }
                }],
                statusTemplate: '合计：未登录教师总数{absent_teachers}、登记教师总数{total_teachers}、未授课占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            absent_teachers: 0,
                            total_teachers: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = data.total_teachers === 0 ? 0 : data.absent_teachers / data.total_teachers;
                        data = Ext.merge({rate: (100*rate).toFixed(2)+'%'}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }, {
                title: '按课程统计',
                url: '/statistic/teacher-absent/by-lesson/',
                exportUrl: '/statistic/teacher-absent/by-lesson/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '未登录教师总数',
                    dataIndex: 'absent_teachers'
                }, {
                    text: '登记教师总数',
                    dataIndex: 'total_teachers'
                }, {
                    text: '未授课占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('absent_teachers'), r.get('total_teachers')); }
                }],
                statusTemplate: '合计：未登录教师总数{absent_teachers}、登记教师总数{total_teachers}、未授课占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            absent_teachers: 0,
                            total_teachers: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = data.total_teachers === 0 ? 0 : data.absent_teachers / data.total_teachers;
                        data = Ext.merge({rate: (100*rate).toFixed(2)+'%'}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }, {
                title: '按年级统计',
                url: '/statistic/teacher-absent/by-grade/',
                exportUrl: '/statistic/teacher-absent/by-grade/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '未登录教师总数',
                    dataIndex: 'absent_teachers'
                }, {
                    text: '登记教师总数',
                    dataIndex: 'total_teachers'
                }, {
                    text: '未授课占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('absent_teachers'), r.get('total_teachers')); }
                }],
                statusTemplate: '合计：未登录教师总数{absent_teachers}、登记教师总数{total_teachers}、未授课占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            absent_teachers: 0,
                            total_teachers: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = data.total_teachers === 0 ? 0 : data.absent_teachers / data.total_teachers;
                        data = Ext.merge({rate: (100*rate).toFixed(2)+'%'}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true,
                query: {
                    '_': '7',
                    start_date: function(){ var d = new Date(); d.setDate(d.getDate()-7); return d; },
                    end_date: function(){ return new Date(); }
                }
            }]
        },
        //授课资源使用统计
        resource: {
            title: '教师授课 > 班班通资源使用统计',
            grid: [{
                title: '按资源来源统计',
                url: '/statistic/resource/resource-from/',
                exportUrl: '/statistic/resource/resource-from/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['resourceFrom', 'grade', 'class', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : '';}
                }, {
                    text: '资源来源',
                    dataIndex: 'resource_from'
                }, {
                    text: '访问次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '访问次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：访问次数{visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            visit_count: store.proxy.reader.rawData.data.total.visit_count
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        return bbtConfig.tmpl(template, {visit_count:0}, 0);
                    }
                }
            }, {
                title: '按资源类型统计',
                url: '/statistic/resource/resource-type/',
                exportUrl: '/statistic/resource/resource-type/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['resourceType', 'grade', 'class', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : '';}
                }, {
                    text: '资源类型',
                    dataIndex: 'resource_type'
                }, {
                    text: '访问次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '访问次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：访问次数{visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            visit_count: store.proxy.reader.rawData.data.total.visit_count
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        return bbtConfig.tmpl(template, {visit_count:0}, 0);
                    }
                }
            }, {
                title: '按教师统计',
                url: '/statistic/resource/teacher/',
                exportUrl: '/statistic/resource/teacher/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'iTeacherName', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '访问次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '访问次数占比（%）',
                    width: 120,
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：访问次数{visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            visit_count: store.proxy.reader.rawData.data.total.visit_count
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        return bbtConfig.tmpl(template, {visit_count:0}, 0);
                    }
                }
            }, {
                title : '按课程统计',
                url: '/statistic/resource/lesson/',
                exportUrl: '/statistic/resource/lesson/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '访问次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '访问次数占比（%）',
                    width: 120,
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：访问次数{visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            visit_count: store.proxy.reader.rawData.data.total.visit_count
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        return bbtConfig.tmpl(template, {visit_count:0}, 0);
                    }
                }
            }]
        },
        //申报记录查询
        assetlist: {
            grid: {
                title: '资产管理 > 资产申报记录查询',
                url: '/asset/asset-log/',
                exportUrl: '/asset/asset-log/export/',
                columns: [{
                    text: '申报时间',
                    dataIndex: 'reported_at',
                    width: 150
                }, {
                    text: '申报类型',
                    width: 60,
                    dataIndex: 'log_type'
                }, {
                    text: '资产类型',
                    dataIndex: 'asset_type__name'
                }, {
                    text: '设备型号',
                    dataIndex: 'device_model'
                }, {
                    text: '数量',
                    width: 50,
                    dataIndex: 'number'
                }, {
                    text: '资产来源',
                    dataIndex: 'asset_from'
                }, {
                    text: '申报用户',
                    width: 60,
                    dataIndex: 'reported_by'
                }, {
                    text: '备注',
                    dataIndex: 'remark',
                    flex: 1
                }],
                tools: [['qdate', 'startDate', 'endDate', 'assetReportType', 'assetType'], ['iDeviceModel', 'assetFrom', 'report_user', 'remark', 'query', '->', 'export']],
                pagination: true,
                query: {
                    '_': '7'
                }
            }
        },
        //资产维修管理
        assetrepairhistosy: {
            grid: {
                title: '资产管理 > 资产维修管理',
                url: '/asset/asset-repair/',
                exportUrl: '/asset/asset-repair/export/',
                columns: [{
                    text: '报修时间',
                    dataIndex: 'reported_at',
                    width: 150
                }, {
                    text: '资产类型',
                    dataIndex: 'asset_type__name'
                }, {
                    text: '设备型号',
                    dataIndex: 'device_model'
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v == '电脑教室' ? v : (v ? v + '年级' : '');}
                }, {
                    text: '班级',
                    dataIndex: 'class_name',
                    renderer: function(v){ return v ? v + '班' : ''; }
                }, /* TODO remove this comment on next dev iteration
                {
                    text: '所属位置',
                    dataIndex: 'fdasfd'
                }, */{
                    text: '申报用户',
                    width: 60,
                    dataIndex: 'reported_by'
                }, {
                    text: '备注',
                    dataIndex: 'remark',
                    flex: 1
                }],
                tools: [['qdate', 'startDate', 'endDate', 'assetType', 'iDeviceModel'], [{tool: 'gradeOld', computerclass: true}, 'classOld', 'report_user',/* 'assetPos', */'remark', 'query', '->', 'export', 'faketb', 'asset_repair']],
                pagination: true,
                query: {
                    '_': '7'
                }
            }
        }
    },
    //资源使用
    bbtResourceStatic: {
        resourceFrom: {
            title: '资源使用 > 资源来源使用统计',
            grid: [{
                title: '按班级统计',
                url: '/statistic/resource-from/class/',
                exportUrl: '/statistic/resource-from/class/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'resourceFrom', 'grade', 'class', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name'
                }, {
                    text: '班级',
                    dataIndex: 'class_name'
                }, {
                    text: '资源来源',
                    dataIndex: 'resource_from'
                }, {
                    text: '使用次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '使用次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：使用次数: {visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            visit_count: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按课程统计',
                url: '/statistic/resource-from/lesson/',
                exportUrl: '/statistic/resource-from/lesson/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'resourceFrom', 'course', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '资源来源',
                    dataIndex: 'resource_from'
                }, {
                    text: '使用次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '使用次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：使用次数: {visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            visit_count: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按教师统计',
                url: '/statistic/resource-from/teacher/',
                exportUrl: '/statistic/resource-from/teacher/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'resourceFrom', 'iTeacherName', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '资源来源',
                    dataIndex: 'resource_from'
                }, {
                    text: '使用次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '使用次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：使用次数: {visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            visit_count: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }]
        },
        resourceType: {
            title: '资源使用 > 资源类型使用统计',
            grid: [{
                title: '按班级统计',
                url: '/statistic/resource-type/class/',
                exportUrl: '/statistic/resource-type/class/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'resourceType', 'grade', 'class', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '年级',
                    dataIndex: 'grade_name'
                }, {
                    text: '班级',
                    dataIndex: 'class_name'
                }, {
                    text: '资源类型',
                    dataIndex: 'resource_type'
                }, {
                    text: '使用次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '使用次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：使用次数: {visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            visit_count: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按课程统计',
                url: '/statistic/resource-type/lesson/',
                exportUrl: '/statistic/resource-type/lesson/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'resourceType', 'course', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '课程',
                    dataIndex: 'lesson_name'
                }, {
                    text: '资源类型',
                    dataIndex: 'resource_type'
                }, {
                    text: '使用次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '使用次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：使用次数: {visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            visit_count: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按教师统计',
                url: '/statistic/resource-type/teacher/',
                exportUrl: '/statistic/resource-type/teacher/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'resourceType', 'iTeacherName', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '教师',
                    dataIndex: 'teacher_name'
                }, {
                    text: '资源类型',
                    dataIndex: 'resource_type'
                }, {
                    text: '使用次数',
                    dataIndex: 'visit_count'
                }, {
                    text: '使用次数占比（%）',
                    width: 120,
                    flex: 1,
                    dataIndex: '_',
                    renderer: function(v,m,r){ try{ var c=100*r.get('visit_count')/r.store.proxy.reader.rawData.data.total.visit_count; return c.toFixed(2)+'%'; }catch(e){ return '0%'; }}
                }],
                pagination: true,
                statusTemplate: '合计：使用次数: {visit_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            visit_count: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }]
        }
    },
    //终端开机使用统计
    bbtMachineStatic: {
        title: '资产管理 > 学校终端开机统计',
        grid: [{
            title: '按学校年级统计',
            url: '/terminal/time-used/by-grade/',
            exportUrl: '/terminal/time-used/by-grade/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'/*, {tool:'gradeOld',byTerm: true,computerclass:true}*/, 'query', '->', 'export'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '学校',
                dataIndex: 'school_name',
                width: 160
            }, {
                text: '年级',
                dataIndex: 'grade_name'
            }, {
                text: '班级总数',
                dataIndex: 'class_count'
            }, {
                text: '日平均开机时长（分钟）',
                width: 160,
                dataIndex: 'use_time_average'
            }, {
                text: '日平均开机次数',
                dataIndex: 'use_count_average'
            }, {
                text: '开机总时长',
                dataIndex: 'use_time_total',
                width: 140,
                renderer: function(v){
                    return bbtConfig.humanReadTime(v);
                }
            }, {
                text: '开机总次数',
                dataIndex: 'use_count_total'
            }],
            pagination: true,
            statusTemplate: '合计：开机总时长{use_time_total}, 开机总次数{use_count_total}',
            statusRender: function(template, paginationbar, store) {
                try {
                    var data = Ext.merge({
                        use_time_total: 0,
                        use_count_total: 0
                    }, store.proxy.reader.rawData.data.total);
                    data.use_time_total = bbtConfig.humanReadTime(data.use_time_total);
                    return bbtConfig.tmpl(template, data, 0);
                } catch (e) {
                    ;
                }
            },
            listeners: {
                afterrender: function(){
                    var term = this.down('combo[name=term_type]');
                    term.on('change', function(me, v){
                        var g = me.ownerCt.down('[name=grade_name]');
                        if(g && g.byTerm) {
                            //g.store.load();
                        }
                    });
                }
            }
        }, {
            title: '按班级统计',
            url: '/terminal/time-used/by-class/',
            exportUrl: '/terminal/time-used/by-class/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', {tool: 'grade', computerclass: true}, 'query', '->', 'export'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '学校',
                dataIndex: 'school_name',
                width: 160
            }, {
                text: '年级',
                dataIndex: 'grade_name'
            }, {
                text: '班级',
                dataIndex: 'class_name'
            }, {
                text: '日平均开机时长（分钟）',
                width: 160,
                dataIndex: 'use_time_average'
            }, {
                text: '日平均开机次数',
                dataIndex: 'use_count_average'
            }, {
                text: '开机总时长',
                dataIndex: 'use_time_total',
                width: 140,
                renderer: function(v){
                    return bbtConfig.humanReadTime(v);
                }
            }, {
                text: '开机总次数',
                dataIndex: 'use_count_total'
            }],
            pagination: true,
            statusTemplate: '合计：开机总时长{use_time_total}, 开机总次数{use_count_total}',
            statusRender: function(template, paginationbar, store) {
                try {
                    var data = Ext.merge({
                        use_time_total: 0,
                        use_count_total: 0
                    }, store.proxy.reader.rawData.data.total);
                    data.use_time_total = bbtConfig.humanReadTime(data.use_time_total);
                    return bbtConfig.tmpl(template, data, 0);
                } catch (e) {
                    ;
                }
            }
        }]
    },
    //终端开机使用日志
    bbtMachineLog: {
        grid: {
            title: '资产管理 > 终端开机日志',
            url: '/terminal/time-used/log/',
            exportUrl: '/terminal/time-used/log/export/',
            tools: ['qdate', 'startDate', 'endDate', {tool:'grade',computerclass:true}, 'class', 'query'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '学校',
                dataIndex: 'school_name',
                width: 160
            }, {
                text: '年级',
                dataIndex: 'grade_name'
            }, {
                text: '班级',
                dataIndex: 'class_name'
            }, {
                text: '使用日期',
                dataIndex: 'create_time',
                width: 140
            }, {
                text: '开机时长',
                width: 160,
                dataIndex: 'use_time',
                renderer: function(v){
                    return bbtConfig.humanReadTime(v);
                }
            }, {
                text: '开机次数',
                dataIndex: 'use_count'
            }],
            pagination: true,
            statusTemplate: '合计：开机总时长{use_time_total}, 开机总次数{use_count_total}',
            statusRender: function(template, paginationbar, store) {
                try {
                    var data = Ext.merge({
                        use_time_total: 0,
                        use_count_total: 0
                    }, store.proxy.reader.rawData.data.total);
                    data.use_time_total = bbtConfig.humanReadTime(data.use_time_total);
                    return bbtConfig.tmpl(template, data, 0);
                } catch (e) {
                    ;
                }
            }
        }
    }
});
