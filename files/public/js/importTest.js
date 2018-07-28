(function(){
    var imports = [
        ['/system/teacher/verify/', '教职人员基础信息'],
        ['/system/lesson_name/verify/', '学校开课课程信息'],
        ['/system/term/verify/', '学年学期信息'],
        ['/system/lesson_period/verify/', '学期作息时间'],
        ['/system/class/verify/', '学期年级班级信息'],
        ['/system/lesson_schedule/verify/', '学期班级课程表'],
        ['/system/lesson_teacher/verify/', '班级课程授课教师']
    ];
    var largeTextAlert = function(title, msg){
        var start = 0, len = 30, loadonce, win, more, p, sc;
        loadonce = function(){
            var li, i, doc = document.createDocumentFragment();
            if(start >= msg.length) {
                more.setHTML("亲，没有更多了");
                more.clearListeners();
                return;
            }
            if((start + len) > msg.length) { len = msg.length - start; }
            for(i=0;i<len;i++) {
                li = document.createElement('li');
                li.innerHTML = msg[start+i];
                doc.appendChild(li);
            }
            start += len;
            more.prev('ul', true).appendChild(doc);
            p = more.parent().dom;
            sc =  p.scrollTop;
            win.down('panel').updateLayout();
            p.scrollTop = sc;
            win.center();
        };
        win = new Ext.window.Window({
            modal: true,
            autoShow: true,
            title: title,
            layout: 'fit',
            items: [{
                xtype: 'panel',
                border: false,
                autoScroll: true,
                bodyCls: 'no-bg',
                maxWidth: 750,
                maxHeight: 600,
                header: false,
                html: '<ul class="msg-list"></ul><a href="javascript:void(0);" class="more"><span></span> 查看更多</a>'
            }],
            buttons: [{text:'确定', handler: function(){
                this.up('window').destroy();
            }}],
            buttonAlign: 'center'
        });
        more = win.getEl().down('.more');
        more.on('click', loadonce);
        loadonce();
    };
    new Ext.window.Window({
        title: '导入测试',
        modal: true,
        autoShow: true,
        width: 350,
        height: 220,
        layout: 'fit',
        items: [{
            xtype: 'panel',
            bodyCls: 'no-bg',
            border: false,
            margin: 30,
            layout: 'anchor',
            defaults: {anchor: '100%'},
            items: [{
                xtype: 'combo',
                fieldLabel: '验证项',
                editable: false,
                name: 'importUrl',
                store: imports,
                value: '/system/teacher/verify/'
            }, {
                xtype: 'form',
                bodyCls: 'no-bg',
                border: false,
                items: [{
                    xtype : 'fileuploadfield',
                    name : 'excel',
                    allowBlank: false,
                    margin : 0,
                    padding : 0,
                    fieldLabel: '选择文件',
                    buttonText: '...',
                    listeners: {
                        change: function(f, path){
                            if(!/\.xlsx?$/.test(path)) {
                                Ext.Msg.alert('提示', '请选择 excel 文件！');
                                f.reset();
                                return;
                            }
                        }
                    }
                }]
            }]
        }],
        buttons: [{text: '验证', handler: function(){
            var p = this.up('window').down('panel'), uc, f, cb;
            uc = p.down('[name=importUrl]');
            if(!uc.getValue()) {
                Ext.Msg.alert('提示', '请选择验证项！');
                return;
            }
            f = p.down('form');
            if(!f.down('[name=excel]').getValue()) {
                Ext.Msg.alert('提示', '请选择 excel 文件！');
                return;
            }
            cb = function(fm, action){
                var data = action.result, errors = [];
                if(data.status == "success") {
                    Ext.each(data.data.records, function(row){
                        errors.push('第' + row.row + '行有错：' + row.error);
                    });
                    largeTextAlert('出问题啦！', errors);
                } else {
                    Ext.Msg.alert('提示', data.msg||'未意料的错误！');
                }
            };
            f.getForm().waitTarget = p.up('window');
            f.submit({
                waitMsg: '正在上传文件……',
                url: uc.getValue(),
                success: cb,
                failure: cb
            });
        }}],
        buttonAlign: 'center'
    });
})();