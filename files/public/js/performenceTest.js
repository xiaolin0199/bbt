Ext.define('bbt.ComboTree', {
    extend: 'Ext.form.field.Picker',
    alias: 'widget.combotree',
    matchFieldWidth: true,
    editable: false,
    createPicker: function(){
        Ext.apply(this.treeConfig, {
            autoScroll: true,
            floating: true,
            focusOnToFront: false,
            shadow: true,
            ownerCt:this.ownerCt,
            bodyStyle: 'margin-top-color: #FFF;',
            listeners: {
                afterrender: function(){
                    var walk, root = this.getRootNode();
                    walk = function(node){
                        if(node.get('children')) {
                            node.set('leaf', false);
                        } else {
                            node.set('leaf', true);
                        }
                        node.set('checked', false);
                        node.eachChild(walk);
                    };
                    walk(root);
                    this.getEl().down('.x-panel-body').setStyle({borderTopWidth: '0px'});
                },
                checkchange: function(node, cf){
                    var walk = function(node){
                        node.set('checked', cf);
                        node.eachChild(walk);
                    };
                    node.eachChild(walk);
                },
                itemclick: function(v, node){
                    if(node.raw.url == "custom") {
                        Ext.create('Ext.window.Window', {
                            modal: true,
                            width: 400,
                            height: 300,
                            layout: 'fit',
                            items: [{
                                xtype: 'urlgrid',
                                border: false
                            }],
                            listeners: {
                                beforedestroy: function(){
                                    var store = this.down('grid').store, rcs = [], root, custom;
                                    root = Ext.getCmp('tester').down('[name=range]').tree.getRootNode();
                                    custom = root.findChild('text', '自定义');
                                    root.remove(custom);
                                    store.each(function(o){
                                        o = o.data;
                                        o.leaf = true;
                                        o.checked = true;
                                        rcs.push(o);
                                    });
                                    root.appendChild(rcs);
                                    root.appendChild(custom);
                                    store.removeAll();
                                }
                            }
                        }).show();
                        node.set('checked', false)
                    }
                }
            }
        });
        var tree = new Ext.tree.Panel(this.treeConfig);
        this.tree = tree;
        return tree;
    },
    getValue: function(){
        try {
            var root = this.tree.getRootNode(), urls = [], walk;
            walk = function(node){
                if(node.raw.url && node.get('checked')) {
                    urls.push(node.raw.url);
                }
                node.eachChild(walk);
            };
            walk(root);
            return urls;
        } catch(e) {
            return [];
        }
    }
});
Ext.define('bbt.UrlGrid', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.urlgrid',
    store: new Ext.data.Store({fields: ['text', 'url']}),
    columns: {
        defaults: {flex: 1},
        items: [{
            text: 'URL',
            dataIndex: 'url',
            editor: {
                xtype: 'textfield',
                regex: /^\//,
                regexText: '必须以 / 开头',
                allowBlank: false
            }
        }, {
            text: '说明',
            dataIndex: 'text',
            minLength: 1,
            editor: {xtype: 'textfield', allowBlank: false}
        }]
    },
    tbar: [{
        text: '添加',
        handler: function(){
            var grid = this.up('grid'), rc, e;
            rc = grid.store.add({})[0];
            e = grid.getPlugin('editor');
            e.editing && e.completeEdit();
            e.startEdit(rc, 1);
        }
    }],
    plugins: [{pluginId: 'editor', ptype: 'rowediting', clicksToEdit: 1, errorSummary: false}]
});
(function(){
    var urlCounter, timeCounter = {}, allLinks = [{text: '通用', children: [{
        text: '教师',
        url: '/system/teacher/list/'
    }, {
        text: '年级班级',
        url: '/classes/'
    }, {
        text: '管理范围',
        url: '/group/'
    }, {
        text: '个人信息',
        url: '/details/'
    }, {
        text: '权限',
        url: '/privileges/'
    }, {
        text: '课程',
        url: '/system/lesson_name/list/'
    }, {
        text: '节次',
        url: '/system/lesson_period/list/'
    }, {
        text: '学年',
        url: '/system/term/list_school_year/'
    }, {
        text: '资源来源',
        url: '/system/resource/list/'
    }, {
        text: '资产类型',
        url: '/asset/asset_type/list/'
    }]}/*, {
        text: '使用记录',
        children: [{
            text: '班班通登录日志',
            url: '/activity/logged_in/'
        }, {
            text: '班班通未登录日志',
            url: '/activity/not_logged_in/'
        }]
    }, {
        text: '统计分析',
        children: [{
            text: '教师授课次数比例统计',
            url: '/statistic/teacher_lesson_count/'
        }, {
            text: '教师授课人数比例统计'
            url: '/statistic/teacher_lesson_grade/,'
        }, {
            text: '教师未登录班班通统计',
            url: ''
        }, {
            text: '授课资源使用统计',
            url: ''
        }]
    }, {
        text: '资产管理',
        children: [{
            text: '资产申报记录查询',
            url: 'asset/asset_log/list/'
        }, {
            text: '资产维修管理',
            url: '/asset/asset_repair/list/'
        }]
    }*/, {
        text: '自定义',
        url: 'custom'
    }];
    Ext.Ajax.on('beforerequest', function(conn, options, e){
        var url = options.url;
        if(!urlCounter) { return; }
        if(url in urlCounter) {
            urlCounter[url]['total'] += 1;
        } else {
            urlCounter[url] = {url: url, total: 1, success: 0, failure: 0, exception: 0, averageTime: 0, totalTime: 0};
        }
        urlCounter[url]['time'] = {start: new Date().getTime()};
    });
    Ext.Ajax.on('requestcomplete', function(conn, resp, options){
        var data = Ext.decode(resp.responseText)||{},
            url = options.url, t;
        if(!urlCounter) { return; }
        if(data && data.status == "success") {
            urlCounter[url]['success'] += 1;
        } else {
            urlCounter[url]['failure'] += 1;
        }
        if(urlCounter[url]['time']) {
            t = new Date().getTime()
            urlCounter[url]['time']['end'] = t;
            urlCounter[url]['totalTime'] += t - urlCounter[url]['time']['start'];
            urlCounter[url]['averageTime'] = urlCounter[url]['totalTime'] / urlCounter[url]['total'];
        }
    });
    Ext.Ajax.on('requestexception', function(conn, resp, options){
        var url = options.url, t;
        if(!urlCounter) { return; }
        urlCounter[url]['exception'] += 1;
        if(urlCounter[url]['time']) {
            t = new Date().getTime()
            urlCounter[url]['time']['end'] = t;
            urlCounter[url]['totalTime'] += t - urlCounter[url]['time']['start'];
        }
    });

    function initUI(){
        new Ext.window.Window({
            title: '班班通性能测试',
            id: 'tester',
            autoShow: true,
            closzable: false,
            width: 800,
            height: 480,
            layout: 'fit',
            items: [{
                xtype: 'grid',
                border: false,
                tbar: [{
                    xtype: 'textfield',
                    fieldLabel: '请求时间间隔',
                    name: 'interval',
                    width: 200,
                    regex: /^\d+$/,
                    regexText: '请输入数字',
                    value: 0
                }, {
                    xtype: 'combotree',
                    name: 'range',
                    fieldLabel: '测试范围',
                    treeConfig: {
                        header: false,
                        height: 170,
                        store: new Ext.data.TreeStore({root: {expanded: true,text: '所有', children: allLinks}})
                    }
                }, '->', {
                    xtype: 'button',
                    text: '开始测试',
                    action: 'start',
                    handler: function(){
                        var tb = this.up('toolbar'),
                            interval = tb.down('[name=interval]'),
                            range = tb.down('[name=range]');
                        if(interval.isValid() && range.isValid()) {
                            tb.up('grid').startTest(parseInt(interval.getValue()), range.getValue());
                        }
                    }
                }, {
                    xtype: 'button',
                    text: '停止测试',
                    action: 'stop',
                    disabled: true,
                    handler: function(){
                        this.up('grid').closeFlags();
                    }
                }],
                columns: {
                    items: [{
                        text: 'URL',
                        dataIndex: 'url',
                        flex: 1
                    }, {
                        text: '总次数',
                        dataIndex: 'total'
                    }, {
                        text: '成功次数',
                        dataIndex: 'success'
                    }, {
                        text: '失败次数',
                        dataIndex: 'failure'
                    }, {
                        text: '异常次数',
                        dataIndex: 'exception'
                    }, {
                        text: '平均耗时',
                        dataIndex: 'averageTime'
                    }, {
                        text: '总耗时',
                        dataIndex: 'totalTime'
                    }],
                    defaults: {menuDisabled: true, sortable: false, draggable: false}
                },
                store: new Ext.data.Store({fields: ['url', 'total', 'success', 'failure', 'exception', 'averageTime', 'totalTime']}),
                updateStore: function(){
                    var data = urlCounter, url, records = [], obj;
                    for(url in data) {
                        records.push(data[url]);
                    }
                    this.store.loadData(records);
                    this.getView().refresh();
                },
                openFlags: function(){
                    var tb = this.down('toolbar'),
                        interval = tb.down('[name=interval]'),
                        range = tb.down('[name=range]'),
                        start = tb.down('[action=start]'),
                        stop = tb.down('[action=stop]');
                    this.stopTest = false;
                    interval.setDisabled(true);
                    range.setDisabled(true);
                    start.setDisabled(true);
                    stop.setDisabled(false);
                },
                closeFlags: function(){
                    var tb = this.down('toolbar'),
                        interval = tb.down('[name=interval]'),
                        range = tb.down('[name=range]'),
                        start = tb.down('[action=start]'),
                        stop = tb.down('[action=stop]');
                    this.stopTest = true;
                    interval.setDisabled(false);
                    range.setDisabled(false);
                    start.setDisabled(false);
                    stop.setDisabled(true);
                },
                startTest:function(interval, urls){
                    var me = this, request, testTimer, container, re=/^\//;
                    request = function(url){
                        var inner = function(){
                            Ext.Ajax.request({
                                url: url,
                                callback: function(){
                                    if(!me.stopTest) {
                                        setTimeout(inner, interval);
                                    }
                                }
                            });
                        };
                        inner();
                    };
                    
                    if(urls.length) {
                        me.openFlags();
                        urlCounter = {};
                        Ext.each(urls, function(url){
                            re.test(url) && request(url);
                        });

                        testTimer = setInterval(function(){
                            me.updateStore();
                            if(me.stopTest) {
                                clearInterval(testTimer);
                            }
                        }, 50);
                    }
                }
            }]
        });
    }
    function getAllLinks() {
        var urls = [], walk = function(node){
            if(node.url) {
                urls.push(node.url);
                node.children && Ext.each(node.children, walk);
            }
        };
        walk(allLinks);
        return urls;
    }
    Ext.onReady(function(){
        initUI();
    });
})();