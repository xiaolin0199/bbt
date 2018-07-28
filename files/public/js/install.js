/*jshint sub:false,expr:true*/
function BBTWebSocket(url) {
    var me = this, buildSocket;
    if(!url) {
        throw new Error("url can't be empty");
    }
    if(!me instanceof BBTWebSocket) {
        return new BBTWebSocket(url);
    }
    buildSocket = function(){
        var socket = new WebSocket(url), timer;
        socket.onclose = function(e){
            console.log('%cWebSocket onclose ...', 'color:red');
            if(me._destroyed) { return; }
            else {
                if(timer) { return; }
                timer = setTimeout(function(){
                    me._socket = buildSocket();
                    timer = null;
                    console.log("rebuild websocket instance!");
                }, 500);
            }
        };
        socket.onerror = function(e){
            console.log("error occured");
        };
        //这个回调处理两种消息：客户端主动请求收到的消息和被动响应的消息
        socket.onmessage = function(e){
            var data, key;
            try {
                data = JSON.parse(e.data);
                key = data.callback;
                me[key](null, data);
            } catch(e) {
                me[key](e);
            } finally {
                key && (delete me[key]);
            }
        };
        socket.onopen = function(e){
            var q = me._queue;
            console.log("web socket was opened!");
            while(q.length) {
                socket.send(JSON.stringify(q.shift()));
            }
            me.ready && me.ready();
        };
        return socket;
    };
    try {
        me._socket = buildSocket();
    } catch(e) {
        alert('当前浏览器不支持 WebSocket，请您使用谷歌浏览器重试！');
        me.destroy();
    }
}
BBTWebSocket.remoteTest = function(host, port, key, callback){
    var syncSocket = new BBTWebSocket('ws://' + host + ':' + port + '/ws/sync');
    syncSocket.key = key;
    syncSocket.ready = function(){
        syncSocket.request('remote-test', {key: key}, callback);
    };
};
BBTWebSocket.prototype = {
    callbackCounter: 0,
    constructor: BBTWebSocket,
    _queue: [],
    emit: function(data, callback){
        var me = this, key = 'callback-' + ++me.callbackCounter;
        data.callback = key;
        me[key] = callback;
        try {
            if(me._socket.readyState === me._socket.OPEN) {
                me._socket.send(JSON.stringify(data));
            } else {
                console.log('store data');
                me._queue.push(data);
            }
        } catch(e) {
            console.log(e);
            delete me[key];
        }

    },
    //包装主动请求的消息
    request: function(operation, data, category, callback){
        var me = this;
        if(arguments.length == 3) {
            callback = category;
            category = "sync";
        }
        me.emit({category: category, operation: operation, data: data}, function(e, data){
            if(e) {
                callback.call(me, e);
            } else {
                if(data.ret === 0) {
                    callback.apply(me, [null, data]);
                } else {
                    callback.call(me, data.msg || ERRORMSG[data.ret] || "unknow error");
                }
            }
        });
    },
    destroy: function(){
        var me = this;
        me._destroyed = true;
        try {
            me._socket.close();
        } catch(e) {
            console.log(e);
        }
    }
};
var bbt = {
    title: '噢易班班通管理分析系统',
    importTeacherUrl: '/install/teacher/import/',
    importLessonUrl: '/install/lesson_name/import/',
    importTermUrl: '/install/term/import/',
    importWorktimeUrl: '/install/lesson_period/import/',
    importGradeClassUrl: '/install/grade_class/import/',
    importLessonScheduleUrl: '/install/lesson_schedule/import/',
    importTeachInfoUrl: '/install/lesson_teacher/import/',
    listGradeClassUrl: '/install/grade_class/',
    promptWidth: 240,
    errorFn: function(form, a){
        var msg = bbt.utils.getErrorMsg(a.result);
        msg && Ext.Msg.alert('提示', msg);
        return msg;
    },
    installer: {
        init: function(){
            var uiConfig = this.config();

            Ext.each(['province', 'city', 'country', 'town'], function(v){
                Ext.create('Ext.data.Store', {
                    autoLoad: false,
                    storeId: v + 'Store',
                    proxy: {
                        type: 'ajax',
                        url: '/group_get_children/',
                        reader: {
                            type: 'json',
                            root: 'data.children'
                        },
                        startParam: undefined,
                        pageParam: undefined
                    },
                    fields: ['name'],
                    pageSize: 10000
                });
            });
            Ext.getStore('provinceStore').load();
            Ext.onReady(function(){
                var win = new Ext.window.Window(uiConfig);
                bbt.installer.initEvents(win);
                //win.getLayout().setActiveItem(4);
                win.show();
            });
            //init cookie
            Ext.state.Manager.setProvider(new Ext.state.CookieProvider());
        },
        initEvents: function(vp){
            var serverConfigPanel = Ext.getCmp('serverConfig-panel');

            bbt.utils.on(serverConfigPanel, {
                'combo[name]': {
                    afterrender: function(){
                        if(!/^province|city|country|town$/.test(this.name)) {
                            return;
                        }
                        this.store.on('load', function(){
                            this._value && this.setValue(this._value) && this.setReadOnly(true);
                            this.store.un('load', arguments.callee);
                        }, this);
                    },
                    change: function(me, v){
                        var next = me.nextArea, pnext,
                            params = {},
                            form=me.up('form').getForm(),
                            status = false, loadCB;
                        if(!v) { return; }
                        next = form.findField(next);
                        if(!next) { return; }
                        if(next.isDisabled()) { return; }
                        pnext = next;
                        while(pnext && !pnext.isDisabled()) {
                            pnext.setValue(undefined);
                            pnext = form.findField(pnext.nextArea);
                        }
                        Ext.each(['town', 'country', 'city', 'province'], function(level){
                            var combo = form.findField(level);
                            //if(combo.isDisabled()) { return; }
                            if(me.name === level) {
                                status = !status;
                            }
                            if(status) {
                                params[level+'_name'] = combo.getValue();
                            }
                        });

                        next.store.proxy.extraParams = params;
                        next.store.load();
                    }
                }
            });
        },
        config: function(){
            return {
                xtype: 'window',
                title: '服务器配置向导',
                width: 596,
                height: 400,
                layout: 'card',
                border: false,
                closable: false,
                resizable: false,
                defaultType: 'panel',
                items: [{ //0: 选择服务器类型
                    xtype: 'panel',
                    bodyCls: 'banner',
                    id: 'common-panel',
                    items: [{
                        xtype: 'fieldset',
                        style: {backgroundPosition: '110px 1px'},
                        border: false,
                        title: '选择服务器类型',
                        margin: '120 20 20 20',
                        items: [{
                            xtype: 'radiogroup',
                            defaultType: 'radio',
                            border: false,
                            layout: {type: 'hbox', pack: 'center'},
                            defaults: {margin: '0 0 0 30'},
                            items: [{
                                name: 'server_type',
                                boxLabel: '省级服务器',
                                inputValue: 'province',
                                margin: 0
                            }, {
                                name: 'server_type',
                                boxLabel: '地市州级服务器',
                                inputValue: 'city'
                            }, {
                                name: 'server_type',
                                boxLabel: '区县市级服务器',
                                inputValue: 'country'
                            }, {
                                name: 'server_type',
                                boxLabel: '校级服务器',
                                inputValue: 'school',
                                checked: true
                            }]
                        }]
                    }],
                    listeners: {
                        afterrender: function(){
                            var me = this, cb = function(options, flag, resp){
                                var data = Ext.decode(resp.responseText), layout, fm, cc;
                                //progress: start download import
                                if(data.status == "success" && /^start|download|import|complete$/.test(data.progress)) {
                                    layout = me.up('window').getLayout();
                                    layout.setActiveItem(3);
                                    cc = Ext.state.Manager.get('settings');
                                    if(cc) {
                                        fm = layout.getActiveItem().down('form').getForm();
                                        fm.setValues(cc);
                                    }
                                    if(data.progress == "complete") {
                                        Ext.Ajax.request({
                                            url: '/install/step/',
                                            params: {install_step: '-1'},
                                            success: function(){
                                                location.pathname = '/';
                                            },
                                            failure: bbt.errorFn
                                        });
                                        return;
                                    }
                                    bbt.startDataTransfer(cc);
                                }
                            };
                           /* Ext.Ajax.request({
                                url: '/install/remote/status/',
                                callback: cb
                            });*/
                        }
                    },
                    buttons: [{
                        text: '下一步',
                        handler: function(){
                            var radioGroup = this.up('panel').down('radiogroup'),
                                v = radioGroup.getValue(), layout, note;
                            bbt.server_type = v.server_type;
                            if(v.server_type == 'school') {
                                note = Ext.getCmp('domain-note');
                                note.show();
                                note.getEl().setHTML('注：用于学校终端与本服务器之间的通讯。');
                            } else if(v.server_type == 'country') {
                                note = Ext.getCmp('domain-note');
                                note.show();
                                note.getEl().setHTML('注：用于教学点终端与本服务器之间的通讯。');
                            }
                            bbt.server_text = radioGroup.getChecked()[0].boxLabel;
                            layout = this.up('window').getLayout();
                            if(bbt.server_type == "school") {
                                layout.setActiveItem(3);
                                layout.getActiveItem().down('button[action=next]').setText('下一步');
                            } else {
                                layout.setActiveItem(2);
                            }
                        }
                    }],
                    buttonAlign: 'right'
                }, { //2: 安装方式
                    xtype: 'panel',
                    bodyCls: 'banner',
                    items: [{
                        xtype: 'fieldset',
                        style: {backgroundPosition: '70px 1px'},
                        border: false,
                        title: '数据来源',
                        margin: '120 20 20 20',
                        items: [{
                            xtype: 'radiogroup',
                            defaultType: 'radio',
                            border: false,
                            layout: {type: 'vbox', pack: 'center'},
                            defaults: {margin: '0 0 0 30'},
                            items: [{
                                name: 'dataType',
                                boxLabel: '本地初始化',
                                checked: true,
                                inputValue: 'local'
                            }, {
                                xtype: 'component',
                                html: '适用于从未连接过上级服务器的情况。',
                                margin: '10 0 20 50'
                            }, {
                                name: 'dataType',
                                boxLabel: '上级服务器在线导入',
                                inputValue: 'remote'
                            }, {
                                xtype: 'component',
                                html: '适用于以前连接过上级服务器，本次为程序重新安装。',
                                margin: '10 0 0 50'
                            }]
                        }]
                    }],
                    buttons: [{
                        text: '下一步',
                        handler: function(){
                            var radioGroup = this.up('panel').down('radiogroup'),
                                v = radioGroup.getValue().dataType,
                                layout, fm, levels, status = false, label, serp;
                            layout = this.up('window').getLayout();

                            if(v == 'local') {
                                layout.next();
                            } else {
                                layout.setActiveItem(3);
                            }
                        }
                    }],
                    buttonAlign: 'right'
                }, { //3: 服务器归属地
                    xtype: 'panel',
                    autoScroll: true,
                    layout: 'fit',
                    //defaults: {anchor: '100%'},
                    items: [{
                        xtype: 'form',
                        bodyCls: 'banner',
                        id: 'serverConfig-panel',
                        border: false,
                        defaultType: 'fieldset',
                        defaults: {collapsible: false,margin: 10,border: false},
                        items: [{
                            sid: 'stype',
                            xtype: 'component',
                            border: false,
                            margin: '85 20 20 20',
                        }, {
                            title: '服务器归属地',
                            style: {backgroundPosition: '105px 1px'},
                            margin: 10,
                            defaultType: 'panel',
                            defaults: {height: 22, border: false,margin: '5 0 0 0'},
                            items: [{
                                defaultType: 'combo',
                                defaults: {emptyText: '-- 请选择 --',allowBlank: false, labelSeparator:''},
                                layout: 'column',
                                items: [{
                                    fieldLabel: '省',
                                    name: 'province',
                                    store: 'provinceStore',
                                    editable: false,
                                    queryMode: 'local',
                                    displayField: 'name',
                                    valueField: 'name',
                                    nextArea: 'city',
                                    columnWidth: 0.5,
                                    margin: '0 10 0 0'
                                }, {
                                    fieldLabel: '地市州',
                                    name: 'city',
                                    store: 'cityStore',
                                    editable: false,
                                    queryMode: 'local',
                                    displayField: 'name',
                                    valueField: 'name',
                                    nextArea: 'country',
                                    columnWidth: 0.5,
                                    margin: '0 0 0 10'
                                }]
                            }, {
                                defaultType: 'combo',
                                defaults: {emptyText: '-- 请选择 --',allowBlank: false, labelSeparator:''},
                                layout: 'column',
                                items: [{
                                    fieldLabel: '区县市',
                                    name: 'country',
                                    store: 'countryStore',
                                    editable: false,
                                    queryMode: 'local',
                                    displayField: 'name',
                                    valueField: 'name',
                                    nextArea: 'town',
                                    columnWidth: 0.5,
                                    margin: '0 10 0 0'
                                }, {
                                    fieldLabel: '街道乡镇',
                                    editable: false,
                                    name: 'town',
                                    store: 'townStore',
                                    queryMode: 'local',
                                    displayField: 'name',
                                    valueField: 'name',
                                    columnWidth: 0.5,
                                    margin: '0 0 0 10'
                                }]
                            }, {
                                defaultType: 'combo',
                                defaults: {emptyText: '-- 请选择 --', flex: 1, allowBlank: false, labelSeparator:''},
                                layout: {type: 'hbox', align: 'center'},
                                items: [{
                                    xtype: 'textfield',
                                    name: 'school_name',
                                    fieldLabel: '学校名称',
                                    emptyText: ''
                                }, {
                                    margin: '0 0 0 20',
                                    xtype: 'textfield',
                                    name: 'server_type',
                                    inputType: 'hidden'
                                }]
                            }]
                        }, {
                            xtype: 'fieldset',
                            id: 'server-port',
                            hideMode: 'visibility',
                            style: {backgroundPosition: '160px 1px'},
                            title: '填写服务器信息',
                            defaultType: 'textfield',
                            defaults: {allowBlank: false},
                            layout: {type:'hbox', pack:'left', align: 'top'},
                            items: [{
                                name: 'host',
                                fieldLabel: 'IP/域名',
                                labelSeparator:'',
                                //labelWidth: 60,
                                validator: function(v){
                                    var re = /(([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-z_!~*\'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6})/i;
                                    if(re.test(v)) {
                                        return true;
                                    }
                                    return "无效的IP/域名";
                                }
                            }, {
                                name: 'port',
                                value: '11111',
                                labelWidth: 10,
                                labelSeparator: '',
                                hidden: true,
                                fieldLabel: '&nbsp;:&nbsp;',
                                validator: function(v){
                                    var msg = '无效的端口号';
                                    if(!/^\d+$/.test(v)) { return msg; }
                                    v = parseInt(v);
                                    if(v >= 0 && v <= 65536) {
                                        return true;
                                    } else {
                                        return msg;
                                    }
                                }
                            }]
                        }, {
                            xtype: 'component',
                            id: 'domain-note',
                            hidden: true,
                            margin: '-10 0 0 20'
                        }]
                    }],
                    buttons: [{
                        text: '完成',
                        action: 'next',
                        handler: function(){
                            var me = this, fm = Ext.getCmp('serverConfig-panel'), msg;
                            msg = bbt.utils.checkForm(fm);
                            if(msg !== true) {
                                //Ext.Msg.alert('提示', msg);
                                return;
                            }
                            fm = fm.getForm();
                            is_school = bbt.server_type == "school";
                            fm.waitMsgTarget = me.up('window').getEl();
                            fm.submit({
                                url: '/install/serverinfo/',
                                waitMsg: '正在提交数据……',
                                timeout: 60000,
                                params: {install_step: 1},
                                success: function(form, action){
                                    if(action.result.status == "success") {
                                        if(bbt.server_type == "school" && me.onSubmitSuccess) {
                                            me.onSubmitSuccess();
                                        } else {
                                            Ext.Ajax.request({
                                                url: '/install/step/',
                                                params: {install_step: '-1'},
                                                success: function(){
                                                    location.pathname = '/';
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                },
                                failure: bbt.errorFn
                            });
                        }
                    }],
                    buttonAlign: 'right',
                    listeners: {
                        show: function(){
                            var levels, fm, status = false, schoolName, serp;
                            fm = this.down('form');
                            fm.down('textfield[name=server_type]').setValue(bbt.server_type);
                            levels = ['province', 'city', 'country', 'town'];
                            Ext.each(levels, function(level){
                                var combo = fm.down('combo[name=' + level + ']');
                                combo.setDisabled(status);
                                combo.allowBlank = status;
                                if(level == bbt.server_type) { status = !status; return; }
                            });
                            schoolName = fm.down('textfield[name=school_name]');
                            if(bbt.server_type == "school") {
                                //fm.down('combo[name=country]').allowBlank = true;
                                //fm.down('combo[name=town]').allowBlank = true;
                                schoolName.setDisabled(false);
                            } else {
                                schoolName.setDisabled(true);
                                //2014-12 新增需求
                                /*serp = Ext.getCmp('server-port');
                                Ext.each(serp.query('textfield'), function(f){
                                    f.allowBlank = true;
                                });
                                serp.hide();*/
                            }
                            Ext.each(fm.query('field[disabled=true]'), function(f){ f.hide(); });
                            //display server type
                            Ext.each(this.up('window').query('component[sid=stype]'), function(cmp){
                                cmp.getEl().setHTML('<span style="color: #22587a;">&gt;&gt;&nbsp;' + bbt.server_text + '</span>');
                            });
                        }
                    }
                }, /*{ //服务器基础信息导入
                    xtype: 'panel',
                    layout: 'anchor',
                    bodyCls: 'banner',
                    defaults: {anchor: '100%'},
                    items: [{
                            sid: 'stype',
                            xtype: 'component',
                            border: false,
                            margin: '85 20 20 20'
                    }, {
                        xtype: 'fieldset',
                        border: false,
                        title: '服务器基础信息导入',
                        style: {backgroundPosition: '140px 1px'},
                        margin: 20,
                        defaults: {border: false, layout: 'hbox', margin: '10 0 0 0'},
                        defaultType: 'panel',
                        header: false,
                        items: [{
                            items: [{
                                border: false,
                                html: '教职人员基础信息',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'form',
                                bodyCls: 'no-bg',
                                //width: 85,
                                height: 22,
                                border: false,
                                layout: 'card',
                                items: [{
                                    xtype : 'fileuploadfield',
                                    name : 'excel',
                                    buttonOnly : true,
                                    margin : 0,
                                    padding : 0,
                                    buttonConfig : {text : '导入'},
                                    listeners: {
                                        change: function(f, path){
                                            if(!/\.xlsx?$/.test(path)) {
                                                //Ext.Msg.alert('提示', '请选择 excel 文件！');
                                                return;
                                            }
                                            f.up('form').submit({
                                                url: bbt.importTeacherUrl,
                                                success: function(form, a){
                                                    var rst = a.result;
                                                    try {
                                                        if(rst.status == "success") {
                                                            //f.up('form').getLayout().next();
                                                            Ext.getCmp('import-2').setDisabled(false);
                                                            fixStyle(Ext.getCmp('import-2'));
                                                        }
                                                    } catch(e){}
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                }, {
                                    xtype: 'component',
                                    border: false,
                                    html: '<p class="import-success">OK！</p>'
                                }]
                            }, {
                                flex:1,
                                border: false
                            }]
                        }, {
                            items: [{
                                border: false,
                                html: '学校开课课程信息',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'form',
                                id: 'import-2',
                                //width: 85,
                                height: 22,
                                disabled: true,
                                bodyCls: 'no-bg',
                                layout: 'card',
                                border: false,
                                items: [{
                                    xtype : 'fileuploadfield',
                                    name : 'excel',
                                    buttonOnly : true,
                                    margin : 0,
                                    padding : 0,
                                    buttonConfig : {text : '导入'},
                                    listeners: {
                                        change: function(f, path){
                                            if(!/\.xlsx?$/.test(path)) {
                                                //Ext.Msg.alert('提示', '请选择 excel 文件！');
                                                return;
                                            }
                                            f.up('form').submit({
                                                url: bbt.importLessonUrl,
                                                success: function(form, a){
                                                    var rst = a.result;
                                                    try {
                                                        if(rst.status == "success") {
                                                            //f.up('form').getLayout().next();
                                                            Ext.getCmp('import-3').setDisabled(false);
                                                            fixStyle(Ext.getCmp('import-3'));
                                                        }
                                                    } catch(e){}
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                }, {
                                    xtype: 'component',
                                    border: false,
                                    html: '<p class="import-success">OK！</p>'
                                }]
                            }, {
                                flex:1,
                                border: false
                            }]
                        }, {
                            items: [{
                                border: false,
                                html: '学年学期信息',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'form',
                                bodyCls: 'no-bg',
                                //width: 85,
                                height: 22,
                                id: 'import-3',
                                disabled: true,
                                border: false,
                                layout: 'card',
                                items: [{
                                    xtype : 'fileuploadfield',
                                    name : 'excel',
                                    buttonOnly : true,
                                    margin : 0,
                                    padding : 0,
                                    buttonConfig : {text : '导入'},
                                    listeners: {
                                        change: function(f, path){
                                            if(!/\.xlsx?$/.test(path)) {
                                                //Ext.Msg.alert('提示', '请选择 excel 文件！');
                                                return;
                                            }
                                            f.up('form').submit({
                                                url: bbt.importTermUrl,
                                                success: function(form, a){
                                                    var rst = a.result;
                                                    try {
                                                        if(rst.status == "success") {
                                                            //f.up('form').getLayout().next();
                                                            Ext.getCmp('next-step-1').setDisabled(false);
                                                        }
                                                    } catch(e){}
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                }, {
                                    xtype: 'component',
                                    border: false,
                                    html: '<p class="import-success">OK！</p>'
                                }]
                            }, {
                                flex:1,
                                border: false
                            }]
                        }]
                    }],
                    buttons: [{
                        text: '下一步',
                        id: 'next-step-1',
                        disabled: true,
                        handler: function(){ this.up('window').getLayout().next(); }
                    }],
                    buttonAlign: 'right'
                }, { //当前学期基础信息导入
                    xtype: 'panel',
                    bodyCls: 'banner',
                    layout: 'anchor',
                    items: [{
                        sid: 'stype',
                        xtype: 'component',
                        border: false,
                        margin: '85 20 20 20'
                    }, {
                        xtype: 'fieldset',
                        title: '当前学期基础信息导入（可跳过）',
                        border: false,
                        style: {backgroundPosition: '220px 1px'},
                        defaults: {border: false, layout: 'hbox', margin: '10 0 0 0'},
                        defaultType: 'panel',
                        layout: 'vbox',
                        margin: 20,
                        anchor: '100%',
                        items: [{
                            items: [{
                                border: false,
                                html: '学期作息时间',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'form',
                                bodyCls: 'no-bg',
                                //width: 85,
                                height: 22,
                                border: false,
                                layout: 'card',
                                items: [{
                                    xtype : 'fileuploadfield',
                                    name : 'excel',
                                    buttonOnly : true,
                                    margin : 0,
                                    padding : 0,
                                    buttonConfig : {text : '导入'},
                                    listeners: {
                                        change: function(f, path){
                                            if(!/\.xlsx?$/.test(path)) {
                                                //Ext.Msg.alert('提示', '请选择 excel 文件！');
                                                return;
                                            }
                                            f.up('form').submit({
                                                url: bbt.importWorktimeUrl,
                                                success: function(form, a){
                                                    var rst = a.result;
                                                    try {
                                                        if(rst.status == "success") {
                                                            f.up('form').getLayout().next();
                                                            Ext.getCmp('import-4').setDisabled(false);
                                                            fixStyle(Ext.getCmp('import-4'));
                                                        }
                                                    } catch(e){}
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                }, {
                                    xtype: 'component',
                                    border: false,
                                    html: '<p class="import-success">OK！</p>'
                                }]
                            }, {
                                flex:1,
                                border: false
                            }]
                        }, {
                            items: [{
                                border: false,
                                html: '学期年级班级信息',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'form',
                                bodyCls: 'no-bg',
                                //width: 85,
                                height: 22,
                                id: 'import-4',
                                disabled: true,
                                border: false,
                                layout: 'card',
                                items: [{
                                    xtype : 'fileuploadfield',
                                    name : 'excel',
                                    buttonOnly : true,
                                    margin : 0,
                                    padding : 0,
                                    buttonConfig : {text : '导入'},
                                    listeners: {
                                        change: function(f, path){
                                            if(!/\.xlsx?$/.test(path)) {
                                                //Ext.Msg.alert('提示', '请选择 excel 文件！');
                                                return;
                                            }
                                            f.up('form').submit({
                                                url: bbt.importGradeClassUrl,
                                                success: function(form, a){
                                                    var rst = a.result;
                                                    try {
                                                        if(rst.status == "success") {
                                                            f.up('form').getLayout().next();
                                                            Ext.getCmp('import-5').setDisabled(false);
                                                            fixStyle(Ext.getCmp('import-5'));
                                                        }
                                                    } catch(e){}
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                }, {
                                    xtype: 'component',
                                    border: false,
                                    html: '<p class="import-success">OK！</p>'
                                }]
                            }, {
                                flex:1,
                                border: false
                            }]
                        }, {
                            items: [{
                                border: false,
                                html: '学期班级课程表',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'button',
                                text : '查看',
                                id: 'import-5',
                                disabled: true,
                                handler: function(){
                                    var c = {
                                        modal: true,
                                        width: 330,
                                        height: 360,
                                        title: '导入课程表',
                                        layout: 'fit',
                                        //closable: false,
                                        resizable: false,
                                        items: [{xtype: 'coursetable', border: false}]
                                    };
                                    new Ext.window.Window(c).show();
                                }
                            }, {
                                flex:1,
                                border: false
                            }]
                        }, {
                            items: [{
                                border: false,
                                html: '学期班级课程授课老师信息',
                                width: bbt.promptWidth
                            }, {
                                xtype: 'form',
                                bodyCls: 'no-bg',
                                //width: 85,
                                height: 22,
                                id: 'import-6',
                                disabled: true,
                                layout: 'card',
                                border: false,
                                items: [{
                                    xtype : 'fileuploadfield',
                                    name : 'excel',
                                    buttonOnly : true,
                                    margin : 0,
                                    padding : 0,
                                    buttonConfig : {text : '导入'},
                                    listeners: {
                                        change: function(f, path){
                                            if(!/\.xlsx?$/.test(path)) {
                                                //Ext.Msg.alert('提示', '请选择 excel 文件！');
                                                return;
                                            }
                                            f.up('form').submit({
                                                url: bbt.importTeachInfoUrl,
                                                params: {install_step: '-1'},
                                                success: function(form, a){
                                                    var rst = a.result;
                                                    try {
                                                        if(rst.status == "success") {
                                                            f.up('form').getLayout().next();
                                                            f.up('panel').down('button[action=next]').setEnabled(true);
                                                        }
                                                    } catch(e){}
                                                },
                                                failure: bbt.errorFn
                                            });
                                        }
                                    }
                                }, {
                                    xtype: 'component',
                                    border: false,
                                    html: '<p class="import-success">OK！</p>'
                                }]
                            }, {
                                flex:1,
                                border: false
                            }]
                        }]
                    }],
                    buttons: [{
                        text: '完成',
                        action: 'next',
                        handler: function(){
                            bbt.request({
                                url: '/install/step/',
                                params: {install_step: '-1'},
                                callback: function(opts, _, resp){
                                    var data;
                                    try {
                                        data = Ext.decode(resp.responseText);
                                        if(data.status == "success") {
                                            location.pathname = '/';
                                        }
                                    } catch(e){}
                                }
                            });
                        }
                    }],
                    buttonAlign: 'right'
                }, */{ //1: 输入上级服务器信息
                    xtype: 'panel',
                    autoScroll: true,
                    layout: 'fit',
                    //defaults: {anchor: '100%'},
                    items: [{
                        xtype: 'form',
                        bodyCls: 'banner',
                        border: false,
                        defaultType: 'fieldset',
                        defaults: {collapsible: false,margin: 10,border: false},
                        items: [{
                            sid: 'stype',
                            xtype: 'component',
                            border: false,
                            margin: '85 20 20 20'
                        }, {
                            title: '上级服务器信息',
                            style: {backgroundPosition: '110px 1px'},
                            defaultType: 'textfield',
                            defaults: {emptyText: '不可为空',allowBlank: false, labelSeparator:''},
                            margin: 10,
                            items: [{
                                xtype: 'panel',
                                border: false,
                                layout: 'hbox',
                                defaults: {emptyText: '不可为空',allowBlank: false, labelSeparator:''},
                                defaultType: 'textfield',
                                items: [{
                                    fieldLabel: 'IP/域名',
                                    name: 'host',
                                    width: 255,
                                    regex: /^(([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-z_!~*\'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6})$/i,
                                    regexText: '无效的 IP/域名'
                                }, {
                                    fieldLabel: ':',
                                    name: 'port',
                                    labelWidth: 8,
                                    width: 60,
                                    value: '11111',
                                    hidden: true,
                                    validator: function(v){
                                        var re = /^[1-9]\d*$/, msg = '无效的端口号', num;
                                        if(re.test(v)) {
                                            num = parseInt(v);
                                            if(num >= 0 && num <= 65535) {
                                                return true;
                                            }
                                        }
                                        return msg;
                                    }
                                }]
                            }, {
                                fieldLabel: '密钥',
                                width: 255,
                                margin: '10 0',
                                name: 'key',
                                regex: /^[0-9A-F]{16}$/,
                                regexText: '密钥格式错误，由数字和大写的A-F组成'
                            }, {
                                xtype: 'button',
                                text: '连接测试',
                                handler: function(){
                                    var me = this, fm = this.up('form'), msg;
                                    msg = bbt.utils.checkForm(fm);
                                    if(msg !== true) {
                                        //Ext.Msg.alert('提示', msg);
                                        return;
                                    }
                                    fm = fm.getForm();

                                    fm.waitMsgTarget = me.up('window').getEl();
                                    fm.submit({
                                        url: '/install/sync-server/verify/',
                                        waitMsg: '正在上传配置信息',
                                        timeout: 600000,
                                        success: function(form, action){
                                            if(action.result.status == "success") {
                                                Ext.Msg.alert('提示', '连接测试成功！');
                                            } else {

                                            }
                                        },
                                        failure: function(form, action){
                                            var msg = bbt.errorFn(form, action);
                                            if(!msg) Ext.Msg.alert('提示', '连接上级服务器失败！');
                                        }
                                    });
                                }
                            }]
                        }]
                    }],
                    buttons: [{
                        text: '完成',
                        action: 'next',
                        loop: function(){

                        },
                        handler: function(){
                            var me = this, fm = this.up('panel').down('form'), msg;
                            msg = bbt.utils.checkForm(fm);
                            if(msg !== true) {
                                //Ext.Msg.alert('提示', msg);
                                return;
                            }
                            fm = fm.getForm();

                            fm.waitMsgTarget = me.up('window').getEl();
                            fm.submit({
                                url: '/install/sync-server/set/',
                                waitMsg: '正在上传配置信息',
                                timeout: 600000,
                                params: {install_step: 1},
                                success: function(form, action){
                                    var data = action.result, layout, btn, values;
                                    values = form.getValues();
                                    if(data.status == "success") {
                                        if(bbt.server_type == "school") {
                                            layout = me.up('window').getLayout();
                                            layout.setActiveItem(2);
                                            btn = layout.getActiveItem().down('button[action=next]');
                                            btn.setText('完成');
                                            bbt.fillArea(layout.getActiveItem());
                                            if(data.data.has_records) {
                                                Ext.state.Manager.set('settings', values);
                                                btn.onSubmitSuccess = function(){ bbt.startDataTransfer(values); };
                                            }
                                        } else {
                                            Ext.state.Manager.set('settings', values);
                                            bbt.startDataTransfer(values);
                                        }
                                    }
                                },
                                failure: function(form, action){
                                    var msg = bbt.errorFn(form, action);
                                    if(!msg) Ext.Msg.alert('提示', '连接上级服务器失败！');
                                }
                            });

                        }
                    }],
                    buttonAlign: 'right'
                }]
            };
        }
    },
    boot: function(){
        this.installer.init();
        bbt.utils.setLoadMask();
        //Ext.onReady(test);
    },
    startDataTransfer: function(o){
        var ws = new BBTWebSocket('ws://' + o.host + ':' + o.port + '/ws/sync');
        ws.ready = function(){
            ws.request("remote-data", {key: o.key}, function(e, data){
                if(e) {
                    Ext.Msg.alert('提示', e.message || e);
                } else {
                    if(data.ret === 0) {
                        bbt.showSyncProgress(data.progress);
                    } else {
                        Ext.Msg.alert('提示', data.msg);
                    }
                }
            });
        };
        this.onDataTransferring(ws);
    },
    onDataTransferring: function(ws){
        var localWs = new BBTWebSocket('ws://' + location.hostname + ':8001/ws/localserver');;
        localWs['null'] = localWs['undefined'] = ws['null'] = ws['undefined'] = function(e, data){
            if(e) {
                Ext.Msg.alert('提示', e.message || e);
            } else {
                if(data.ret !== 0) {
                    Ext.Msg.alert('提示', data.msg);
                    return;
                }
                if(data.progress) {
                    bbt.showSyncProgress(data.progress);
                } else if(data.data || data.syllabus) {
                    bbt.showSyncProgress('数据回传完毕，请等待服务器配置！');
                    bbt.pingLocal(localWs, data.data);
                } else if(data.finished) {
                    location.pathname = "/";
                }
            }
        };
    },
    pingLocal: function(ws, data){
        var ping, senddata, pingTimer;
        ping = function(){
            ws.request('ping', {}, 'localserver', function(e, data){
                if(data && data.ret === 0 && data.operation == "pong") {
                    clearInterval(pingTimer);
                    senddata();
                }
            });
        };
        senddata = function(){
            ws.request('restore', data, 'localserver', function(e, data){
                if(data) {
                    if(data.finished) {
                        location.pathname = "/";
                    } else {
                        bbt.showSyncProgress(data.progress);
                    }
                } else {
                    bbt.showSyncProgress(e.message);
                }
            });
        };
        ping();
        pingTimer = setInterval(ping, 5000);
    },
    testLocalStatus: function(){
        var timer = setInterval(function(){
            Ext.Ajax.request({
                url: '/install/restore-status',
                method: 'GET',
                callback: function(_1, _2, resp){
                    var data = Ext.decode(resp.responseText);
                    if(data.finished) {
                        location.pathname = "/";
                    } else {
                        bbt.showSyncProgress(data.progress);
                    }
                }
            });
        }, 1000);
    },
    showSyncProgress: function(msg){
        Ext.Msg.progress('请勿刷新页面', '正在回传数据', msg);
    },
    fillArea: function(p){
        Ext.Ajax.request({
            url: '/install/sync-server/get-group/',
            callback: function(opts, _, resp){
                var data = Ext.decode(resp.responseText), area = {}, k, group, root, combo;
                if(data.status == "success") {
                    p.down('textfield[name=school_name]').setValue(data.data.school_name).setReadOnly(true);

                    if(data.data.town_name) {
                        p.down('[name=town]')._value = data.data.town_name;
                    }
                    Ext.each(data.data.records, function(item){
                        area[item.uuid] = {name: item.name, pid: item.parent_id, group_type: item.group_type};
                    });
                    for(k in area) {
                        group = area[k];
                        if(!group.pid) {
                            root = group;
                            continue;
                        }
                        area[group.pid].child = group;
                    }
                    group = root;
                    while(group) {
                        combo = p.down('combo[name=' + group.group_type + ']');
                        if(combo.store.count() > 0) {
                            combo.setValue(group.name);
                            combo.setReadOnly(true);
                        } else {
                            combo._value = group.name;
                        }

                        group = group.child;
                    }
                }
            }
        });
    },
    utils: {
        on: function(container, events){
            var selector, listeners;
            for(selector in events) {
                listeners = events[selector];
                Ext.each(container.query(selector), function(cmp){
                    cmp.on(listeners);
                });
            }
        },
        checkForm: function(form) {
            var bf = form.getForm(), isValid = true, msg;
            bf.getFields().each(function(f){
                if(!f.isValid()) {
                    msg = f.getFieldLabel() + '：' + f.getActiveError();
                    isValid = false;
                    return false;
                }
            });
            return msg || isValid;
        },
        getErrorMsg: function(data) {
            var k, msg = '';
            for(k in data) break;
            if(!k) {
                return "服务器错误！";
            }
            if(Ext.isArray(data.errors)) {
                data.errors = data.errors[0];
            }
            if(typeof data.errors == "object") {
                Ext.Object.each(data.errors, function(k, err){
                    if(typeof err == "string") {
                        msg += err;
                    } else if(Ext.isArray(err)) {
                        msg += err.join('<br/>');
                    }
                });
            }
            return msg || data.msg;
        },
        getIcon: function(panel, action){
            try {
                var icon = bbt.icons[panel][action];
                if(icon.charAt(0) != '/') {
                    icon = '/public/images/' + icon;
                }
                return icon;
            } catch(e) {}
            return bbt.icons.defaultIcon;
        },
        setLoadMask: function(){
            Ext.Ajax.on('requestcomplete', function(conn, options){
                try {
                    if(options.request.options.loadMaskId) {
                        var mask = bbt._loadmask[options.request.options.loadMaskId];
                        delete options.loadMaskId;
                        bbt.utils.destroyMask(mask);
                    }
                } catch (e) {}
            });
        },
        createMask: function(component, msg){
            var mask = new Ext.LoadMask(component, {msg:msg}),
                maskId = new Date().getTime() + '' + Math.random();
            bbt._loadmask[maskId] = mask;
            mask.show();
            return maskId;
        },
        destroyMask: function(mask){
            if(typeof mask == "string") {
                mask = bbt._loadmask[mask];
            }
            mask && mask.hide();
            mask.destroy && mask.destroy();
        },
        serializeStore: function(store, formatter) {
            var rc, i = 0, len = store.count(), fields, msg, data = {}, prefix;
            fields = store.model.getFields();
            formatter = formatter||{};
            for(;i<len;i++) {
                rc = store.getAt(i);
                if(typeof msg == "string") {
                    return msg;
                }
                prefix = 'form-' + i + '-';
                Ext.each(fields, function(f){
                    var name = f.name, v = rc.get(name);
                    if(name in formatter) { v = formatter[name](v); }
                    data[prefix + name] = v;
                });
            }
            data['form-TOTAL_FORMS'] = i;
            data['form-INITIAL_FORMS'] = 0;
            data['form-MAX_NUM_FORMS'] = '';
            return data;
        }
    },
    request: function(options){
        options = options || {};
        if(!options.url) { return; }
        Ext.Ajax.request(options);
    },
    _loadmask: {}
};
Ext.define('bbt.CourseTable', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.coursetable',
    store: new Ext.data.Store({fields: ['grade__name', 'name']}),
    bodyCls: 'import-schedule-grid',
    columns: {
        defaults: {sortable: false, menuDisabled: true, draggable: true},
        items: [{
            text: '年级',
            dataIndex: 'grade__name',
            renderer: function(v){ return v ? v + '年级' : '';}
        }, {
            text: '班级',
            dataIndex: 'name',
            renderer: function(v){ return v ? v + '班' : '';}
        }, {
            text: '操作',
            dataIndex: '_',
            renderer: function(v){
                if(v) { return v; }
                return '<form style="margin:0;padding:0;margin-top:1px;" method="POST"><div class="x-panel x-panel-default" style="margin: 0px; width: 38px; height: 22px; "><div class="x-panel-body no-bg x-panel-body-default x-panel-body-default x-docked-noborder-top x-docked-noborder-right x-docked-noborder-bottom x-docked-noborder-left" style="width: 38px; height: 22px; "><table class="x-field x-form-item x-field-default x-anchor-form-item x-form-readonly" style="padding: 0px; margin: 0px; border-width: 0px; table-layout: auto;" cellpadding="0"><tbody><tr><td style="display:none;" valign="top" halign="left" width="105" class="x-field-label-cell"><label for="filefield-1036-inputEl" class="x-form-item-label x-form-item-label-left" style="width:100px;margin-right:5px;"></label></td><td class="x-form-item-body x-form-file-wrap" colspan="3" role="presentation"><table class="x-form-trigger-wrap" cellpadding="0" cellspacing="0" style="table-layout: auto;"><tbody><tr><td class="x-form-trigger-input-cell" style="display: none;"><input type="text" name="" readonly="readonly" style="" class="x-form-field x-form-text  " autocomplete="off" aria-invalid="false" data-errorqtip=""></td><td style="width: 38px;"><div class="x-btn x-form-file-btn x-btn-default-small x-noicon x-btn-noicon x-btn-default-small-noicon" style="border-width:1px 1px 1px 1px;"><em><button type="button" class="x-btn-center" hidefocus="true" role="button" autocomplete="off"><span class="x-btn-inner" style="">导入</span><span class="x-btn-icon "></span></button></em><input class="x-form-file-input" type="file" size="1" name="excel"></div></td></tr></tbody></table></td></tr></tbody></table><div style="font-size: 1px; width: 1px; height: 1px; display: none;"></div></div></div></form>';
            }
        }]
    },
    tbar: ['->', {
        text: '完成',
        disabled: true,
        id: 'next-step-2',
        handler: function(){
            Ext.getCmp('import-5').setDisabled(true);
            this.up('window').destroy();
        }
    }],
    listeners: {
        viewready: function(){
            var me = this, mask = new Ext.LoadMask(me.up('window'), {msg: '正在导入课表'});
            mask.hide();
            bbt.request({
                url: '/install/grade_class/',
                success: function(resp){
                    var data = Ext.decode(resp.responseText);
                    me.store.loadData(data.data);
                },
                failure: bbt.errorFn
            });
            //bind input[type="file"] events
            setTimeout(function(){
                Ext.each(me.getEl().query('input[type="file"]'), function(ipt){
                    var el = Ext.get(ipt);
                    el.on('change', function(){
                        var form = el.up('form'), node = form.up('.x-grid-row');
                        node = me.getView().getRecord(node);
                        mask.show();
                        Ext.Ajax.upload(form,
                            bbt.importLessonScheduleUrl,
                            'grade_name='+node.get('grade__name')+'&class_name='+node.get('name'),
                            {
                                success: function(fm, action){
                                    mask.hide();
                                    Ext.getCmp('import-6').setDisabled(false);
                                    fixStyle(Ext.getCmp('import-6'));
                                    Ext.getCmp('next-step-2').setDisabled(false);
                                    el.up('.x-btn').addCls(['x-disabled', 'x-btn-disabled', 'x-btn-default-small-disabled']);
                                    el.clearListeners();
                                    try {
                                        var rc = me.getView().getRecord(el.up('.x-grid-row'));
                                        rc && rc.set('_', '<img src="/public/images/install/import_ok.png"/>');
                                        rc.commit();
                                    } catch(e) {}
                                },
                                failure: function(){
                                    mask.hide();
                                    bbt.errorFn.apply(this, arguments);
                                }
                            }
                        );
                    });
                });
            }, 100);

        }
    },
});

function fixStyle(fm){
    var btn = fm.getEl().down('.x-btn');
    try {
        btn.removeCls(['x-disabled', 'x-btn-disabled', 'x-btn-default-small-disabled']);
    } catch(e){}

}

bbt.boot();
function test(){
    var c = {
        modal: true,
        width: 350,
        height: 400,
        title: '导入课程表',
        layout: 'fit',
        items: [{xtype: 'coursetable', border: false}]
    };
    var win = new Ext.window.Window(c).show();
    win.down('grid').store.loadData([{grade__name: '一', name: '1'}, {grade__name: '一', name: '2'}]);
}
