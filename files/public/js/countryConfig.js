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
    averageTeach: function(class_total, finished_time){
        var v = 0;
        try {
            v = finished_time / class_total;
        } catch (e) {
            v = 0;
        }
        return v.toFixed(1);
    },
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
        if(!v) { return '0分钟'; }
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
    humanReadSize: function(size){
        var unit, tmp;
        if(typeof size != "number") {
            size = 0;
        }
        if(size > 1073741824) {
            unit = 'TB';
            tmp = (size / 1073741824).toFixed(3);
        } else if(size > 1048576) {
            unit = 'GB';
            tmp = (size / 1048576).toFixed(3);
        } else if(size > 1024) {
            unit = 'MB';
            tmp = (size / 1024).toFixed(3);
        } else {
            unit = 'KB';
            tmp = size;
        }
        return tmp + unit;
    },
    bbtUsageLog: {
        login: {
            title: '教师授课 > 学校终端登录日志',
            grid: [{
                title: '班班通终端',
                url: '/activity/logged-in/',
                tools: [['qdate', 'startDate', 'endDate', 'town', 'school', 'grade', 'class'], ['jieci', 'course', 'iTeacherName', 'query']],
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
                tools: [['qdate', 'startDate', 'endDate', 'town', 'school', {tool: 'grade', computerclass: true, only_computerclass: true, fieldLabel: '电脑教室', labelWidth: 75, width: 145, _:{root: 'data.class'}}], ['jieci', 'course', 'iTeacherName', 'query']],
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
                    dataIndex: 'computerclass'
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
                tools: [['qdate', 'startDate', 'endDate', 'town', 'school', 'grade', 'class'], ['jieci', 'course', 'iTeacherName', 'query']],
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
        },
        eduunit: {
            grid: {
                title: '教师授课 > 教学点终端使用日志',
                url: '/edu-unit/terminal-use/details/',
                tools: ['qdate', 'startDate', 'endDate', 'eduTown', 'eduPoint', 'eduClassNo', 'query'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教学点',
                    dataIndex: 'point_name',
                    width: 160
                }, {
                    text: '教室终端编号',
                    dataIndex: 'number',
                    width: 160
                }, {
                    text: '使用日期',
                    dataIndex: 'date',
                }, {
                    text: '使用时长（分钟）',
                    width: 150,
                    dataIndex: 'use_time'
                }, {
                    text: '折合课时（45分钟/节）',
                    width: 180,
                    dataIndex: 'to_class_time',
                }, {
                    text: '开机时长（分钟）',
                    width: 120,
                    dataIndex: 'boot_time'
                }],
                pagination: true,
                statusTemplate: '合计：使用时长{use_time}、开机时长{boot_time}、折合课时{to_class_time}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            use_time: 0,
                            boot_time: 0,
                            to_class_time: 0
                        }, store.proxy.reader.rawData.data.total);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
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
                title: '按街道乡镇统计',
                url: '/statistic/teaching-time/by-town/',
                exportUrl: '/statistic/teaching-time/by-town/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 140
                }, {
                    text: '班级总数',
                    dataIndex: 'class_total'
                }, {
                    text: '班级平均授课数',
                    dataIndex: 'class_average',
                    width: 140
                }, {
                    text: '实际授课总数',
                    dataIndex: 'finished_time'
                }, {
                    text: '计划达标授课数/班级',
                    width: 140,
                    dataIndex: 'class_schedule_time'
                }, {
                    text: '计划达标授课总数（学期）',
                    width: 140,
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }, {
                    text:'学校达标率（%）',
                    dataIndex:'finished_rate_school',
                    flex:1,
                },{
                    text:'班级达标率（%）',
                    dataIndex:'finished_rate_class',
                    flex:1,
                }],
                statusTemplate: '合计：实际授课总数{finished_time}、计划达标授课总数（学期）{schedule_time}、授课达标占比{rate}、学校达标率{finished_rate_school} 、班级达标率{finished_rate_class}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.finished_time, data.schedule_time);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }, {
                title: '按学校统计',
                url: '/statistic/teaching-time/by-school/',
                exportUrl: '/statistic/teaching-time/by-school/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 140
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 140
                }, {
                    text: '班级总数',
                    dataIndex: 'class_total'
                }, {
                    text: '班级平均授课数',
                    dataIndex: 'class_average',
                    width: 140
                }, {
                    text: '实际授课总数',
                    dataIndex: 'finished_time'
                }, {
                    text: '计划达标授课数/班级',
                    width: 140,
                    dataIndex: 'class_schedule_time'
                },{
                    text: '计划达标授课总数（学期）',
                    width: 140,
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }, {
                    text:'班级达标率（%）',
                    dataIndex:'finished_rate_class',
                    flex:1
                }],
                statusTemplate: '合计：实际授课总数{finished_time}、计划达标授课总数（学期）{schedule_time}、授课达标占比{rate}、班级达标率{finished_rate_class}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.finished_time, data.schedule_time);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }, {
                title: '按学校年级统计',
                url: '/statistic/teaching-time/by-grade/',
                exportUrl: '/statistic/teaching-time/by-grade/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 140
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 140
                }, {
                    text: '年级',
                    dataIndex: 'grade_name',
                    renderer: function(v){ return v ? v + '年级' : '';}
                }, {
                    text: '班级总数',
                    dataIndex: 'class_total'
                }, {
                    text: '班级平均授课数',
                    dataIndex: 'class_average',
                    //width: 140
                }, {
                    text: '实际授课总数',
                    dataIndex: 'finished_time'
                }, {
                    text: '计划达标授课数/班级',
                    //width: 140,
                    dataIndex: 'class_schedule_time'
                }, {
                    text: '计划达标授课总数（学期）',
                    width: 140,
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                },{
                    text:'班级达标率（%）',
                    dataIndex:'finished_rate_class',
                    flex:1
                }],
                statusTemplate: '合计：实际授课总数{finished_time}、计划达标授课总数（学期）{schedule_time}、授课达标占比{rate}、班级达标率{finished_rate_class}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.finished_time, data.schedule_time);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }, {
                title: '按班级统计',
                url: '/statistic/teaching-time/by-class/',
                exportUrl: '/statistic/teaching-time/by-class/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'query', '->', 'export']],
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
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }],
                statusTemplate: '合计：实际授课总数{finished_time}、计划达标授课总数（学期）{schedule_time}、授课达标占比{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.finished_time, data.schedule_time);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }/*, {
                title: '按班级教师课程统计',
                url: '/statistic/teaching-time/by-lessonteacher/',
                exportUrl: '/statistic/teaching-time/by-lessonteacher/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'class', 'course', 'iTeacherName', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 140
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 140
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
                    dataIndex: 'schedule_time'
                }, {
                    text: '授课达标占比（%）',
                    dataIndex: '_',
                    flex: 1,
                    renderer: function(v,m,r){ return bbtConfig.getRate(r.get('finished_time'), r.get('schedule_time')); }
                }],
                statusTemplate: '合计：实际授课总数{finished_time}、计划达标授课总数（学期）{schedule_time}、授课达标占比（%）{rate}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            finished_time: 0,
                            schedule_time: 0
                        }, store.proxy.reader.rawData.data.total), rate;
                        rate = bbtConfig.getRate(data.finished_time, data.schedule_time);
                        data = Ext.merge({rate: rate}, data);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }*/]
        },
        //班班通授课时长统计
        timeUsedCount: {
            title: '教师授课 > 班班通授课时长统计',
            grid: [{
                title: '按街道乡镇统计',
                url: '/statistic/time-used/by-town/',
                exportUrl: '/statistic/time-used/by-town/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '班级总数',
                    dataIndex: 'class_count'
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
                title: '按学校统计',
                url: '/statistic/time-used/by-school/',
                exportUrl: '/statistic/time-used/by-school/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '班级总数',
                    dataIndex: 'class_count'
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
                title: '按学校年级统计',
                url: '/statistic/time-used/by-grade/',
                exportUrl: '/statistic/time-used/by-grade/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'query', '->', 'export']],
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
                    text: '班级总数',
                    dataIndex: 'class_count'
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
                title: '按班级统计',
                url: '/statistic/time-used/by-class/',
                exportUrl: '/statistic/time-used/by-class/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'query', '->', 'export']],
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
            }/*, {
                title: '按教师统计',
                url: '/statistic/time-used/by-teacher/',
                exportUrl: '/statistic/time-used/by-teacher/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'iTeacherName', 'query', '->', 'export']],
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
                        time = Math.floor(time/60);
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
                        return (v ? Math.floor(v/60) : 0);
                    }
                }],
                statusTemplate: '合计：实际授课总时长 {total_time_used} 分钟',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_time_used: Math.floor(store.proxy.reader.rawData.data.total_time_used/60)
                        };
                       return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
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
                        time = Math.floor(time/60);
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
                        return (v ? Math.floor(v/60) : 0);
                    }
                }],
                statusTemplate: '合计：实际授课总时长 {total_time_used} 分钟',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_time_used: Math.floor(store.proxy.reader.rawData.data.total_time_used/60)
                        };
                       return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                },
                pagination: true,
                enableSummary: true
            }*/]
        },
        //授课人数比例统计
        teacherNumber: {
            title: '教师授课 > 班班通授课人数统计',
            grid: [{
                title: '按街道乡镇统计',
                url: '/statistic/teacher-active/by-town/',
                exportUrl: '/statistic/teacher-active/by-town/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
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
                title: '按学校统计',
                url: '/statistic/teacher-active/by-school/',
                exportUrl: '/statistic/teacher-active/by-school/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
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
                title: '按学校课程统计',
                url: '/statistic/teacher-active/by-lesson/',
                exportUrl: '/statistic/teacher-active/by-lesson/export/',
                tools: [['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'course', 'query', '->', 'export']],
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
                title: '按学校年级统计',
                url: '/statistic/teacher-active/by-grade/',
                exportUrl: '/statistic/teacher-active/by-grade/export/',
                tools: [['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'query', '->', 'export']],
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
                title: '按街道乡镇统计',
                url: '/statistic/teacher-absent/by-town/',
                exportUrl: '/statistic/teacher-absent/by-town/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
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
                title: '按学校统计',
                url: '/statistic/teacher-absent/by-school/',
                exportUrl: '/statistic/teacher-absent/by-school/export/',
                tools: ['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
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
                title: '按学校课程统计',
                url: '/statistic/teacher-absent/by-lesson/',
                exportUrl: '/statistic/teacher-absent/by-lesson/export/',
                tools: [['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'course', 'query', '->', 'export']],
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
                title: '按学校年级统计',
                url: '/statistic/teacher-absent/by-grade/',
                exportUrl: '/statistic/teacher-absent/by-grade/export/',
                tools: [['queryMethodEx', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'grade', 'query', '->', 'export']],
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
                    renderer: function(v){ return v ? v + '年级' : ''; }
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
                title: '学校资源来源统计',
                url: '/statistic/resource/resource-from/',
                exportUrl: '/statistic/resource/resource-from/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'resourceFrom', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '资源来源',
                    dataIndex: 'resource_from'
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
                title: '学校资源类型统计',
                url: '/statistic/resource/resource-type/',
                exportUrl: '/statistic/resource/resource-type/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'resourceType', 'query', '->', 'export']],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
                    text: '资源类型',
                    dataIndex: 'resource_type'
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
                title : '学校课程使用统计',
                url: '/statistic/resource/lesson/',
                exportUrl: '/statistic/resource/lesson/export/',
                tools: [['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate'], ['town', 'school', 'course', 'query', '->', 'export']],
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
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
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
                tools: [['qdate', 'startDate', 'endDate', 'town', 'school', 'assetReportType', 'assetType'], ['iDeviceModel', 'assetFrom', 'remark', 'report_user', 'query', '->', 'export']],
                pagination: true,
                query: {
                    '_': '7'
                }
            }            
        },
        //资产维修查询
        assetrepairhistosy: {
            grid: {
                title: '资产管理 > 资产维修查询',
                url: '/asset/asset-repair/',
                exportUrl: '/asset/asset-repair/export/',
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
                }, {
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
                    renderer: function(v){ return v ? v+'班' : '';}
                }, {
                    text: '申报用户',
                    width: 60,
                    dataIndex: 'reported_by'
                }, {
                    text: '备注',
                    dataIndex: 'remark',
                    flex: 1
                }],
                tools: [['qdate', 'startDate', 'endDate', 'town', 'school', {tool: 'grade', computerclass: true}, 'class'], ['report_user', 'assetType', 'iDeviceModel', /*'assetPos', */'remark', 'query', '->', 'export']],
                pagination: true,
                query: {
                    '_': '7'
                }
            }
        },
        eduunit: {
            title: '教师授课 > 教学点教室使用统计',
            grid: [{
                title: '按街道乡镇统计',
                url: '/edu-unit/statistic/classroom-use/by-town/',
                exportUrl: '/edu-unit/statistic/classroom-use/by-town/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教室总数',
                    dataIndex: 'room_count',
                }, {
                    text: '使用时长（分钟）',
                    width: 120,
                    dataIndex: 'use_time'
                }, {
                    text: '折合课时（45分钟/节）',
                    width: 160,
                    dataIndex: 'to_class_time'
                }, {
                    text: '开机时长（分钟）',
                    width: 120,
                    dataIndex: 'boot_time'
                }, {
                    text: '使用占比（%）',
                    dataIndex: 'percent'
                }],
                pagination: true,
                statusTemplate: '合计：使用时长{use_time}、开机时长{boot_time}、使用占比{percent}、折合课时{to_class_time}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            use_time: 0,
                            boot_time: 0,
                            to_class_time: 0,
                            percent: '0.00%'
                        }, store.proxy.reader.rawData.data.total);
                        data.use_time = bbtConfig.humanReadTime(data.use_time);
                        data.boot_time = bbtConfig.humanReadTime(data.boot_time);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按教学点统计',
                url: '/edu-unit/statistic/classroom-use/by-unit/',
                exportUrl: '/edu-unit/statistic/classroom-use/by-unit/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'eduTown', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教学点',
                    dataIndex: 'point_name',
                    width: 160
                }, {
                    text: '教室总数',
                    dataIndex: 'room_count',
                }, {
                    text: '使用时长（分钟）',
                    width: 120,
                    dataIndex: 'use_time'
                }, {
                    text: '折合课时（45分钟/节）',
                    width: 160,
                    dataIndex: 'to_class_time'
                }, {
                    text: '开机时长（分钟）',
                    width: 120,
                    dataIndex: 'boot_time'
                }, {
                    text: '使用占比（%）',
                    dataIndex: 'percent'
                }],
                pagination: true,
                statusTemplate: '合计：使用时长{use_time}、开机时长{boot_time}、使用占比{percent}、折合课时{to_class_time}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            use_time: 0,
                            boot_time: 0,
                            to_class_time: 0,
                            percent: '0.00%'
                        }, store.proxy.reader.rawData.data.total);
                        data.use_time = bbtConfig.humanReadTime(data.use_time);
                        data.boot_time = bbtConfig.humanReadTime(data.boot_time);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按教学点教室统计',
                url: '/edu-unit/statistic/classroom-use/by-unit-class/',
                exportUrl: '/edu-unit/statistic/classroom-use/by-unit-class/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'eduTown', 'eduPoint', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教学点',
                    dataIndex: 'point_name',
                    width: 160
                }, {
                    text: '教室编号',
                    dataIndex: 'name',
                    width: 160
                }, /*{
                    text: '教室总数',
                    dataIndex: 'number',
                }, */{
                    text: '使用时长（分钟）',
                    width: 120,
                    dataIndex: 'use_time'
                }, {
                    text: '折合课时（45分钟/节）',
                    width: 160,
                    dataIndex: 'to_class_time'
                }, {
                    text: '开机时长（分钟）',
                    width: 120,
                    dataIndex: 'boot_time'
                }, {
                    text: '使用占比（%）',
                    dataIndex: 'percent'
                }],
                pagination: true,
                statusTemplate: '合计：使用时长{use_time}、开机时长{boot_time}、使用占比{percent}、折合课时{to_class_time}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = Ext.merge({
                            use_time: 0,
                            boot_time: 0,
                            to_class_time: 0,
                            percent: '0.00%'
                        }, store.proxy.reader.rawData.data.total);
                        data.use_time = bbtConfig.humanReadTime(data.use_time);
                        data.boot_time = bbtConfig.humanReadTime(data.boot_time);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }]
        }
    },
    //资源使用
    bbtResourceStatic: {
        resourceFrom: {
            title: '资源使用 > 资源来源使用统计',
            grid: [{
                title: '按街道乡镇统计',
                url: '/statistic/resource-from/town/',
                exportUrl: '/statistic/resource-from/town/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'resourceFrom', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
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
                title: '按学校统计',
                url: '/statistic/resource-from/school/',
                exportUrl: '/statistic/resource-from/school/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'school', 'resourceFrom', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
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
                title: '按街道乡镇统计',
                url: '/statistic/resource-type/town/',
                exportUrl: '/statistic/resource-type/town/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'resourceType', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
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
                title: '按学校统计',
                url: '/statistic/resource-type/school/',
                exportUrl: '/statistic/resource-type/school/export/',
                tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'school', 'resourceType', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '学校',
                    dataIndex: 'school_name',
                    width: 160
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
        },
        file: {
            title: '资源使用 > 卫星接收资源统计',
            grid: [{
                title: '按街道乡镇统计',
                url: '/edu-unit/statistic/resource-store/by-town/',
                exportUrl: '/edu-unit/statistic/resource-store/by-town/export/',
                tools: [{tool: 'schoolYear', useCurrent: true}, 'term', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教学点个数',
                    dataIndex: 'total_unit'
                }, {
                    text: '资源文件个数',
                    width: 160,
                    dataIndex: 'total_count'
                }, {
                    text: '资源文件种类',
                    width: 160,
                    dataIndex: 'total_type'
                }, {
                    text: '资源文件大小',
                    dataIndex: 'total_size'
                }, {
                    text: '平均接收大小/教学点',
                    dataIndex: 'avg_size',
                    width: 160
                }],
                pagination: true,
                statusTemplate: '合计：资源接收总大小: {total_resource_size}, 资源接收文件总个数: {total_resource_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_resource_count: store.proxy.reader.rawData.data.total_resource_count,
                            total_resource_size: store.proxy.reader.rawData.data.total_resource_size
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }, {
                title: '按教学点统计',
                url: '/edu-unit/statistic/resource-store/by-unit/',
                exportUrl: '/edu-unit/statistic/resource-store/by-unit/export/',
                tools: [{tool: 'schoolYear', useCurrent: true}, 'term', 'eduTown', 'query', '->', 'export'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教学点',
                    dataIndex: 'point_name'
                }, {
                    text: '资源文件个数',
                    width: 160,
                    dataIndex: 'total_count'
                }, {
                    text: '资源文件种类',
                    width: 160,
                    dataIndex: 'total_type'
                }, {
                    text: '资源文件大小',
                    dataIndex: 'total_size'
                }],
                pagination: true,
                statusTemplate: '合计：资源接收总大小: {total_resource_size}, 资源接收文件总个数: {total_resource_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_resource_count: store.proxy.reader.rawData.data.total_resource_count,
                            total_resource_size: store.proxy.reader.rawData.data.total_resource_size
                        };
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }]
        },
        fileLog: {
            grid: {
                title: '资源使用 > 卫星接收资源日志',
                url: '/edu-unit/resource-store/details/',
                exportUrl: '/edu-unit/resource-store/details/export/',
                tools: ['qdate', 'startDate', 'endDate', 'eduTown', 'eduPoint', 'query'],
                columns: [{
                    text: '街道乡镇',
                    dataIndex: 'town_name',
                    width: 160
                }, {
                    text: '教学点',
                    dataIndex: 'point_name'
                }, {
                    text: '资源接收时间',
                    width: 140,
                    dataIndex: 'rece_time'
                }, {
                    text: '资源文件个数',
                    width: 160,
                    dataIndex: 'rece_count'
                }, {
                    text: '资源文件种类数',
                    dataIndex: 'rece_type'
                }, {
                    text: '资源文件大小',
                    dataIndex: 'rece_size',
                    renderer: function(v){
                        return bbtConfig.humanReadSize(v);
                    }
                }, {
                    text: '详细信息',
                    hidden: true,
                    dataIndex: 'details',
                    renderer: function(){
                        return '';
                    }
                }],
                plugins: [{
                    ptype: 'rowexpander',
                    rowBodyTpl : [
                        '<div class="expanded-body"><table style="table-layout:fixed;width:100%;"><thead><tr><td>文件类型</td><td>文件数量</td><td>文件大小（KB）</td></tr></thead><body>',
                        '<tpl for="details"><tr><td>{type}</td><td>{count}</td><td>{size}</td></tr></tpl>',
                        '</tbody></table></div>'
                    ]
                }],
                pagination: true,
                statusTemplate: '合计：资源接收总大小: {total_resource_size}, 资源接收文件总个数: {total_resource_count}',
                statusRender: function(template, paginationbar, store) {
                    try {
                        var data = {
                            total_resource_count: store.proxy.reader.rawData.data.total_resource_count,
                            total_resource_size: store.proxy.reader.rawData.data.total_resource_size
                        };
                        data.total_resource_size = bbtConfig.humanReadSize(data.total_resource_size);
                        return bbtConfig.tmpl(template, data, 0);
                    } catch (e) {
                        ;
                    }
                }
            }
        }
    },
    //终端开机使用统计
    bbtMachineStatic: {
        title: '资产管理 > 学校终端开机统计',
        grid: [{
            title: '按街道乡镇统计',
            url: '/terminal/time-used/by-town/',
            exportUrl: '/terminal/time-used/by-town/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
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
            }
        }, {
            title: '按学校统计',
            url: '/terminal/time-used/by-school/',
            exportUrl: '/terminal/time-used/by-school/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'query', '->', 'export'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '学校',
                dataIndex: 'school_name',
                width: 160
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
            }
        }, {
            title: '按学校年级统计',
            url: '/terminal/time-used/by-grade/',
            exportUrl: '/terminal/time-used/by-grade/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'school', 'query', '->', 'export'],
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
            }
        }, {
            title: '按班级统计',
            url: '/terminal/time-used/by-class/',
            exportUrl: '/terminal/time-used/by-class/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'town', 'school', {tool:'grade', computerclass:true}, 'query', '->', 'export'],
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
        title: '资产管理 > 终端开机日志',
        grid: [{
            title: '学校',
            url: '/terminal/time-used/log/',
            exportUrl: '/terminal/time-used/log/export/',
            tools: ['qdate', 'startDate', 'endDate', 'town', 'school', {tool:'grade',computerclass:true}, 'class', 'query'],
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
                width: 140,
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
        }, {
            title: '教学点',
            url: '/edu-unit/terminal-boot/details/',
            exportUrl: '/edu-unit/terminal-boot/details/export/',
            tools: ['qdate', 'startDate', 'endDate', 'eduTown', 'eduPoint', 'eduClassNo', 'query'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '教学点',
                dataIndex: 'point_name',
                width: 160
            }, {
                text: '教室终端编号',
                dataIndex: 'number'
            }, {
                text: '使用日期',
                dataIndex: 'create_time',
                width: 140
            }, {
                text: '开机时长',
                width: 140,
                dataIndex: 'boot_time',
                renderer: function(v){
                    return bbtConfig.humanReadTime(v);
                }
            }, {
                text: '开机次数',
                dataIndex: 'boot_count'
            }],
            pagination: true,
            statusTemplate: '合计：开机总时长{boot_time_total}, 开机总次数{boot_count_total}',
            statusRender: function(template, paginationbar, store) {
                try {
                    var data = Ext.merge({
                        boot_time_total: 0,
                        boot_count_total: 0
                    }, store.proxy.reader.rawData.data.total);
                    data.boot_time_total = bbtConfig.humanReadTime(data.boot_time_total);
                    return bbtConfig.tmpl(template, data, 0);
                } catch (e) {
                    ;
                }
            }
        }]
    },
    //教学点终端开机使用统计
    eduMachineStatic: {
        title: '资产管理 > 教学点终端开机统计',
        grid: [{
            title: '按街道乡镇统计',
            url: '/edu-unit/statistic/terminal-boot/by-town/',
            exportUrl: '/edu-unit/statistic/terminal-boot/by-town/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'query', '->', 'export'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '教室终端总数',
                dataIndex: 'room_count'
            }, {
                text: '日平均开机时长（分钟）',
                width: 160,
                dataIndex: 'boot_time_average'
            }, {
                text: '日平均开机次数',
                dataIndex: 'boot_count_average'
            }, {
                text: '开机总时长',
                dataIndex: 'boot_time_total',
                width: 140,
                renderer: function(v){
                    return bbtConfig.humanReadTime(v);
                }
            }, {
                text: '开机总次数',
                dataIndex: 'boot_count_total'
            }],
            pagination: true,
            statusTemplate: '合计：开机总时长{boot_time_total}, 开机总次数{boot_count_total}',
            statusRender: function(template, paginationbar, store) {
                try {
                    var data = Ext.merge({
                        boot_time_total: 0,
                        boot_count_total: 0
                    }, store.proxy.reader.rawData.data.total);
                    data.boot_time_total = bbtConfig.humanReadTime(data.boot_time_total);
                    return bbtConfig.tmpl(template, data, 0);
                } catch (e) {
                    ;
                }
            }
        }, {
            title: '按教学点统计',
            url: '/edu-unit/statistic/terminal-boot/by-unit/',
            exportUrl: '/edu-unit/statistic/terminal-boot/by-unit/export/',
            tools: ['queryMethod', 'schoolYear', 'term', 'startDate', 'endDate', 'eduTown', 'query', '->', 'export'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '教学点',
                dataIndex: 'point_name',
                width: 160
            }, {
                text: '教室终端总数',
                dataIndex: 'room_count'
            }, {
                text: '日平均开机时长（分钟）',
                width: 160,
                dataIndex: 'boot_time_average'
            }, {
                text: '日平均开机次数',
                dataIndex: 'boot_count_average'
            }, {
                text: '开机总时长',
                dataIndex: 'boot_time_total',
                width: 140,
                renderer: function(v){
                    return bbtConfig.humanReadTime(v);
                }
            }, {
                text: '开机总次数',
                dataIndex: 'boot_count_total'
            }],
            pagination: true,
            statusTemplate: '合计：开机总时长{boot_time_total}, 开机总次数{boot_count_total}',
            statusRender: function(template, paginationbar, store) {
                try {
                    var data = Ext.merge({
                        boot_time_total: 0,
                        boot_count_total: 0
                    }, store.proxy.reader.rawData.data.total);
                    data.boot_time_total = bbtConfig.humanReadTime(data.boot_time_total);
                    return bbtConfig.tmpl(template, data, 0);
                } catch (e) {
                    ;
                }
            }
        }]
    },
    //教学点终端开机使用日志
    eduMachineLog: {
        grid: {
            title: '资产管理 > 终端开机使用日志',
            url: '/edu-unit/ terminal-boot/details/',
            exportUrl: '/edu-unit/ terminal-boot/details/export/',
            tools: ['qdate', 'startDate', 'endDate', 'town', 'school', {tool:'grade',computerclass:true}, 'class', 'query'],
            columns: [{
                text: '街道乡镇',
                dataIndex: 'town_name',
                width: 160
            }, {
                text: '教学点',
                dataIndex: 'point_name',
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
                width: 140,
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
Ext.define("Ext.ux.RowExpander",{extend:"Ext.AbstractPlugin",requires:["Ext.grid.feature.RowBody","Ext.grid.feature.RowWrap"],alias:"plugin.rowexpander",rowBodyTpl:null,expandOnEnter:true,expandOnDblClick:true,selectRowOnExpand:false,rowBodyTrSelector:".x-grid-rowbody-tr",rowBodyHiddenCls:"x-grid-row-body-hidden",rowCollapsedCls:"x-grid-row-collapsed",renderer:function(d,b,a,c,e){if(e===0){b.tdCls="x-grid-td-expander"}return'<div class="x-grid-row-expander">&#160;</div>'},constructor:function(){this.callParent(arguments);var b=this.getCmp();this.recordsExpanded={};if(!this.rowBodyTpl){Ext.Error.raise("The 'rowBodyTpl' config is required and is not defined.")}var a=Ext.create("Ext.XTemplate",this.rowBodyTpl),c=[{ftype:"rowbody",columnId:this.getHeaderId(),recordsExpanded:this.recordsExpanded,rowBodyHiddenCls:this.rowBodyHiddenCls,rowCollapsedCls:this.rowCollapsedCls,getAdditionalData:this.getRowBodyFeatureData,getRowBodyContents:function(d){return a.applyTemplate(d)}},{ftype:"rowwrap"}];if(b.features){b.features=c.concat(b.features)}else{b.features=c}},init:function(a){this.callParent(arguments);this.grid=a;this.addExpander();a.on("render",this.bindView,this,{single:true});a.on("reconfigure",this.onReconfigure,this)},onReconfigure:function(){this.addExpander()},addExpander:function(){this.grid.headerCt.insert(0,this.getHeaderConfig())},getHeaderId:function(){if(!this.headerId){this.headerId=Ext.id()}return this.headerId},getRowBodyFeatureData:function(c,a,b,f){var d=Ext.grid.feature.RowBody.prototype.getAdditionalData.apply(this,arguments),e=this.columnId;d.rowBodyColspan=d.rowBodyColspan-1;d.rowBody=this.getRowBodyContents(c);d.rowCls=this.recordsExpanded[b.internalId]?"":this.rowCollapsedCls;d.rowBodyCls=this.recordsExpanded[b.internalId]?"":this.rowBodyHiddenCls;d[e+"-tdAttr"]=' valign="top" rowspan="2" ';if(f[e+"-tdAttr"]){d[e+"-tdAttr"]+=f[e+"-tdAttr"]}return d},bindView:function(){var a=this.getCmp().getView(),b;if(!a.rendered){a.on("render",this.bindView,this,{single:true})}else{b=a.getEl();if(this.expandOnEnter){this.keyNav=Ext.create("Ext.KeyNav",b,{enter:this.onEnter,scope:this})}if(this.expandOnDblClick){a.on("itemdblclick",this.onDblClick,this)}this.view=a}},onEnter:function(h){var b=this.view,g=b.store,j=b.getSelectionModel(),a=j.getSelection(),f=a.length,c=0,d;for(;c<f;c++){d=g.indexOf(a[c]);this.toggleRow(d)}},toggleRow:function(f){var b=this.view,e=b.getNode(f),g=Ext.get(e),c=Ext.get(g).down(this.rowBodyTrSelector),a=b.getRecord(e),d=this.getCmp();if(g.hasCls(this.rowCollapsedCls)){g.removeCls(this.rowCollapsedCls);c.removeCls(this.rowBodyHiddenCls);this.recordsExpanded[a.internalId]=true;b.refreshSize();b.fireEvent("expandbody",e,a,c.dom)}else{g.addCls(this.rowCollapsedCls);c.addCls(this.rowBodyHiddenCls);this.recordsExpanded[a.internalId]=false;b.refreshSize();b.fireEvent("collapsebody",e,a,c.dom)}},onDblClick:function(b,a,d,c,f){this.toggleRow(d)},getHeaderConfig:function(){var c=this,b=Ext.Function.bind(c.toggleRow,c),a=c.selectRowOnExpand;return{id:this.getHeaderId(),width:24,sortable:false,resizable:false,draggable:false,hideable:false,menuDisabled:true,cls:Ext.baseCSSPrefix+"grid-header-special",renderer:function(e,d){d.tdCls=Ext.baseCSSPrefix+"grid-cell-special";return'<div class="'+Ext.baseCSSPrefix+'grid-row-expander">&#160;</div>'},processEvent:function(i,f,d,g,h,j){if(i=="mousedown"&&j.getTarget(".x-grid-row-expander")){var k=j.getTarget(".x-grid-row");b(k);return a}}}}});
