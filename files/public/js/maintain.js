Ext.define('LogPanel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.log',
    autoScroll: true,
    tbar: [{
        xtype: 'combo',
        fieldLabel: '日志类型',
        editable: false,
        name: 'log_type',
        store: [['1', 'debug'], ['2', 'error'], ['3', 'setting']],
        value: '2'
    }, '->', {text: '下载', action: 'download'}],
    title: '查看日志',
    html: '<div class="log-list"></div>',
    listeners: {
        afterrender: function(){
            var tb = this.down('toolbar[dock=top]');
            this.loadLogs(2);
            tb.down('[action=download]').setHandler(this.downloadLog, this);
            tb.down('[name=log_type]').on('change', function(_, v){
                this.up('log').loadLogs(v);
            });
        },
    },
    downloadLog: function(){
        Ext.Ajax.request({
            url: '/maintain/log/download/',
            callback: function(opts, _, resp) {
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    bbt_mt.downloadFile(data.url, '');
                } else {
                    Ext.Msg.alert('错误', data.msg);
                }
            }
        });
    },
    loadLogs: function(type){
        var me = this, mask, exceptCB;
        mask = me.setLoading();
        Ext.Ajax.request({
            url: '/maintain/log/?log_type='+type,
            callback: function(opts, _, resp){
                var data = Ext.decode(resp.responseText), loglist;
                if(data.status == "success") {
                    var doc = document.createDocumentFragment();
                    Ext.each(data.data.lines, function(line){
                        var p = document.createElement('p');
                        p.innerHTML = line;
                        doc.appendChild(p);
                    });
                    loglist = me.getEl().down('.log-list', true);
                    loglist.innerHTML = '';
                    loglist.appendChild(doc);
                }
                exceptCB();
            }
        });
        exceptCB = function(){
            mask.hide();
            mask = null;
            Ext.Ajax.un('requestexception', exceptCB);
        };
        Ext.Ajax.on('requestexception', exceptCB);
    }
});
/* 网络诊断 */
Ext.define('NetworkPanel', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.network',
    columns: [{
        text: 'IP地址',
        width: 160,
        dataIndex: 'address'
    }, {
        text: '请求方式',
        dataIndex: 'method'
    }, {
        text: '状态',
        dataIndex: 'status'
    }],
    tbar: [{xtype: 'button', text: '开始测试'}],
    listeners: {
        afterrender: function(){
            this.down('toolbar').down('button').setHandler(function(){
                this.store.load();
            }, this);
        }
    },
    title: '网络诊断',
    initComponent: function(){
        var store = new Ext.data.Store({
            autoLoad: false,
            fields: ['address', 'status', 'method'],
            proxy: {
                url: '/maintain/desktop-preview/network-diagnose/',
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            }
        });
        this.store = store;
        this.callParent();
    }
});

var bbt_mt = {
    init: function(){
        var config = new Ext.container.Viewport({
            padding: 5,
            layout: 'border',
            items: [{
                region: 'west',
                xtype: 'panel',
                title: '菜单',
                collapsible: true,
                split: true,
                width: 220,
                items: [{
                    xtype: 'boundlist',
                    border: false,
                    displayField: 'text',
                    valueField: 'value',
                    store: new Ext.data.Store({fields:['text','value'], data:[{text: '查看日志', value:'log'}, {text: '网络诊断', value: 'network'}]}),
                    listeners: {
                        itemclick: function(v, rc, el){
                            var tc = Ext.getCmp('content-panel'), p;
                            p = tc.down(rc.get('value'));
                            if(p) {
                                tc.setActiveTab(p);
                                return;
                            }
                            p = bbt_mt.findPanel(rc.get('value'));
                            if(p){
                                p = tc.add(p);
                                tc.setActiveTab(p);
                            }
                        }
                    }
                }]
            }, {
                region: 'center',
                xtype: 'tabpanel',
                id: 'content-panel',
                items: [{
                    xtype: 'panel',
                    title: '当前信息',
                    closable: false,
                    autoScroll: true,
                    html: '<pre></pre>',
                    listeners: {
                        afterrender: function(){
                            var el = this.getEl().down('pre');
                            Ext.Ajax.request({
                                url: '/maintain/info/',
                                callback: function(opts, _, resp){
                                    var data = Ext.decode(resp.responseText);
                                    if(data.status == "success") {
                                        el.setHTML(JSON.stringify(data.data, null, '    '));
                                    } else {
                                        el.setHTML(data.msg);
                                    }
                                }
                            })
                        }
                    }
                }]
            }]
        });
    },
    findPanel: function(t){
        return {xtype: t, closable: true};
    },
    downloadFile: function(url, name) {
    Ext.create('Ext.window.Window', {
        title: '下载文件',
        modal: true,
        width: 240,
        height: 120,
        layout: {type: 'vbox', pack: 'center', align: 'center'},
        items: [{
            html: '点击下面的按钮下载' + name + '！',
            bodyCls: 'no-bg',
            border: false,
            margin: 20
        }, {
            xtype: 'button',
            text: '确定',
            href: url,
            margin: '-5 0 0 0',
            handler: function(){
                var win = this.up('window');
                win.destroy();
            }
        }]
    }).show();
}

};
bbt_mt.init();