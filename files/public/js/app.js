/*jshint sub:false,expr:true*/
var bbt = {
    version: '20140704',
    loadScript: function(){
        var scripts = ['/public/js/app2.js', '/public/js/'+bbt.UserInfo.level+'Config.js'],
            i, len, el, query = location.search, parts, obj = {}, r = /^true|1|yes$/;

        //scan extensions
        if(query.length) {
            query = query.substring(1);
            parts = query.split('&');
            Ext.each(parts, function(p){
                var pair = p.split('=');
                obj[pair[0]] = pair[1];
            });
        }
        if(r.test(obj.tester)) {
            scripts.push('/public/js/performenceTest.js');
        }
        if(r.test(obj.importTest)) {
            scripts.push('/public/js/importTest.js');
        }
        for(i=0,len=scripts.length;i<len;i++) {
            el = document.createElement('script');
            el.type = 'text/javascript';
            el.src = scripts[i]/* + '?v=' + this.version*/;
            document.body.appendChild(el);
        }
    },
    loadGroup: function(cb){
        Ext.Ajax.request({url: '/group/', success: function(resp){
            var data, root, groups = {}, uuid, g, gp, levelData;
            try {
                data = Ext.decode(resp.responseText);
            } catch(e) { data = {}; }
            if(data.status == "success") {
                data = data.data;
                Ext.each(data.group, function(group){
                    groups[group.uuid] = group;
                    if(!group.parent__uuid) {
                        root = group;
                    }
                });
                for(uuid in groups) {
                    g = groups[uuid];
                    if(g === root) { continue; }
                    gp = groups[g.parent__uuid];
                    if(!gp.children) {
                        gp.children = [];
                    }
                    gp.children.push(g);
                }
                levelData = root;
                while(levelData.group_type != bbt.UserInfo.level) {
                    Ext.getStore(levelData.group_type+'Store').add(levelData);
                    levelData = levelData.children;
                    if(Ext.isArray(levelData) && levelData.length !== 0) {
                        levelData = levelData[0];
                    } else {
                        break;
                    }
                }
                Ext.getStore(levelData.group_type + 'Store').add(levelData);
            }
        }});
    },
    loadClasses: function(cb){
        if(typeof cb !== "function") { cb([]); return; }
        Ext.Ajax.request({
            url: '/classes/',
            callback: function(opts, _, resp){
                var data = Ext.decode(resp.responseText),
                    grades = {}, ret = [], obj, i, len, rcs, g;
                if(data.status !== "success") { cb([]); return; }
                for(i=0,len=data.data.length;i<len;i++) {
                    obj = data.data[i];
                    if(!(obj.grade__name in grades)) {
                        grades[obj.grade__name] = [];
                    }
                    grades[obj.grade__name].push({text: obj.name, value: obj.name});
                }
                for(g in grades) {
                    ret.push({text: g/*, fulltext: bbt.fullgrade(g)*/, value: g, sub: grades[g]});
                }
                cb(ret);
            }
        });
    },
    loadCurrentSchoolYear: function(cb){
        Ext.Ajax.request({
            url: '/system/term/current-or-next/',
            callback: cb
        });
    },
    loadTermCompareData: function(url, params, cb){
        var dataIndex = url.indexOf('total-time') === -1 ? "lesson_count" : "total_time";
        params = params || {};
        Ext.Ajax.request({
            url: url,
            method: 'GET',
            params: params,
            callback: function(options, _, resp){
                var data, map, ret, ret2, week, v, sum, i, maxNum;
                try {
                    data = Ext.decode(resp.responseText);
                    if(data.status == "success") { data = data.data; }
                } catch (e) {}
                if(!data) { cb && cb([], []); return; }
                map = {};
                maxNum = Math.max(
                    data.term ? data.term.length : 0,
                    data.term_previous ? data.term_previous.length : 0,
                    data.term_lastyear ? data.term_lastyear.length : 0,
                    20);
                if(data.term) {
                    sum = 0;
                    Ext.each(data.term, function(item){
                        var key = item.week + '',
                            value = item[dataIndex];
                        if(dataIndex == "total_time") {
                            value = Math.floor(value / 60);
                        }

                        if(!(key in map)) {
                            map[key] = [];
                        }
                        map[key][0] = value;
                        sum += value;
                        map[key][3] = sum;
                    });
                }
                if(data.term_previous) {
                    sum = 0;
                    Ext.each(data.term_previous, function(item){
                        var key = item.week + '',
                            value = item[dataIndex];
                        if(dataIndex == "total_time") {
                            value = Math.floor(value / 60);
                        }
                        if(!(key in map)) {
                            map[key] = [];
                        }
                        map[key][1] = value;
                        sum += value;
                        map[key][4] = sum;
                    });
                }
                if(data.term_lastyear) {
                    sum = 0;
                    Ext.each(data.term_lastyear, function(item){
                        var key = item.week + '',
                            value = item[dataIndex];
                        if(dataIndex == "total_time") {
                            value = Math.floor(value / 60);
                        }
                        if(!(key in map)) {
                            map[key] = [];
                        }
                        map[key][2] = value;
                        sum += value;
                        map[key][5] = sum;
                    });
                }
                ret = [];
                ret2 = [];
                for(week=1;week<=maxNum;week++) {
                    v = map[week+''];
                    if(v) {
                        ret.push({
                            data1: typeof v[0] == "number" ? v[0] : '',
                            data2: typeof v[1] == "number" ? v[1] : '',
                            data3: typeof v[2] == "number" ? v[2] : '',
                            name: week
                        });
                        ret2.push({
                            data1: typeof v[3] == "number" ? v[3] : '',
                            data2: typeof v[4] == "number" ? v[4] : '',
                            data3: typeof v[5] == "number" ? v[5] : '',
                            name: week
                        });
                    } else {
                        ret.push({name: week});
                        ret2.push({name: week});
                    }

                }
                /*for(week in map) {
                    v = map[week];
                    ret.push({
                        data1: v[0],
                        data2: hasPrev ? v[1] : 0,
                        data3: hasLast ? v[2] : 0,
                        name: week
                    });
                    ret2.push({
                        data1: v[3],
                        data2: hasPrev ? v[4] : 0,
                        data3: hasLast ? v[5] : 0,
                        name: week
                    });
                }
                for(week=ret.length+1;week<=maxNum;week++) {
                    ret.push({name: week});
                    ret2.push({name: week});
                }*/
                cb && cb(ret, ret2);
            }
        });
    },
    loadSchoolCascadeData: function(p){
        var names = ['grade_name', 'lesson_period', 'lesson_name'];
        Ext.each(names, function(name){
            var combo = p.down('[name=' + name + ']');
            combo && combo.store.load();
        });
    },
    beforeCascadeLoad: function(){
        var params = this.proxy.extraParams, p = this.owner.up('grid'), tmp, valid;
        //班班通授课综合分析界面需要特殊处理
        if(!p) {
            p = this.owner.up('toolbar');
        }
        if(this.owner.computerclass) {
            params.computerclass_need = true;
        }
        if(this.owner.only_computerclass) {
            params.only_computerclass = true;
        }
        //find combo <name>start_date</name>
        tmp = p.down('[name=start_date]');
        if(tmp) {
            tmp = tmp.getValue();
            tmp = Ext.isDate(tmp) ? Ext.Date.format(tmp, 'Y-m-d') : '';
            params.start_date = tmp;
        }
        //find combo <name>end_date</name>
        tmp = p.down('[name=end_date]');
        if(tmp) {
            tmp = tmp.getValue();
            tmp = Ext.isDate(tmp) ? Ext.Date.format(tmp, 'Y-m-d') : '';
            params.end_date = tmp;
        }
        //find combo <name>school_year</name>
        tmp = p.down('[name=school_year]');
        if(tmp) {
            params.school_year = tmp.getValue();
        }
        //find combo <name>term_type</name>
        tmp = p.down('[name=term_type]');
        if(tmp) {
            params.term_type = tmp.getValue();
        }
        //set current combo's value
        tmp = {};
        tmp[this.owner.displayField] = '所有';
        this.loadData([tmp]);
        this.owner.setValue('');
        //only valid if is not school server
        if(!bbt.UserInfo.isSchool()) {
            valid = true;
            try {
                tmp = p.down('[name=school_name]');
                tmp = tmp.findRecordByValue(tmp.getValue());
                tmp = tmp.raw.uuid;
                params.uuid = tmp;
            } catch(e) {
                valid = false;
            }
            if(!valid || !params.uuid) {
                return false;
            }
        }
    },
    autoArea: function(widget){
        if(!bbt.UserInfo.isSchool()) {
            widget.on('afterrender', function(){
                var levels = ['province', 'city', 'country', 'town', 'school'], i, data, store;
                i = Ext.Array.indexOf(levels, bbt.UserInfo.level);
                data = Ext.getStore(levels[i++]+'Store').getAt(0).get('children');

                store = Ext.getStore(levels[i]+'Store');
                store.add(data);
                store.fireEvent('load', store);
            });
            widget.on('beforedestroy', function(){
                var levels = ['province', 'city', 'country', 'town', 'school'], i, len, store;
                i = Ext.Array.indexOf(levels, bbt.UserInfo.level);
                for(i=i+1,len=levels.length;i<len;i++) {
                    store = Ext.getStore(levels[i] + 'Store');
                    store.removeAll();
                }
            });
        }
    },
    autoFill2: function(panel){
        var eventName, tbar, comboes = [];
        if(panel.is('panel')) {
            eventName = "afterlayout";
        } else if(panel.is('grid')) {
            eventName = "viewready";
        } else {
            return;
        }
        tbar = panel.query('toolbar[dock=top]');
        Ext.each(tbar, function(t){
            var c = t.query('combo');
            if(c && c.length){
                comboes = comboes.concat(c);
            }
        });
        panel.on(eventName, function(){
            Ext.each(comboes, function(f){
                var dantengCB = function(){
                    f.setValue('');
                    f.store.un('load', dantengCB);
                };
                if(f.store.isLoading()) {
                    f.store.on('load', dantengCB);
                } else {
                    !f.getValue() && f.setValue('');
                }
            });
        });

    },
    autoFill: function(widget){
        return;
        Ext.each(widget.is('grid')?[widget]:widget.query('grid'), function(w_g){
            w_g.on('viewready', function(){
                var comboes = [], tb = this.query('toolbar[dock=top]');
                Ext.each(tb, function(t){
                    var c = t.query('combo');
                    if(c && c.length){
                        comboes = comboes.concat(c);
                    }
                });
                Ext.each(comboes, function(f){
                    var dantengCB;
                    if(f.skipAutoValue) { f.store.load(); }
                    dantengCB = function(){
                        !f.getValue() && f.setValue('');
                        f.store.un('load', dantengCB);
                    };
                    if(f.store.isLoading() && !f.getValue()) {
                        f.store.on('load', dantengCB);
                    } else {
                        !f.getValue() && f.setValue('');
                    }
                });
            });
        });
    },
    getUPYunImageUrl: function(url, params){
        var param;
        if(params) {
            params = Ext.Object.toQueryString(params);
            if(params) { params = '?' + params; }
            else { params = ''; }
        } else {
            params = '';
        }
        return "http://oe-test1.b0.upaiyun.com" + url + params;
    },
    fullgrade: function(grade){
        if('一二三四五六'.indexOf(grade) != -1) {
            return grade + '年级（小学）';
        } else if('七八九'.indexOf(grade) != -1) {
            return grade + '年级（初中）';
        } else if('十一十二'.indexOf(grade) != -1) {
            return grade + '年级（高中）';
        } else {
            return grade;
        }
    },
    createOverlay: function(zIndex){
        var div = document.createElement('div'),
            close = document.createElement('a');
        zIndex || (zIndex = 10);
        div.style.cssText = "position:absolute;top:0;left:0;bottom:0;right:0;background-color: #000;opacity: 0.5;filter:alpha(opacity=50);z-index:"+zIndex;
        close.className = "close-trigger";
        close.style.cssText = "z-index:10000;";
        close.href = "javascript:void(0);";
        close.setAttribute("data-role", "overlay");

        document.body.appendChild(div);
        document.body.appendChild(close);

        close.$closeTarget = div;
        Ext.get(close).on('click', function(e, a){
            var node = a.$closeTarget;
            node.onBeforeDestroy && node.onBeforeDestroy(node);
            Ext.removeNode(node);
            Ext.removeNode(a);
        });
        return div;
    },
    destroyWindow: function(win){
        var box = win.getBox();
        win.animate({
            duration: 200,
            to: {
                width: '100px',
                height: '100px',
                x: box.x + (box.width - 100) / 2,
                y: box.y + (box.height - 100) / 2
            },
            callback: function(){
                win.destroy();
                win = null;
            }
        });
    },
    getLevelTools: function(level){
        var levels = ['province', 'city', 'country', 'town', 'school'], pos;
        if(!level) {
            level = bbt.UserInfo.level;
        }
        pos = Ext.Array.indexOf(levels, level);
        if(pos != -1) {
            return Ext.Array.slice(levels, pos+1);
        }
        return [];
    },
    simulateClick: function(el){
        var evt;
        if(Ext.isIE && Ext.ieVersion < 9) {
            evt = document.createEventObject();
            evt.button = 0;
            evt.ctrlKey = false;
            evt.altKey = false;
            evt.shiftKey = false;
            el.fireEvent('onclick', evt);
        } else {
            evt = document.createEvent("MouseEvents");
            evt.initMouseEvent("click", true, true);
            el.dispatchEvent(evt);
        }
    },
    utils: {
        strftime: function(d){
            if(typeof d == "string") { return d; }
            else if(Ext.isDate(d)) {
                return d.getFullYear() + '-' + (d.getMonth()+1) + '-' + d.getDate();
            }
        },
        toDate: function(timestr){
            var dates, times, parts, d;
            if(timestr.indexOf(' ') !== -1) {
                parts = timestr.split(' ');
                dates = parts[0].split('-');
                times = parts[1].split(':');
            } else {
                dates = timestr.split('-');
            }
            d = new Date();
            if(dates.length === 3) {
                d.setFullYear(parseInt(dates[0]));
                d.setMonth(parseInt(dates[1])-1);
                d.setDate(parseInt(dates[2]));
            }
            if(times && times.length > 1) {
                d.setHours(parseInt(times[0]));
                d.setMinutes(parseInt(times[1]));
                d.setSeconds(parseInt(times[2])||0);
            }
            return d;
        },
        makeTipFor: function(tip, obj){
            Ext.create('Ext.tip.ToolTip', {
                target: obj,
                html: tip
            });
        },
        parseGroupData: function(data){
            var root, groups = {}, uuid, g, gp, levelData;
            Ext.each(data.group, function(group){
                groups[group.uuid] = group;
                group.children = [];
            });

            Ext.each(data.grade, function(grade){
                var school = groups[grade.term__school__uuid];
                if(!school.children) {
                    school.children = [];
                }
                grade.leaf = true;
                grade.text = grade.name + '年级';
                grade.group_type = 'grade';
                school.children.push(grade);
            });
            for(uuid in groups) {
                g = groups[uuid];
                g.leaf = false;
                g.expanded = true;
                g.text = g.name;

                if(!g.parent__uuid) { root = g; continue; }
                gp = groups[g.parent__uuid];
                gp.children.push(g);
            }
            return root;
        },
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

Ext.define('bbt.UserInfo', {
    singleton: true,
    _amap: function(arr){
        var ret = {}, i, len;
        for(i=0,len=arr.length;i<len;i++) {
            ret[arr[i]] = true;
        }
        return ret;
    },
    _isloading: false,
    isReady: function(){
        return !!this._ready;
    },
    isSchool: function(){
        if(this.isReady()) {
            return this.level == "school";
        }
        return false;
    },
    update: function(callback){
        var me = this;

        if(me._isloading) { return; }
        Ext.Ajax.request({
            url: '/details/',
            callback: function(opts, _, resp){
                var data, userdata, suc = false;
                try {
                    data = Ext.decode(resp.responseText)||{};
                    if(data.status == "success") {
                        if(me._lastResponseText != resp.responseText) {
                            me._lastResponseText = resp.responseText;
                            data = data.data;
                            userdata = {};
                            userdata.privileges = me._amap(data.privileges);
                            userdata.permitted_groups = me._amap(data.permitted_groups);
                            me.userdata = userdata;
                            Ext.apply(me, data);
                            suc = true;
                            me._ready = true;
                        }
                    }
                } catch (e) {}
                finally {
                    callback && callback(suc);
                    me._isloading = false;
                }

            }
        });
        me._isloading = true;
    },
    isGroup: function(g){
        try {
            if(me.superuser) {
                return true;
            } else {
                return g in this.userdata.privileges;
            }
        } catch (e) {
            return false;
        }
    },
    hasPrivilege: function(name){
        var me = this;
        try {
            if(me.superuser) {
                return true;
            } else {
                return name in me.userdata.privileges;
            }
        } catch (e) {
            return false;
        }

    }
});


//boot
(function(){
    Ext.Ajax.timeout = 10 * 60000;
    Ext.data.proxy.Ajax.prototype.timeout = 10 * 60000;
    var boot = {
        privileges: null,
        isSchoolServer: function(){
            var type = Ext.get(document.getElementById('bbt-server-info')).down('span').getHTML();
            return Ext.String.trim(type) == "school";
        },
        login: function(){
            var win = Ext.create('Ext.window.Window', {
                baseCls: '',
                width: '100%',
                height: '100%',
                minHeight: 450,
                minWidth: 800,
                layout: {type: 'hbox', align: 'stretch'},
                padding: 0,
                margin: 0,
                bodyCls: 'login-win',
                header: false,
                shadow: false,
                border: false,
                closable: false,
                resizable: false,
                items: [{
                    xtype: 'panel',
                    border: false,
                    bodyCls: 'no-bg',
                    html: '<div class="download-client"><p><img src="/public/images/login/title.png"/></p>' + '<p class="btns"><a class="' + (this.isSchoolServer() ? 'school' : 'country') + '-download" href="/download/client.zip"></a></p></div>',
                    flex: 1,
                    listeners: {
                        afterrender: function(){
                            var p = this.el.down('.btns', true), show = Ext.util.Cookies.get('show_download_btn');
                            p.style.display = (show === "true" ? "block" : "none");
                        }
                    }
                }, {
                    xtype: 'form',
                    bodyCls: 'login-form-bg',
                    width: 392,
                    height: 340,
                    flex: 1,
                    margin: 0,
                    padding: 0,
                    border: false,
                    layout: 'absolute',
                    defaultType: 'textfield',
                    defaults: {height:30, allowBlank: false, enableKeyEvents: true, width: 220},
                    items: [{
                        name: 'username',
                        emptyText: '      请输入用户名',
                        fieldBodyCls: 'login-user',
                        listeners: {
                            focus: function(){ if(!this.getValue()){this.addCls('login-user-hover');} },
                            blur: function(){ if(!this.getValue()){this.removeCls('login-user-hover');} }
                        }
                    }, {
                        name: 'password',
                        inputType: 'password',
                        hidden: Ext.isIE,
                        emptyText: '      请输入密码',
                        fieldBodyCls: 'login-password',
                        listeners: {
                            focus: function(){ if(!this.getValue()){this.addCls('login-password-hover');} },
                            blur: function(){
                                if(!this.getValue()){
                                    this.removeCls('login-password-hover');
                                    if(Ext.isIE) {
                                        this.hide();
                                        this.up('form').down('[name=_]').show();
                                    }
                                }
                            }
                        }
                    }, {
                        name: '_',
                        emptyText: '      请输入密码',
                        readOnly: true,
                        hidden: !Ext.isIE,
                        allowBlank: true,
                        fieldBodyCls: 'login-password',
                        listeners: {
                            focus: function(){
                                var real = this.up('form').down('[name=password]');
                                this.hide();
                                real.show();
                                real.focus();
                            },
                            show: function(){
                                if(this.isDisabled()) {
                                    this.setDisabled(false);
                                }
                            }
                        }
                    }, {
                        xtype: 'button',
                        text: '登  录',
                        cls: 'login-submit',
                        overCls: 'login-submit-hover',
                        border: false,
                        width: 98,
                        height: 28,
                        handler: function(){
                            var form = this.up('form');
                            doLogin(form);
                        }
                    }]
                }],
                listeners: {
                    afterrender: function(){
                        var me = this, img = document.createElement('img');
                        img.src = '/public/images/login/login.jpg';
                        me.getEl().down('.x-box-inner').insertFirst(img);
                        Ext.get(img).setSize(me.getWidth(), me.getHeight());
                        me.on('resize', function(){
                            var h = me.getHeight(), mt, fm, wf;
                            Ext.get(img).setSize(me.getWidth(), h);
                            mt = Math.round(h*180/811 - (340 - h*278/811)/2);
                            if(mt < 0) { mt = 0; }

                            me.down('panel').setBodyStyle('marginTop', h*180/811+'px');
                            fm = me.down('form');
                            fm.setBodyStyle('marginTop', mt+'px');
                            wf = fm.getWidth();
                            fm.down('textfield[name=username]').setPosition((wf-392)/2+86, 90);
                            fm.down('textfield[name=password]').setPosition((wf-392)/2+86, 140);
                            fm.down('textfield[name=_]').setPosition((wf-392)/2+86, 140);
                            fm.down('button').setPosition((wf-392)/2+306-98, 210);
                        });
                        me.on('beforedestroy', function(){
                            img && img.parentNode.removeChild(img);
                            img = null;
                        });
                        Ext.get(window).on('resize', function(){
                            me.updateLayout();
                        });
                    }
                }
            }).show();
            new Ext.util.KeyMap({
                target: win.down('form').getEl(),
                key: 13,
                fn: function(){
                    var fm = Ext.getCmp(this.target.dom.id);
                    doLogin(fm);
                }
            });
            function doLogin(form) {
                var msg, win = form.up('window');
                msg = checkForm(form);
                if(msg !== true) {
                    Ext.Msg.alert('提示', '用户名或密码不可为空！');
                    return;
                }
                if(doLogin.wait) { return; }
                form.down('[name=_]').setDisabled(true);
                form.getForm().submit({
                    url: '/login/',
                    method: 'POST',
                    success: function(form, action){
                        var data = action.result;
                        if(data.status == "success") {
                            win.destroy();
                            boot.buildUI();
                        }
                        delete doLogin.wait;
                    },
                    failure: function(_, action){
                        var k, data = action.result, errorMsg=[data.msg];
                        for(k in data.errors) {
                            errorMsg = errorMsg.concat(data.errors[k]);
                        }
                        Ext.Msg.alert('提示', errorMsg.join('<br/>'));
                        delete doLogin.wait;
                    }
                });
                doLogin.wait = true;
            }
        },
        init: function(cb){

            bbt.login = true;

            Ext.onReady(function () {
                var p = document.getElementById('bbt-server-info');
                p.parentNode.removeChild(p);
                new Ext.container.Viewport({
                    layout: 'border',
                    padding: 5,
                    items: [
                        {
                            region: 'north',
                            xtype: 'toolbar',
                            margin: '0 0 5 0',
                            id: 'app-toolbar'
                        },
                        {
                            region: 'west',
                            xtype: 'treepanel',
                            bodyCls: 'func-menu',
                            title: '主菜单',
                            id: 'app-menu',
                            width: 220,
                            split: true,
                            collapsible: true,
                            overflowY: 'auto',
                            rootVisible: false
                        },
                        {
                            region: 'center',
                            xtype: 'panel',
                            defaults: {border: false},
                            id: 'content-panel',
                            layout: 'fit',
                            items: []
                        }
                    ]
                });
                Ext.Ajax.on('beforerequest', function(conn, opts){
                    try {
                        //lower case sort direction
                        if(opts.params && opts.params.order_direction) {
                            opts.params.order_direction = opts.params.order_direction.toLowerCase();
                        }
                    } catch (e) {}
                });
                bbt.loadScript();

                cb && cb();
                //全局 ajax 完成回调检测
                Ext.Ajax.on('requestcomplete', function(con, resp){
                    var data = Ext.decode(resp.responseText), url;
                    if(data.status == "not login") {
                        Ext.Msg.alert('提示', '登录失败！', function(b){
                            location.pathname = '/';
                        });
                    }
                    try {
                        url = resp.request.options.url;
                        if(url.indexOf('/statistic/') === 0 ||
                           url.indexOf('/activity/') === 0 ||
                           url.indexOf('/terminal/') === 0 ||
                           url.indexOf('/edu-unit/') === 0) {
                            if(data.status != "success") {
                                Ext.Msg.alert('提示', data.msg);
                            }
                        }
                    } catch(e) { }
                });
                Ext.QuickTips.init();
                Ext.override(Ext.toolbar.Toolbar, {
                    onBeforeAdd: function(component) {
                        var oldUI = component.ui;
                        if (component.is('field')) {
                            component.ui = component.ui + '-toolbar';
                        }

                        // Any separators needs to know if is vertical or not
                        if (component instanceof Ext.toolbar.Separator) {
                            component.setUI((this.vertical) ? 'vertical' : 'horizontal');
                        }
                        this.callParent(arguments);
                        if(component.is('button')) {
                            component.ui = oldUI;
                        }
                    }
                });
                //禁用回车后退
                Ext.getDoc().on('keydown', function(e){
                    var t = e.target;
                    if(e.getKey() === Ext.EventObject.BACKSPACE) {
                        if(t.editable === true || Ext.Array.contains(['input', 'textarea'], t.tagName.toLowerCase())) {}
                        else { e.stopEvent(); }
                    }

                });
            });
        },
        buildUI: function(){
            var doBuild;
            if(!bbt.UserInfo.isReady()) {
                bbt.UserInfo.update();
            }
            Ext.Ajax.request({
                url: '/privileges/',
                success: function(resp){
                    var data = Ext.decode(resp.responseText);
                    boot.privileges = data.data;
                },
                failure: function(){
                    boot.blueScreen('无法连接服务器');
                }
            });
            doBuild = function(){
                boot.init(function(){
                    var walk, nodes, btns, ownPrivileges = bbt.UserInfo.userdata.privileges, realPS, key;
                    walk = function(ps) {
                        var i, len, tmp, rst = [];
                        if(!Ext.isArray(ps)) { ps = [ps]; }
                        for(i=0, len=ps.length;i<len;i++) {
                            if(ps[i].privileges) {
                                ps[i].privileges = walk(ps[i].privileges);
                                if(ps[i].privileges.length === 0) {
                                    continue;
                                }
                            } else {
                                if(!(ps[i].key in ownPrivileges)) {
                                    continue;
                                }
                            }
                            rst.push(ps[i]);
                        }
                        return rst;
                    };


                    realPS = walk(boot.privileges);
                    nodes = boot.privilege2Tree(realPS);
                    boot.initMenu(nodes);
                    btns = boot.privilege2ButtonGroup(realPS);
                    boot.initToolbar(btns);
                    boot.initMainUIEvents();
                    try {
                        key = Ext.Object.fromQueryString(location.search.substring(1)).key;
                    } catch(e) {}
                    if(key) {
                        setTimeout(function(){
                            execute(key);
                        }, 1000);
                    } else {
                        execute('global_statistic');
                    }

                });
            };
            setTimeout(function(){
                if(bbt.UserInfo.isReady() && boot.privileges) {
                    doBuild();
                } else {
                    setTimeout(arguments.callee, 1);
                }
            }, 1);
        },
        initToolbar: function(btns){
            var toolbar = Ext.getCmp('app-toolbar'), user = bbt.UserInfo, lang;
            lang = {
                "province": '省级管理员',
                "city": '地市州级管理员',
                "country": '区县市级管理员',
                "school": '校级管理员'
            };
            btns.push('->');
            btns.push({
                xtype: 'button',
                icon: '/public/images/user.png',
                scale: 'large',
                text: '您好，' + lang[user.level] + '：' + user.username,
                menu: {
                    items: [/*{
                        text: '用户信息',
                        icon: '/public/images/userinfo.gif',
                        handler: function(){
                            bbt.UserManager.editCurrentUser();
                        }
                    }, */{
                        text: '退出',
                        iconCls: 'tool-icon icon-exit',
                        handler: function(){
                            Ext.Msg.confirm('提示', '确定要退出吗？', function(btn){
                                if(btn == "yes") {
                                    apiRequest('logout', function(){
                                        window.location.reload();
                                    });
                                }
                            });
                        }
                    }]
                }
            });
            toolbar.add(btns);
        },
        initMenu: function(nodes){
            var menu = Ext.getCmp('app-menu');
            menu.getRootNode().appendChild(nodes);
        },
        initMainUIEvents: function(){
            var menu = Ext.getCmp('app-menu'), toolbar, bindKey;
            menu.addDocked({
                dock: 'top',
                xtype: 'toolbar',
                items: [{
                    text: '全部展开',
                    iconCls: 'tool-icon icon-expand',
                    handler: function(){
                        this.up('treepanel').expandAll();
                    }
                }, '-', {
                    text: '全部折叠',
                    iconCls: 'tool-icon icon-collapse',
                    handler: function(){
                        this.up('treepanel').collapseAll();
                    }
                }]
            });
            menu.on({
                collapse: function(){
                    //this.hoverable = true;
                    this.placeholder.getEl().on('mouseenter', function(){
                        this.floatCollapsedPanel();
                    }, this);
                }
            });
            /*menu.getEl().on({
                mouseleave: function(){
                    var cmp = Ext.getCmp(this.id);
                    if(cmp.placeholder && cmp.hoverable) {
                        cmp.placeholderCollapse();
                    }
                }
            });*/
            menu.on('itemclick', function(me, model){
                var key = model.raw.key;
                key && execute(key);
            });
            menu.on('itemexpand', function(node, e){
                var el = this.getView().getNode(node);
                Ext.get(el).down('.x-grid-cell-inner').setStyle('border-bottom', '0px solid #99bce8');
            });
            menu.on('itemcollapse', function(node, e){
                var el = this.getView().getNode(node);
                Ext.get(el).down('.x-grid-cell-inner').setStyle('border-bottom', '1px solid #99bce8');
            });
            toolbar = Ext.getCmp('app-toolbar');

            bindKey = function(btn){
                if(!btn) { return; }
                if(btn.key) { btn.handler = execute; }

                if(btn.menu) {
                    btn.on('mouseover', function(){
                        if(!this.menu.isVisible()) {
                            this.showMenu();
                        }
                    });
                    btn.on('mouseout', function(){
                        if(this.menu.isVisible()) {
                            this.hideMenu();
                        }
                    });
                    btn.menu.on('mouseenter', function(){
                        this.show();
                    });
                    btn.menu.on('mouseleave', function(){
                        this.hide();
                    });
                    btn.menu.items.each(bindKey);
                }
            };
            toolbar.items.each(bindKey);
        },
        blueScreen: function(msg) {
            var d = document.createElement('div');
            d.style.cssText = "position:absolute;top:0;left:0;bottom:0;right:0;background-color: blue;color: #FFF;font-size: 48px;padding-top:50px;";
            d.innerHTML = msg || 'unknow error, please contact your administrator!';
            Ext.onReady(function(){
                document.body.appendChild(d);
            });
        },
        privilege2Tree: function(privileges){
            var tree = [], makeNode, depth = 2, icons = {
                general: '',
                activity: '',
                //replace this `statistic` to `resource`
                resource: '',
                asset: '',
                system: '',
                maintenance: '',
                help: ''
            };
            makeNode = function(privilege, dp){
                var node = {text: privilege.name, key: privilege.key};
                if(Ext.isArray(privilege.privileges) && dp < depth) {
                    node.leaf = false;
                    node.expanded = true;
                    node.children = [];
                    (node.key in icons) && (node.iconCls = 'menu-icon icon-' + node.key + '-16');
                    Ext.each(privilege.privileges, function(p){
                        p.is_hide || node.children.push(makeNode(p, dp + 1));
                    });
                } else {
                    node.leaf = true;
                }
                return node;
            };
            if(!Ext.isArray(privileges)) { privileges = [privileges]; }
            Ext.each(privileges, function(privilege){
                tree.push(makeNode(privilege, 1));
            });
            return tree;
        },
        privilege2ButtonGroup: function(privileges){
            var list = [], makeButton, makeMenu, depth = 2, icons = {
                general: '',
                activity: '',
                //replace this `statistic` to `resource`
                resource: '',
                asset: '',
                system: '',
                maintenance: '',
                help: '',
            };
            makeMenu = function(data){
                var menu = [];
                Ext.each(data, function(p){

                    var item = {text: p.name, key: p.key};
                    /* only one level
                    if(p.privileges) {
                        item.menu = makeMenu(p.privileges, );
                    }*/

                    p.is_hide || menu.push(item);
                });
                return menu;
            };

            makeButton = function(privilege){
                var icon = 'menu-icon icon-' + privilege.key + '-32';
                var btn = {xtype: 'button', text: privilege.name, key: privilege.key, scale: 'large', iconCls: icon};
                if(privilege.privileges) {
                    btn.menu = makeMenu(privilege.privileges);
                }
                return btn;
            };
            if(!Ext.isArray(privileges)) { privileges = [privileges]; }
            Ext.each(privileges, function(privilege){
                list.push(makeButton(privilege));
            });
            return list;
        }
    }, execute, panels = {
        //globals
        global_statistic: {xtype: 'panel', title: '实时概况 > 全局数据', layout: 'border', defaults: {border: false}, items: [{region: 'west', bodyCls: 'r-border', xtype: 'bbt_area', width: 200, split: true, expandAllNodes: false}, {region: 'center', xtype: 'bbt_globalview', bodyCls: 'l-border'}]},
        global_login_status: {xtype: 'panel', title: '实时概况 > 班班通登录状态', layout: 'border', defaults: {border: false}, items: [{region: 'west', bodyCls: 'r-border', xtype: 'bbt_area', width: 200, split: true, expandAllNodes: false, schoolFirst: true,quickSearch: true,pinyinSupport:true, autoSchool: true}, {region: 'center', xtype: 'loginstatuspanel', bodyCls: 'l-border'}]},
        global_desktop_preview: {xtype: 'panel', title: '实时概况 > 桌面预览', layout: 'border', defaults: {border: false}, items: [{region: 'west', bodyCls: 'r-border', xtype: 'bbt_area', width: 200, split: true, expandAllNodes: false, schoolFirst: true,pinyinSupport:true,quickSearch: true, autoSchool: true}, {region: 'center', xtype: 'desktoppreview', bodyCls: 'l-border'}]},
        global_computer_room: {xtype: 'panel', title: '实时概况 > 电脑教室全局数据', layout: 'border', defaults: {border: false}, items: [{region: 'west', bodyCls: 'r-border', xtype: 'bbt_area', width: 200, split: true, expandAllNodes: false}, {region: 'center', xtype: 'computerclassglobalview', bodyCls: 'l-border'}]},
        global_computer_room_desktop_preview: {xtype: 'panel', title: '实时概况 > 电脑教室桌面预览', layout: 'border', defaults: {border: false}, items: [{region: 'west', bodyCls: 'r-border', xtype: 'bbt_area', width: 200, split: true, expandAllNodes: false, schoolFirst: true,pinyinSupport:true,quickSearch: true, autoSchool: true}, {region: 'center', xtype: 'desktoppreview', bodyCls: 'l-border', computerclass:true}]},
        global_teaching_venue: {xtype: '', title: '实时概况 > 教学点全局数据', feature: true},
        //maintenance
        maintenance_reset: {xtype: 'maintainpanel', title: '运维管理 > 终端远程关机重启'},
        maintenance_vnc: {xtype: 'remotehelppanel', title: '运维管理 > 远程桌面协助'},
        maintenance_trans_file: {xtype: '', title: '运维管理 > 文件发送', feature: true},
        maintenance_post: {xtype: 'noticewindow', title: '运维管理 > 校园电子公告', window: true},
        maintenance_msg: {xtype: '', title: '运维管理 > 消息发送', feature: true},
        activity_computer_room: {xtype: '', title: '使用记录 > 电脑教室使用日志', feature: true},
        activity_teaching_venue: {xtype: '', title: '使用记录 > 教学点使用日志', feature: true},
        statistic_teaching_venue_satellite_download: {xtype: '', title: '统计分析 > 教学点资源卫星下载统计', feature: true},
        activity_desktop_preview: {xtype: 'previewlog', title: '教师授课 > 班班通桌面使用日志', border: false},
        activity_edu_unit_preview: {xtype: 'previewlog', title: '教师授课 > 教学点桌面使用日志', edupoint:true, border: false},
        computer_room_logged_in: {xtype: '', title: '教师授课 > 电脑教室登陆日志', feature: true},
        teaching_analysis: {xtype: 'cphcount', title: '教师授课 > 班班通授课综合分析', border: false},
        resource_analysis: {xtype: '', title: '统计分析 > 班班通资源使用分析', feature: true},
        asset_log: {xtype: 'assetmgr', title: '资产管理 > 资产统计与申报', border: false},
        //resource
        resource_global_statistic: {xtype: 'resourceusage', title: '资源使用 > 资源使用综合分析', border: false},
        //system mangers
        system_user: {xtype: 'bbt_usermanager', title: '系统设置 > 用户管理', border: false},
        system_role: {xtype: 'bbt_rolemanager', title: '系统设置 > 角色管理', border: false},
        system_grade_class: {xtype: 'tabpanel', border: false, title: '系统设置 > 年级班级管理', items: [{xtype:'gc', title: '班班通教室', border: false}, {xtype:'computerclass', title: '电脑教室', border: false}]},
        system_lesson_period: {xtype: 'worktime', title: '系统设置 > 学校作息时间管理', border: false},
        system_lesson_name: {xtype: 'lesson', title: '系统设置 > 学校开课课程管理', border: false},
        system_new_lesson_name: {xtype: 'lesson2', title: '系统设置 > 学校开课课程管理', border: false},
        system_teacher: {xtype: 'teacher', title: '系统设置 > 教职人员信息管理', border: false},
        system_class_lesson: {xtype:'tabpanel', title: '系统设置 > 班级课程综合管理', items: [{xtype: 'coursetable', title: '课程表管理', border: false},{xtype: 'teachinfo', title: '班级课程授课老师管理', border: false}]},
        system_resource: {xtype: 'bbt_resource', title: '系统设置 > 资源管理', border: false},
        system_term: {xtype: 'term', title: '系统设置 > 学年学期管理', border: false},
        system_newterm: {xtype: 'panel', border: false, layout: 'card', items:[{xtype: 'term2', title: '系统设置 > 学年学期管理', border: false}, {xtype: 'courseoutline', title: '系统设置 > 学期关联教材大纲', border: false}]},
        system_sync_server: {xtype: 'bbt_setting', title: '系统设置 > 系统设置', window: true},
        system_node: {xtype: 'tabpanel', title: '系统设置 > 服务器汇聚管理', items:[{xtype: 'bbt_nodemanager', title: '学校服务器管理', border: false}, {xtype: 'edupoint_recv', title: '教学点卫星接收终端管理', border: false}, {xtype: 'edupoint_class', title: '教学点教室终端管理', border: false}]},
        system_restore: {xtype: 'bbt_restore', title: '系统设置 > 数据还原', window: true},
        system_edu_unit: {xtype: 'edupoint', title: '系统设置 > 教学点管理'},
        system_desktop_preview: {xtype: 'preview_settings', title: '系统设置 > 桌面预览设置', window: true},
        system_school_server_setting: {xtype: 'school_setting', title: '系统设置 > 校级服务器设置', window: true},
        system_country_server_setting: {xtype: 'school_setting', title: '系统设置 > 区县市级服务器设置', window: true},
        system_baseinfo: {xtype: 'basicinfo', title: '系统设置 > 基础信息同步查看', border: false},
        system_about: {xtype: 'bbt_about', title: '帮助 > 关于', window: true},
        system_activation: {xtype: 'bbt_activation', title: '帮助 > 授权信息'}
    }, currentKey;

    bbt.UserInfo.update(function(success){
        if(success) {
            if(bbt.UserInfo.level == "country") {
                panels.global_statistic.title = "实时概况 > 班班通全局数据";
                panels.global_desktop_preview.title = "实时概况 > 班班通桌面预览"
            }
            boot.buildUI();
        } else {
            Ext.onReady(function(){ boot.login(); });
        }
    });
    Ext.onReady(function(){
        var p = document.getElementById('bbt-server-info'),
            levels = {
                school: '校级服务器',
                country: '区县市级服务器',
                city: '地市州级服务器',
                province: '省级服务器'
            }, html;
        html = p.innerHTML.replace(/\{ (\w+)? \}/,function(a, v){
            return levels[v];
        });
        p.innerHTML = html;
    });

    //Ext.form.Basic.errorReader = new Ext.data.reader.Json({successProperty: 'status'});
    execute = function(key) {
        if(typeof key != "string") { key = key.key; }
        if(key === currentKey) { return; }
        var config, contentPane;
        //panel defined above
        config = panels[key];
        if(!config) {
            config = bbtConfig.get(key);
        }
        if(!config) { return; }
        if(config.window) {
            if(config.show) { config.show(); }
            else {
                /*if(key == 'system_sync_server'){
                    Ext.create('bbt.SystemSettings', config);
                } else if(key == 'system_restore') {
                    Ext.create('bbt.SystemRestore', config);
                } else if(key == 'system_desktop_preview') {
                    Ext.create('bbt.DesktopPreviewSettings', config);
                } else if(key == "system_about") {
                    Ext.create('bbt.About', config);
                } else if(key == "system_school_server_setting") {
                    Ext.create('bbt.SchoolSettings', config);
                }*/
                Ext.widget(config);
            }
            return;
        } else if(config.feature) {
            config = {xtype: 'new_feature', title: config.title, border: false};
        }
        contentPane = Ext.getCmp('content-panel');
        contentPane.removeAll(true);
        contentPane.add(config);
        currentKey = key;
    };
})();
var EStore = Ext.data.Store, tools = tools || {}, bbtConfig = {
    //映射后台命名为前台命名
    map: {
        logged_in: 'bbtUsageLog.login',
        not_logged_in: 'bbtUsageLog.unlogin',
        teacher_lesson_statistic: 'bbtAnalyzeStatic.teachCount',
        teacher_number_statistic: 'bbtAnalyzeStatic.teacherNumber',
        teacher_absent_statistic: 'bbtAnalyzeStatic.unlogin',
        resource_statistic: 'bbtAnalyzeStatic.resource',
        asset_report_log: 'bbtAnalyzeStatic.assetlist',
        asset_repair: 'bbtAnalyzeStatic.assetrepairhistosy',
        time_used_statistic: 'bbtAnalyzeStatic.timeUsedCount',
        resource_from_statistic: 'bbtResourceStatic.resourceFrom',
        resource_type_statistic: 'bbtResourceStatic.resourceType',
        resource_satellite_statistic: 'bbtResourceStatic.file',
        resource_satellite_log: 'bbtResourceStatic.fileLog',
        machine_time_used_statistic: 'bbtMachineStatic',
        edu_unit_machine_time_used_statistic: 'eduMachineStatic',
        machine_time_used_log: 'bbtMachineLog',
        edu_unit_classroom_statistic: 'bbtAnalyzeStatic.eduunit',
        edu_unit_logged_in: 'bbtUsageLog.eduunit'
    },
    gridDefaults: {
        title: '',//字符串 - 要显示的表格的标题
        url: '',//字符串 - 要显示的表格的数据源
        tools: null, //数组 - 要显示的表格的过滤条件，条件名参见 app.js 公用工具集合
        pagination: false, //true or false是否启用分页
        status: '', //字符串 - 要显示的表格右下角的消息文本
        statusRender: null, //格式化 status 的函数
        columns: null, //标准的 Ext.grid.Panel columns 配置对象
        sorters: null //标准的 Ext.data.Store sorter 配置对象
    },
    getAssetIcon: function(name){
        return '/public/images/asset/' + name + '.png';
    },
    get: function(key){
        if(key in bbtConfig.map) { key = bbtConfig.map[key] ;}
        else { return; }
        var parts = key.split('.'), obj = bbtConfig, widget;
        while(parts.length) {
            obj = obj[parts.shift()];
            if(typeof obj == "undefined") { return null; }
        }
        obj = Ext.clone(obj);
        if(!Ext.isArray(obj.grid)) { obj.grid = [obj.grid]; }
        Ext.each(obj.grid, function(item, i, a){
            var fields, store, pgbar, colDefaults = {
                menuDisabled: true,
                sortable: false,
                draggable: false
            }, mytools, queryCB;
            fields = Ext.Array.map(item.columns, function(c){ Ext.applyIf(c, colDefaults); return c.dataIndex; });
            store = new Ext.data.Store({
                fields: fields,
                proxy: {
                    type: 'ajax',
                    url: item.url,
                    reader: {
                        type: 'json',
                        root: 'data.records',
                        totalProperty: 'data.record_count'
                    },
                    extraParams: {},
                    sortParam: 'order_field',
                    pageParam: 'page',
                    directionParam: 'order_direction',
                    simpleSortMode: true,
                    startParam: undefined
                },
                sorters: item.sorters,
                remoteSort: true
            });

            if(item.statusTemplate) {
                pgbar = {
                    xtype:'pagingtoolbar',
                    store: store,
                    items: ['->', {
                        xtype: 'tbtext',
                        itemId: 'status',
                        statusTemplate: true
                    }],
                    statusTemplate: item.statusTemplate,
                    displayInfo: false,
                    statusRender: item.statusRender||function(){return '';},
                    listeners: {
                        boxready: function(){
                            var me = this, store = me.store, loadCB;
                            me.down('textfield').setWidth(60);
                            loadCB = function(s){
                                try {
                                    if(s.proxy.reader.rawData.data.records) {
                                        me.down('tbtext[statusTemplate]').setText(me.statusRender(me.statusTemplate, me, store));
                                    }
                                } catch(e) {}
                            };
                            store.on('load', loadCB);
                            if(!store.isLoading()) { loadCB(); }
                            me.on('beforedestroy', function(){
                                store.un('load', loadCB);
                            });
                        }
                    }
                };
            } else {
                pgbar = {
                    xtype:'pagingtoolbar',
                    store: store,
                    displayInfo: true,
                    listeners: {
                        boxready: function(){
                            this.down('textfield').setWidth(60);
                        }
                    }
                };
            }
            mytools = bbt.ToolBox.convert(item.tools);
            a[i] = {
                xtype: 'grid',
                border: false,
                hidden: item.hidden,
                columns: item.columns,
                dockedItems: mytools[0].xtype == "toolbar" ? mytools : {xtype: 'toolbar', dock: 'top', items: mytools, layout: {overflowHandler: 'Menu'}},
                columnLines: true,
                features: item.features,
                plugins: item.plugins,
                bbar: pgbar,
                store: store,
                title: item.title,
                viewConfig: {stripeRows: true, forceFit: true},
                exportUrl: item.exportUrl,
                chart: item.chart,
                listeners: {
                    beforedestroy: function(){
                        if(this.onAllLoadedTimer) {
                            clearInterval(this.onAllLoadedTimer);
                        }
                    },
                    viewready: function(){
                        var k, me = this, query = item.query||{}, tbs = me.query('toolbar[dock=top]'), combos=[], btn;
                        Ext.each(tbs, function(tb){
                            Ext.each(tb.query('[name]'), function(comp){
                                var v;
                                if(comp.is('combo')) { combos.push(comp); }
                                if(comp.name in query) {
                                    v = query[comp.name];
                                    if(typeof v == "function") { v = v(); }
                                    comp.setValue(v);
                                    //comp.is('datefield') && comp.collapse();
                                }
                            });
                            var hasbtn = tb.down('button[action=query]');
                            hasbtn && (btn = hasbtn);
                        });
                        me.onAllLoadedTimer = setInterval(function(){
                            var wait = false;
                            Ext.each(combos, function(c){
                                if(typeof c._loaded !== "undefined" && c._loaded !== true) { wait = true; return; } 
                                if(c.store && c.store.isLoading()) {
                                    wait = true;
                                    return false;
                                }
                            });
                            if(!wait) {
                                clearInterval(me.onAllLoadedTimer);
                                delete me.onAllLoadedTimer;
                                setTimeout(function(){ btn.handler.call(btn); }, 10);
                            }
                        }, 10);
                    }
                }
            };
            if(item.listeners) {
                Ext.applyIf(a[i].listeners, item.listeners);
            }
        });
        if(obj.grid.length === 1) {
            obj = obj.grid[0];
        } else {
            obj = {
                xtype: 'tabpanel',
                title: obj.title,
                border: false,
                items: obj.grid
            };
        }
        widget = Ext.widget(obj.xtype, obj);
        bbt.autoFill(widget);

        if(!bbt.UserInfo.isSchool()) {
            bbt.autoArea(widget);
        }

        return widget;
    },
    tmplReg: /\{(\w+)\}/g,
    isEmpty: function(v) {
        return v === null || v === undefined || v === '';
    },
    tmpl: function(template, data, defaultValue){
        var me = this;
        if(typeof defaultValue == "undefined") {
            defaultValue = '';
        }
        return template ? template.replace(me.tmplReg, function(_, key){
            return me.isEmpty(data[key]) ? defaultValue : data[key];
        }) : '';
    }
};

/* 管辖范围 */
Ext.define('bbt.areaTree', {
    extend: 'Ext.tree.Panel',
    alias: 'widget.bbt_area',
    initComponent: function () {
        var store = new Ext.data.TreeStore({
            root: {text: '所有', expanded: true, children: []}
        });
        Ext.apply(this, {
            store: store,
            rootVisible: false,
            useArrows: true,
            displayField: 'text',
            listeners: {
                itemclick: function(_, model){
                    var me = this, level, lm, sibling;
                    lm = {
                        grade: 0,
                        school: 1,
                        town: 2,
                        country: 3,
                        city: 4,
                        province: 5
                    }
                    level = me.autoSchool ? "school" : me.autoLevel;
                    if(lm[model.raw.group_type] > lm[level]) {
                        model.eachChild(function(child){
                            var node;
                            if(child === model.firstChild) {
                                node = child;
                                while(node && node.raw.group_type !== level) {
                                    node = node.firstChild;
                                }
                                node && me.fireClick(node);
                            } else {
                                child.collapse(true);
                            }
                        });
                    } else {
                        me.fireClick(model);
                    }
                    //extra support
                    if(bbt.UserInfo.level == "country" && model.raw.group_type == "town") {
                        sibling = model.nextSibling;
                        while(sibling) {
                            sibling.isExpanded() && sibling.collapse();
                            sibling = sibling.nextSibling;
                        }
                        sibling = model.previousSibling;
                        while(sibling) {
                            sibling.isExpanded() && sibling.collapse();
                            sibling = sibling.previousSibling;
                        }
                        model.expand();
                    }
                },
                viewready: function(){
                    this.updateStore(function(me){
                        var ok = false;
                        me.getRootNode().cascadeBy(function(node){
                            if(ok) { return false; }
                            if(me.schoolFirst) {
                                if(node.raw.group_type == 'school'){
                                    me.fireClick(node);
                                    ok = true;
                                    return false;
                                }
                            } else {
                                if(node.raw.group_type == bbt.UserInfo.level){
                                    me.fireClick(node);
                                    ok = true;
                                    return false;
                                }
                            }
                        });
                        me.isStoreLoaded = true;
                        me.fireEvent('load', me);
                        if(!bbt.UserInfo.isSchool()) {
                            me.calcSchool();
                        }
                    });
                }
            }
        });
        if(!bbt.UserInfo.isSchool() && this.quickSearch) {
            this.tbar = [{
                xtype: 'combo',
                displayField: 'text',
                valueField: 'value',
                querMode: 'local',
                hideTrigger: true,
                emptyText: '查找“实验小学”？试试输入“syxx”',
                width: '100%',
                store: new Ext.data.Store({fields: ['text','value']}),
                afterSubTpl: '<a class="search-box" href="javascript:void(0);"></a>',
                doSearch: function(){
                    var v = this.getValue(), root, ret;
                    this.collapse();
                    if(!v) { return; }
                    v = Ext.String.trim(v);
                    root = this.up('treepanel').getRootNode();
                    ret = [];
                    if(!v) {return;}
                    root.cascadeBy(function(n){
                        var text = n.data.text || '',
                            pinyin = n.raw.first_letter || '';
                        if(n.raw.group_type != "school") { return; }
                        if(text.indexOf(v) !== -1 || pinyin.indexOf(v) !== -1) {
                            ret.push({text:text,value:text,node: n});
                        }
                    });
                    this.store.removeAll();
                    this.store.add(ret);
                    this.expand();
                },
                listeners: {
                    afterrender: function(){
                        this.getEl().down('.search-box').on('click', function(){
                            this.hide();
                        });
                    },
                    focus: function(){
                        this.selectText();
                    },
                    blur: function(){
                        this.getEl().down('.search-box').show();
                    },
                    change: function(){ this.doSearch(); },
                    select: function(me, rc){
                        var tree;
                        if(rc.length) {
                            rc = rc[0].raw.node;
                            tree = me.up('treepanel');
                            tree.collapseAll();
                            tree.selectPath(rc.getPath('text'), 'text');

                            setTimeout(function(){
                                var el = tree.getView().getNode(rc);
                                bbt.simulateClick(el);
                            }, 400);
                        }
                    }
                }
            }];
        }
        this.callParent();

    },
    calcSchool: function(){
        var root = this.getRootNode(), calc;
        calc = function(node){
            var i, len, sum = 0;
            if(node.raw.group_type == "town") {
                sum = node.childNodes.length;
            } else {
                for(i=0,len=node.childNodes.length;i<len;i++) {
                    sum += calc(node.childNodes[i]);
                }
            }
            node.set('text', node.get('text') + '(' + sum + ')');
            node.commit();
            return sum;
        };
        calc(root);
    },
    fireClick: function(model){
        var panel;
        if(!model) { return; }
        panel = Ext.getCmp('content-panel').down('[region=center]');
        panel.onLevelChange && panel.onLevelChange(model.raw.group_type||'grade', model.raw.uuid);
        this.selectPath(model.getPath('text'), 'text');
        if(!model.isLeaf()) {
            model.expand();
        }
    },
    updateStore: function(cb){
        var me = this, params;
        if(this.pinyinSupport) {
            params = {first_letter: 'true'};
        }
        Ext.Ajax.request({
            url: '/group/',
            method: 'GET',
            params: params,
            success: function(resp){
                var data;
                try {
                    data = Ext.decode(resp.responseText);
                } catch(e) {
                    data = {};
                }
                if(data.status == "success") {
                    data = data.data;
                    me._parse(data);
                    cb && cb(me);
                }
            }
        });
    },
    _parse: function(data){
        var me = this, root, groups = {}, uuid, gradeTexts, g, gp, level = bbt.UserInfo.level, isSchool = bbt.UserInfo.isSchool(), cuuid, defaultExpand = typeof me.expandAllNodes == "undefined" ? true : me.expandAllNodes;
        Ext.each(data.group, function(group){
            group.iconCls = "icon-" + group.group_type;
            groups[group.uuid] = group;
            if(!group.parent__uuid) {
                root = group;
            }
            if(group.group_type == level) {
                cuuid = group.uuid;
            }
        });
        if(data.grade && data.grade.length) {
            gradeTexts = '一 二 三 四 五 六 七 八 九 十 十一 十二'.split(' ');
            data.grade.sort(function(a, b){
                var ai = Ext.Array.indexOf(gradeTexts, a.name),
                    bi = Ext.Array.indexOf(gradeTexts, b.name);
                return ai - bi;
            });
            Ext.each(data.grade, function(grade){
                var school = groups[grade.term__school__uuid];
                if(!school.children) {
                    school.children = [];
                }
                grade.leaf = true;
                if(me.skipComputerClass && grade.name == "电脑教室") { return; }
                grade.text = grade.name == "电脑教室" ? grade.name : grade.name + '年级';
                grade.iconCls = 'icon-grade';
                grade.group_type = "grade";
                school.children.push(grade);
            });
        } else {
            data.grade = false;
        }

        for(uuid in groups) {
            g = groups[uuid];
            if(!data.grade && g.group_type == "school") {
                g.leaf = true;
            } else {
                g.leaf = false;
            }

            g.expanded = defaultExpand;
            g.text = g.name;

            if(!g.parent__uuid) { root = g; continue; }
            gp = groups[g.parent__uuid];
            if(!gp.children) {
                gp.children = [];
            }
            gp.children.push(g);
        }
        //this.getRootNode().appendChild(root);
        if(me.currentAsRoot) {
            me.getRootNode().appendChild(groups[cuuid].children);
        } else {
            me.getRootNode().appendChild(root);
        }
    }
});
Ext.chart.theme.bbt = Ext.extend(Object, {
    constructor: function(config) {
        Ext.chart.theme.Base.prototype.constructor.call(this, Ext.apply({
            colors: ['#398439', '#269abc', '#d58512', '#285e8e', '#ac2925']
        }, config));
    }
});
/* 自定义图表 */
Ext.define('bbt.chart', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.bbt_chart',
    initComponent: function () {
        this.border = false;
        this.layout = {type: 'vbox', align: 'stretch'};
        this.chart.flex = 9;
        this.chart.theme = 'bbt';
        this.chart.border = false;
        this.items = [this.chart, {xtype: 'panel', hidden: this.hidePanel, border: false, height: 32, padding: 5, html: '<ul class="bbt-legend"></ul>'}];
        this.callParent();
    },
    addItem: function (text, color) {
        var li = document.createElement('li'), legend;
        li.innerHTML = '<a href="javascript:void(0)"><b style="background-color:' + color + ';"></b>' + text + '</a>';
        legend = this.getEl().query('.bbt-legend')[0];
        legend.appendChild(li);
    },
    clearItems: function () {
        var legend = this.getEl().query('.bbt-legend')[0];
        legend && (legend.innerHTML = '');
    }
});
/* 实时概况 */
new EStore({id: 'ClassNumStore', fields: ['number', 'label']});
new EStore({id: 'ClassNumStore2', fields: ['name', 'num']});
new EStore({id: 'TeacherNumStore', fields: ['number', 'label']});
new EStore({id: 'TeacherNumStore2', fields: ['name', 'num']});
Ext.define('bbt.globalView', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.bbt_globalview',
    minWidth: 800,
    initComponent: function () {
        var me = this;
        Ext.apply(me, {
            border: false,
            minWidth: 450,
            minHeight: 500,
            layout: {type: 'vbox', align: 'stretch'},
            defaults: {flex: 1, border: false},
            listeners: {
                beforedestroy: function(){
                    var stores = ['ClassNumStore', 'ClassNumStore2', 'TeacherNumStore', 'TeacherNumStore2'],
                        i = 0, len = stores.length;
                    for(;i<len;i++) {
                        Ext.getStore(stores[i]).removeAll();
                    }
                }
            }
        });
        me.items = [
            {
                xtype: 'panel',
                layout: {type: 'hbox', align: 'stretch'},
                defaultType: 'bbt_chart',
                defaults: {flex: 1, border: false},
                items: [
                    {
                        bodyCls: 'rb-border',
                        chart: {
                            xtype: 'chart',
                            theme: 'Green',
                            store: 'ClassNumStore',
                            animate: true,
                            series: [
                                {
                                    type: 'pie',
                                    highlight: true,
                                    showInLegend: true,
                                    angleField: 'number',
                                    tips: {trackMouse: true, width: 120, renderer: function(r){ this.setTitle(r.get('label')); }},
                                    label: {display: 'rotate', field: 'label', contrast: true, color: '#F06000'},
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#d58512', '#398439'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                afterrender: this.addClassItems,
                                refresh: this.addClassItems
                            }
                        }
                    },
                    {
                        bodyCls: 'b-border',
                        chart: {
                            xtype: 'chart',
                            theme: 'Green',
                            store: 'TeacherNumStore',
                            animate: true,
                            series: [
                                {
                                    type: 'pie',
                                    highlight: true,
                                    showInLegend: true,
                                    angleField: 'number',
                                    tips: {trackMouse: true, width: 120, renderer: function(r){ this.setTitle(r.get('label')); }},
                                    label: {display: 'rotate', field: 'label', contrast: true, color: '#F06000'},
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#d58512', '#398439'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                afterrender: this.addTeacherItems,
                                refresh: this.addTeacherItems
                            }
                        }
                    }
                ]
            },
            {
                xtype: 'panel',
                layout: {type: 'hbox', align: 'stretch'},
                defaultType: 'bbt_chart',
                defaults: {flex: 1, border: false},
                items: [
                    {
                        bodyCls: 'r-border',
                        hidePanel: true,
                        chart: {
                            xtype: 'chart',
                            theme: 'Sky',
                            animate: true,
                            store: 'ClassNumStore2',
                            axes: [
                                {
                                    type: 'Numeric',
                                    position: 'left',
                                    fields: ['num'],
                                    title: '在线教室Top5',
                                    minimum: 0,
                                    maximum: 10
                                },
                                {
                                    type: 'Category',
                                    position: 'bottom',
                                    fields: ['name'],
                                    label: {renderer:function(v){
                                        if(v && v.length > 5) {
                                            return v.substring(0, 5)+'...';
                                        }
                                        return v;
                                    }}
                                }
                            ],
                            series: [
                                {
                                    type: 'column',
                                    axis: 'left',
                                    gutter: 100,
                                    style: {width: 30},
                                    highlight: true,
                                    tips: {trackMouse: true, width: 140, renderer: function(r){ r.get('name')&&this.setTitle(r.get('name')+':'+r.get('num')); }},
                                    label: {display: 'insideEnd', field: 'num', contrast: true},
                                    xField: 'name',
                                    yField: 'num',
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#398439', '#269abc', '#d58512', '#285e8e', '#ac2925', '#F00'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                //afterrender: this.addOnlineClassItems,
                                //refresh: this.addOnlineClassItems
                            }
                        }
                    },
                    {
                        hidePanel: true,
                        chart: {
                            xtype: 'chart',
                            animate: true,
                            theme: 'Sky',
                            store: 'TeacherNumStore2',
                            axes: [
                                {
                                    type: 'Numeric',
                                    position: 'left',
                                    fields: ['num'],
                                    title: '授课教师在线Top5',
                                    minimum: 0,
                                    maximum: 10
                                },
                                {
                                    type: 'Category',
                                    position: 'bottom',
                                    fields: ['name'],
                                    label: {renderer:function(v){
                                        if(v && v.length > 5) {
                                            return v.substring(0, 5)+'...';
                                        }
                                        return v;
                                    }}
                                }
                            ],
                            series: [
                                {
                                    type: 'column',
                                    gutter: 100,
                                    axis: 'left',
                                    highlight: true,
                                    style: {width: 30},
                                    tips: {trackMouse: true, width: 140, renderer: function(r){r.get('name')&&this.setTitle(r.get('name')+':'+r.get('num'));}},
                                    label: {display: 'insideEnd', field: 'num', contrast: true},
                                    xField: 'name',
                                    yField: 'num',
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#398439', '#269abc', '#d58512', '#285e8e', '#ac2925', '#F00'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                //afterrender: this.addOnlineTeacherItems,
                                //refresh: this.addOnlineTeacherItems
                            }
                        }
                    }
                ]
            }
        ];
        me.callParent();
        //setTimeout(function(){ me.update(); }, 1);
    },
    onLevelChange: function(level, uuid){
        /*var types = ['province', 'city', 'country', 'town', 'school', 'grade'],
            ct = bbt.UserInfo.level;

        if(Ext.Array.indexOf(types, level) < Ext.Array.indexOf(types, ct)) {
            this.update({uuid: uuid, type: ct});
        } else {
            this.update({uuid: uuid, type: level});
        }*/
        this.update({uuid: uuid, type: level});
    },
    addOnlineClassItems: function(c){
        var sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            sum += r.get('num');
        });
        bbtChart.addItem('在线教室（TOP 5）：' + sum, '#FFF');
    },
    addOnlineTeacherItems: function(c){
        var sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            sum += r.get('num');
        });
        bbtChart.addItem('在线授课教师（TOP 5）：' + sum, '#FFF');
    },
    addClassItems: function (c) {
        var colors = ['#d58512', '#398439'], sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            bbtChart.addItem(r.get('label'), colors[i]);
            sum += r.get('number');
        });
        bbtChart.addItem('教室总数：' + sum, '#FFF');
    },
    addTeacherItems: function (c) {
        var colors = ['#d58512', '#398439'], sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            bbtChart.addItem(r.get('label'), colors[i]);
            sum += r.get('number');
        });
        bbtChart.addItem('授课教师总数：' + sum, '#FFF');
    },
    updateMaximum: function(classes, teachers){
        var cmp = function(a, b){ return a.num > b.num ? 1 : -1; },
            maxClass = Ext.Array.max(classes, cmp),
            maxTeacher = Ext.Array.max(teachers, cmp);

        Ext.each(this.query('chart'), function(chart){
            if(chart.store.storeId == 'ClassNumStore2') {
                maxClass && maxClass.num && (chart.axes.get(0).maximum = maxClass.num + 10);
            } else if(chart.store.storeId == 'TeacherNumStore2') {
                maxTeacher && maxTeacher.num && (chart.axes.get(0).maximum = maxTeacher.num + 10);
            }
        });
    },
    getDefaultArea: function(){
        var root = this.up('panel').down('bbt_area').getRootNode(), ret = {
            type: bbt.UserInfo.level
        };
        root.cascadeBy(function(node){
            if(node.raw.group_type === bbt.UserInfo.level) {
                ret.uuid = node.raw.uuid;
                return false;
            }
        });
        return ret;
    },
    update: function(params){
        var me = this, mid;
        params = params || me.getDefaultArea();
        mid = bbt.utils.createMask(me, 'Loading');
        Ext.Ajax.request({
            url: '/global_statistic/',
            method: 'GET',
            params: params,
            success: function(resp){
                var data = Ext.decode(resp.responseText), store, tmp;
                if(data.status == "success") {
                    store = Ext.getStore('ClassNumStore');
                    store.removeAll();
                    store.loadData(me.parseData(data.data['class'], '教室'));

                    store = Ext.getStore('TeacherNumStore');
                    store.removeAll();
                    store.loadData(me.parseData(data.data['teacher'], '授课教师', true));

                    me.updateMaximum(data.data['class']['online_list'], data.data['teacher']['online_list']);

                    store = Ext.getStore('ClassNumStore2');
                    store.removeAll();
                    tmp = data.data['class']['online_list'];
                    store.loadData(tmp.length ? tmp : [{name: '', number:0}]);

                    store = Ext.getStore('TeacherNumStore2');
                    store.removeAll();
                    tmp = data.data['teacher']['online_list'];
                    store.loadData(tmp.length ? tmp : [{name: '', number:0}]);
                }
            },
            callback: function(){
                bbt.utils.destroyMask(mid);
            }
        });
    },
    parseData: function(data, label, pre){
        if(pre) {
            return [{
                label: label +'在线'+ '：' + data.online,
                number: data.online
            }, {
                label: label +'离线' +  '：' + data.offline,
                number: data.offline
            }];
        } else {
            return [{
                label: '在线'+label + '：' + data.online,
                number: data.online
            }, {
                label: '离线' + label + '：' + data.offline,
                number: data.offline
            }];
        }
        return result;
    }
});
Ext.define('bbt.ComputerClassGlobalView', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.computerclassglobalview',
    minWidth: 800,
    initComponent: function () {
        var me = this;
        Ext.apply(me, {
            border: false,
            minWidth: 450,
            minHeight: 500,
            layout: {type: 'vbox', align: 'stretch'},
            defaults: {flex: 1, border: false},
            listeners: {
                beforedestroy: function(){
                    var stores = ['ClassNumStore', 'ClassNumStore2', 'TeacherNumStore', 'TeacherNumStore2'],
                        i = 0, len = stores.length;
                    for(;i<len;i++) {
                        Ext.getStore(stores[i]).removeAll();
                    }
                }
            }
        });
        me.items = [
            {
                xtype: 'panel',
                layout: {type: 'hbox', align: 'stretch'},
                defaultType: 'bbt_chart',
                defaults: {flex: 1, border: false},
                items: [
                    {
                        bodyCls: 'rb-border',
                        chart: {
                            xtype: 'chart',
                            theme: 'Green',
                            store: 'ClassNumStore',
                            animate: true,
                            series: [
                                {
                                    type: 'pie',
                                    highlight: true,
                                    showInLegend: true,
                                    angleField: 'number',
                                    tips: {trackMouse: true, width: 120, renderer: function(r){ this.setTitle(r.get('label')); }},
                                    label: {display: 'rotate', field: 'label', contrast: true, color: '#F06000'},
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#d58512', '#398439'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                afterrender: this.addClassItems,
                                refresh: this.addClassItems
                            }
                        }
                    },
                    {
                        bodyCls: 'b-border',
                        chart: {
                            xtype: 'chart',
                            theme: 'Green',
                            store: 'TeacherNumStore',
                            animate: true,
                            series: [
                                {
                                    type: 'pie',
                                    highlight: true,
                                    showInLegend: true,
                                    angleField: 'number',
                                    tips: {trackMouse: true, width: 120, renderer: function(r){ this.setTitle(r.get('label')); }},
                                    label: {display: 'rotate', field: 'label', contrast: true, color: '#F06000'},
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#d58512', '#398439'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                afterrender: this.addTeacherItems,
                                refresh: this.addTeacherItems
                            }
                        }
                    }
                ]
            },
            {
                xtype: 'panel',
                layout: {type: 'hbox', align: 'stretch'},
                defaultType: 'bbt_chart',
                defaults: {flex: 1, border: false},
                items: [
                    {
                        bodyCls: 'r-border',
                        hidePanel: true,
                        chart: {
                            xtype: 'chart',
                            theme: 'Sky',
                            animate: true,
                            store: 'ClassNumStore2',
                            axes: [
                                {
                                    type: 'Numeric',
                                    position: 'left',
                                    fields: ['num'],
                                    title: '电脑教室在线总数（TOP 5）',
                                    minimum: 0,
                                    maximum: 10
                                },
                                {
                                    type: 'Category',
                                    position: 'bottom',
                                    fields: ['name'],
                                    label: {renderer:function(v){
                                        if(v && v.length > 5) {
                                            return v.substring(0, 5)+'...';
                                        }
                                        return v;
                                    }}
                                }
                            ],
                            series: [
                                {
                                    type: 'column',
                                    axis: 'left',
                                    gutter: 100,
                                    style: {width: 30},
                                    highlight: true,
                                    tips: {trackMouse: true, width: 140, renderer: function(r){ r.get('name')&&this.setTitle(r.get('name')+':'+r.get('num')); }},
                                    label: {display: 'insideEnd', field: 'num', contrast: true},
                                    xField: 'name',
                                    yField: 'num',
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#398439', '#269abc', '#d58512', '#285e8e', '#ac2925', '#F00'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                /*afterrender: this.addOnlineClassItems,
                                refresh: this.addOnlineClassItems*/
                            }
                        }
                    },
                    {
                        hidePanel: true,
                        chart: {
                            xtype: 'chart',
                            animate: true,
                            theme: 'Sky',
                            store: 'TeacherNumStore2',
                            axes: [
                                {
                                    type: 'Numeric',
                                    position: 'left',
                                    fields: ['num'],
                                    title: '登录授课总数（TOP 5）',
                                    minimum: 0,
                                    maximum: 10
                                },
                                {
                                    type: 'Category',
                                    position: 'bottom',
                                    fields: ['name'],
                                    label: {renderer:function(v){
                                        if(v && v.length > 5) {
                                            return v.substring(0, 5)+'...';
                                        }
                                        return v;
                                    }}
                                }
                            ],
                            series: [
                                {
                                    type: 'column',
                                    gutter: 100,
                                    axis: 'left',
                                    highlight: true,
                                    style: {width: 30},
                                    tips: {trackMouse: true, width: 140, renderer: function(r){r.get('name')&&this.setTitle(r.get('name')+':'+r.get('num'));}},
                                    label: {display: 'insideEnd', field: 'num', contrast: true},
                                    xField: 'name',
                                    yField: 'num',
                                    renderer: function(sprite, record, attr, index, store){
                                        var colors = ['#398439', '#269abc', '#d58512', '#285e8e', '#ac2925', '#F00'];
                                        return Ext.apply(attr, {
                                            fill: colors[index % colors.length]
                                        });
                                    }
                                }
                            ],
                            listeners: {
                                /*afterrender: this.addOnlineTeacherItems,
                                refresh: this.addOnlineTeacherItems*/
                            }
                        }
                    }
                ]
            }
        ];
        me.callParent();
        //setTimeout(function(){ me.update(); }, 1);
    },
    onLevelChange: function(level, uuid){
        /*var types = ['province', 'city', 'country', 'town', 'school', 'grade'],
            ct = bbt.UserInfo.level;

        if(Ext.Array.indexOf(types, level) < Ext.Array.indexOf(types, ct)) {
            this.update({uuid: uuid, type: ct});
        } else {
            this.update({uuid: uuid, type: level});
        }*/
        this.update({uuid: uuid, type: level});
    },
    addOnlineClassItems: function(c){
        var sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            sum += r.get('num');
        });
        bbtChart.addItem('电脑教室在线总数（TOP 5）：' + sum, '#FFF');
    },
    addOnlineTeacherItems: function(c){
        var sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            sum += r.get('num');
        });
        bbtChart.addItem('登录授课总数（TOP 5）：' + sum, '#FFF');
    },
    addClassItems: function (c) {
        var colors = ['#d58512', '#398439'], sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            bbtChart.addItem(r.get('label'), colors[i]);
            sum += r.get('number');
        });
        bbtChart.addItem('电脑教室数：' + sum, '#FFF');
    },
    addTeacherItems: function (c) {
        var colors = ['#d58512', '#398439'], sum = 0, bbtChart;
        bbtChart = c.up('bbt_chart');
        bbtChart.clearItems();
        c.store.each(function (r, i) {
            bbtChart.addItem(r.get('label'), colors[i]);
            sum += r.get('number');
        });
        bbtChart.addItem('电脑教室数：' + sum, '#FFF');
    },
    updateMaximum: function(classes, teachers){
        var cmp = function(a, b){ return a.num > b.num ? 1 : -1; },
            maxClass = Ext.Array.max(classes, cmp),
            maxTeacher = Ext.Array.max(teachers, cmp);

        Ext.each(this.query('chart'), function(chart){
            if(chart.store.storeId == 'ClassNumStore2') {
                maxClass && maxClass.num && (chart.axes.get(0).maximum = maxClass.num + 10);
            } else if(chart.store.storeId == 'TeacherNumStore2') {
                maxTeacher && maxTeacher.num && (chart.axes.get(0).maximum = maxTeacher.num + 10);
            }
        });
    },
    getDefaultArea: function(){
        var root = this.up('panel').down('bbt_area').getRootNode(), ret = {
            type: bbt.UserInfo.level
        };
        root.cascadeBy(function(node){
            if(node.raw.group_type === bbt.UserInfo.level) {
                ret.uuid = node.raw.uuid;
                return false;
            }
        });
        return ret;
    },
    update: function(params){
        var me = this, mid;
        params = params || me.getDefaultArea();
        mid = bbt.utils.createMask(me, 'Loading');
        Ext.Ajax.request({
            url: '/global-statistic/computer-class/',
            method: 'GET',
            params: params,
            success: function(resp){
                var data = Ext.decode(resp.responseText), cc, store, tmp;
                if(data.status == "success") {
                    cc = data.data.computerclass;
                    store = Ext.getStore('ClassNumStore');
                    store.removeAll();
                    store.loadData([{
                        label: '电脑教室在线：' + cc.online,
                        number: cc.online
                    }, {
                        label: '电脑教室离线：' + cc.offline,
                        number: cc.offline
                    }]);

                    store = Ext.getStore('TeacherNumStore');
                    store.removeAll();
                    store.loadData([{
                        label: '登录授课：' + cc.login,
                        number: cc.login
                    }, {
                        label: '未登录授课：' + cc.unlogin,
                        number: cc.unlogin
                    }]);

                    me.updateMaximum(cc['online_list'], cc['login_list']);

                    store = Ext.getStore('ClassNumStore2');
                    store.removeAll();
                    tmp = cc['online_list'];
                    store.loadData(tmp.length ? tmp : [{name: '', number:0}]);

                    store = Ext.getStore('TeacherNumStore2');
                    store.removeAll();
                    tmp = cc['login_list'];
                    store.loadData(tmp.length ? tmp : [{name: '', number:0}]);
                }
            },
            callback: function(){
                bbt.utils.destroyMask(mid);
            }
        });
    },
    parseData: function(data, label){
        var result = [{
            label: '在线'+label + '：' + data.online,
            number: data.online
        }, {
            label: '离线' + label + '：' + data.offline,
            number: data.offline
        }];
        return result;
    }
});

/**
 * common api request interface
 * @apiName [String] api_interface key
 * @params [Object] extra data when use POST
 * @success [optional] callback when server response successfuly
 * @failure [optional] callback when server response error,
 * @callback [optional] callback when request end
 */
function apiRequest(url, params, success, failure) {
    var idstr = '', waitMsg, waitTarget, form, config, loadMask;
    if(typeof params == "function") {
        success = params;
        params = {};
    }
    if(params.id) { idstr = '?id=' + params.id; delete params.id; }
    if(params.form) { form = params.form; delete params.form; }
    waitMsg = apiRequest.msg || '正在获取数据……';
    waitTarget = apiRequest.target || params.waitTarget || (form && form.up('panel')) || document.body;
    params.waitTarget && (delete params.waitTarget);
    apiRequest.msg && (delete apiRequest.msg);
    apiRequest.target && (delete apiRequest.target);

    config = {
        url: url + idstr,
        params: params
    };
    if(form) {
        form = form.getForm();
        form.waitMsgTarget = waitTarget.getEl();
        config.waitMsg = waitMsg;
        config.success = function(_form, action){
            success(action.result);
        };
        config.failure = function(_form, action){
            Ext.Msg.alert('提示', getErrorMsg(action.result));
        };
        form.submit(config);
    } else {
        loadMask = new Ext.LoadMask(waitTarget, {msg: waitMsg});
        loadMask.show();
        config.timeout = 30 * 60 * 1000;
        config.callback = function(_options, _success, resp){
            loadMask.hide();
            onResponse(resp, success, failure);
            loadMask.destroy();
        };
        Ext.Ajax.request(config);
    }
}

function decodeResponse(resp) {
    var data;
    try {
        data = Ext.JSON.decode(resp.responseText);
    } catch (e) {
        data = {};
    }
    return data;
}


function checkForm(form) {
    var isValid = true, msg;

    if(form.is && form.is('form')) {
        form = form.getForm();
    }

    form.getFields().each(function(f){
        if(!f.isValid()) {
            msg = f.getFieldLabel() + '：' + f.getActiveError();
            isValid = false;
            return false;
        }
    });
    return msg || isValid;
}

function checkPassword(fm, name, name2) {
    if(arguments.length === 1) {
        name = 'password',
        name2 = 'password_confirmation';
    }
    fm.xtype === "form" && (fm = fm.getForm());
    var v1 = fm.findField(name).getValue();
    var v2 = fm.findField(name2).getValue();
    return v1 === v2;
}

function downloadFile(url, name) {
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
            listeners: {
                click: function(){
                    var win = this.up('window');
                    setTimeout(function(){ win.destroy(); }, 500);
                }
            }
        }]
    }).show();
}

function getErrorMsg(data) {
    var k, msg;
    try {
        if(typeof data == "string") {
            data = Ext.decode(data);
            msg = data.msg;
        }
    } catch (e) {
        msg = '未知的错误!';
    }
    for(k in data) break;
    if(!k) {
        return "服务器错误！";
    }
    if(data.errors && Ext.Object.getSize(data.errors) > 0) {
        if(Ext.isObject(data.errors)) {
            data.errors = [data.errors];
        }
        msg = Ext.Array.map(data.errors, function(error){
            var k, info;
            for(k in error) {
                info = error[k];
                if(Ext.isArray(info)) {
                    info = info.join(';');
                }
                break;
            }
            return info;
        });
        return msg.join('<br/>');
    }

    return msg || data.msg;
}


function onItemDelete(title, content, cb){
    if(arguments.length == 1) {
        cb = title;
        title = '提示';
        content = '确定要删除吗？';
    } else if(arguments.length == 2) {
        cb = content,
        content = title;
        title = '提示';
    }
    title = title || '提示';
    Ext.Msg.confirm(title, content, function(b){
        if(b == 'yes') { cb && cb(); }
    });
}

function onResponse(resp, cb, ignore) {
    var data = decodeResponse(resp), msg;
    switch(data.status) {
        case "success":
            cb && cb(data);
            break;
        case "failure":
            msg = '操作失败！';
            msg += '<br/>' + getErrorMsg(data);
            break;
        default:
            msg = '服务器异常！';
            break;
    }
    if(msg) {
        if(typeof ignore == "function") {
            ignore(msg);
        } else if(ignore !== true) {
            Ext.Msg.alert('提示', msg);
        }
    }
}


function timeit(msg) {
    var before = timeit.lastTime, now = new Date().getTime();
    if(before) {
        console.log(msg, now, now - before);
    } else {
        console.log(msg, now);
    }
    timeit.lastTime = now;
}
