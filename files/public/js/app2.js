/*jshint sub:false,expr:true*/
//公用工具集合
Ext.define('bbt.ToolBox', {
    singleton: true,
    get: function(name, defaults) {
        if(name == '->') { return name; }
        if(typeof name == "object") {
            if(name.tool) {
                defaults = name;
                name = defaults.tool;
            } else {
                return name;
            }
        }
        var tool = this._tools[name], config;
        if(typeof tool == "function") {
            config = tool(defaults ? defaults._ : defaults);
        } else {
            config = Ext.clone(tool);
        }
        if(defaults) {
            Ext.apply(config, defaults);
        }
        return config;
    },
    register: function(name, tool){
        var k;
        if(arguments.length === 1) {
            for(k in name) {
                this.register(k, name[k]);
            }
        } else {
            if(name in this._tools) {
                throw new Error('tool ' + name + ' already exists!');
            } else {
                this._tools[name] = tool;
            }
        }
    },
    convert: function(tools){
        var me = this, i, len, ret = [];
        if(typeof tools == "string") {
            return me.get(tools);
        } else if(Ext.isArray(tools)) {
            for(i=0,len=tools.length;i<len;i++) {
                if(Ext.isArray(tools[i])) {
                    ret.push({
                        xtype: 'toolbar',
                        dock: 'top',
                        layout: {overflowHandler: 'Menu'},
                        items: Ext.Array.map(tools[i], function(a){ return me.get(a); })
                    });
                } else {
                    ret.push(me.get(tools[i]));
                }
            }
            return ret;
        }
        return [];
    },
    _tools: {}
});
bbt.ToolBox.register({
    resourceType : function(){
        var store = new Ext.data.Store({
            fields: ['uuid', 'value'],
            data: [{value: '所有'}],
            proxy: {
                type: 'ajax',
                url: '/system/resource/resource-type/',
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            },
            pageSize: 1000,
            listeners: {
                 load: function(s, rcs){
                    s.insert(0, {value: '所有'});
                 }
            }
        });
        store.load();
        return {
            xtype : 'combo',
            name : 'resource_type',
            displayField: 'value',
            valueField: 'uuid',
            submitField: 'value',
            editable: false,
            fieldLabel : '资源类型',
            labelWidth : 60,
            width : 145,
            queryMode: 'local',
            store: store,
            value: '所有'
        };
    },
    resourceFrom: function(){
        var store = new Ext.data.Store({
            fields: ['uuid', 'value'],
            data: [{value: '所有'}],
            proxy: {
                type: 'ajax',
                url: '/system/resource/resource-from/',
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            },
            pageSize: 1000,
            listeners: {
                load: function(s, rcs){
                    s.insert(0, {value: '所有'});
                }
            }
        });
        store.load();
        return {
            xtype : 'combo',
            name : 'resource_from',
            editable: false,
            fieldLabel : '资源来源',
            displayField: 'value',
            valueField: 'uuid',
            submitField: 'value',
            queryMode: 'local',
            labelWidth : 60,
            width : 180,
            store: store,
            value: '所有'
        };
    },
    grade: function(_){
        var combo = {
            xtype: 'combo',
            name: 'grade_name',
            fieldLabel : '年级',
            labelWidth : 40,
            width : 115,
            skipAutoValue: true,
            editable: false,
            displayField: 'name',
            submitField: 'name',
            valueField: 'uuid',
            queryMode: 'local',
            listConfig: {minWidth: 40},
            store: new Ext.data.Store({
                fields: ['uuid', 'name'],
                data: [{name: '所有'}],
                pageSize: 500,
                proxy: {
                    url: '/list/get-grade-class/',
                    type: 'ajax',
                    reader: {
                        type: 'json',
                        root: _ ? _.root : 'data.grade'
                    }
                },
                sorters: [{
                    sorterFn: function(rc1, rc2){
                        var seqMap = {"一": 1,"二": 2,"三": 3,"四": 4,"五": 5,"六": 6,"七": 7,"八": 8,"九": 9,"十": 10},
                            seq1, seq2, getSeq;
                        if(!rc1.get('uuid')) { return -1; }
                        getSeq = function(s){
                            if((s.indexOf('十一') === 0)) { return 11; }
                            if((s.indexOf('十二') === 0)) { return 12; }
                            if(s == "电脑教室") { return 100; }
                            return seqMap[s];
                        };
                        seq1 = getSeq(rc1.get('name'));
                        seq2 = getSeq(rc2.get('name'));
                        return seq1 - seq2;
                    }
                }],
                listeners: {
                    beforeload: bbt.beforeCascadeLoad,
                    load: function(s){
                        var rc, dv;
                        try {
                            s.owner.ownerCt.down('[name=class_name]').store.rawData = s.proxy.reader.rawData.data['class'];
                        } catch(e) { console.log(e); }
                        rc = s.getAt(0);
                        if(!rc || (rc && rc.get('name') != '所有')) {
                            s.insert(0, {name: '所有', uuid: ''});
                        }
                        if(s.expandOnLoad) {
                            dv = s.defaultValueOnLoad;
                            if(s.owner.findRecordByValue(dv)) {
                                s.owner.setValue(dv);
                            }
                            setTimeout(function(){s.owner.expand();}, 1);
                            delete s.expandOnLoad;
                            delete s.defaultValueOnLoad;
                        }
                    }
                }
            }),
            value: '',
            listeners: {
                beforerender: function(){
                    this.store.owner = this;
                },
                change: function(me, v){
                    var rc = me.findRecordByValue(v), cc;
                    cc = me.ownerCt.down('[name=class_name]');
                    cc && rc && cc.updateStore(rc);
                },
                expand: function(){
                    var lastLoadConditions = this.lastLoadConditions,
                        willLoad = false,
                        p = this.up('grid');
                    if(bbt.UserInfo.isSchool()) {
                        if(typeof lastLoadConditions == "undefined") {
                            lastLoadConditions = this.lastLoadConditions = {};
                            willLoad = true;
                        }
                        Ext.each(['school_year', 'term_type', 'start_date', 'end_date'], function(name){
                            var combo = p.down('[name=' + name + ']'), v;
                            if(combo) {
                                v = combo.getValue();
                                if(Ext.isDate(v)) {
                                    v = Ext.Date.format(v, 'Y-m-d');
                                }
                                if(v !== lastLoadConditions[name]) {
                                    lastLoadConditions[name] = v;
                                    willLoad = true;
                                }
                            }
                        });
                        if(willLoad) {
                            this.store.expandOnLoad = true;
                            this.store.defaultValueOnLoad = this.getValue();
                            this.store.load();
                        }
                    }
                }
            }
        };
        return combo;
    },
    gradeOld: function(){
        var store = new Ext.data.Store({
            fields: ['text', 'fulltext', 'value', 'sub'],
            pageSize: 500,
            sorters: [{sorterFn: function(rc1, rc2){
                var seqMap = {"一": 1,"二": 2,"三": 3,"四": 4,"五": 5,"六": 6,"七": 7,"八": 8,"九": 9,"十": 10},
                    seq1, seq2, getSeq;
                if(!rc1.get('value')) { return -1; }
                getSeq = function(s){
                    if((s.indexOf('十一') === 0)) { return 11; }
                    if((s.indexOf('十二') === 0)) { return 12; }
                    if(s == "电脑教室") { return 100; }
                    return seqMap[s];
                };
                seq1 = getSeq(rc1.get('value'));
                seq2 = getSeq(rc2.get('value'));
                return seq1 - seq2;
            }}],
            listeners: {
                beforeload: function(s, op){
                    var me = this, params = op.params||{}, owner = me.owner, p = owner.up('grid');
                    if(owner.byTerm) {
                        Ext.each(['school_year', 'term_type', 'start_date', 'end_date'], function(v){
                            var f = p.down('[name=' + v + ']');
                            if(f) {
                                params[v] = f.getValue();
                            }
                        });
                        params.no_cache = true;
                    }
                    if(owner.computerclass) {
                        params.computerclass_need = true;
                    }
                    if(owner.only_computerclass) {
                        params.only_computerclass = true;
                    }
                    Ext.Ajax.request({
                        method: 'GET',
                        url: me.owner.byTerm ? '/classes1/' : '/classes/',
                        params: params,
                        callback: function(opts, _, resp){
                            var data = Ext.decode(resp.responseText),
                                grades = {}, ret = [], obj, i, len, rcs, g, suffix = me.owner.useSuffix, dv;
                            if(me.owner.displayAll) {
                                ret.push({text:'所有',value:''});
                            }
                            if(data.status !== "success") { return; }
                            for(i=0,len=data.data.length;i<len;i++) {
                                obj = data.data[i];
                                
                                if(!(obj.grade__name in grades)) {
                                    grades[obj.grade__name] = [];
                                }
                                grades[obj.grade__name].push({text: obj.name, value: obj.name});
                            }
                            for(g in grades) {
                                if(suffix) {
                                    ret.push({text: bbt.fullgrade(g), value: g, sub: grades[g]});
                                } else {
                                    ret.push({text: g/*, fulltext: bbt.fullgrade(g)*/, value: g, sub: grades[g]});
                                }
                                
                            }
                            me.loadData(ret);
                            if(me.expandOnLoad) {
                                dv = me.defaultValueOnLoad;
                                if(me.owner.findRecordByValue(dv)) {
                                    me.owner.setValue(dv);
                                }
                                delete me.expandOnLoad;
                                delete me.defaultValueOnLoad;
                                setTimeout(function(){me.owner._ignoreLoad=true;me.owner.expand();}, 1);
                            } else {
                                me.owner.setValue('');
                            }
                        }
                    });
                    return false;
                }
            }
        });
        return {
            xtype: 'combo',
            fieldLabel : '年级',
            labelWidth : 40,
            name: 'grade_name',
            width : 115,
            queryMode : 'local',
            store : store,
            editable: false,
            displayAll: true,
            displayField : 'text',
            valueField : 'value',
            listConfig: {
                minWidth: 40
            },
            listeners: {
                afterrender: function(){
                    var me = this, term;
                    me.store.owner = me;
                    if(me.byTerm) {
                        term = me.ownerCt.down('[name=term_type]');
                        term.on('change', function(){
                            me.store.load();
                        });
                    } else {
                        me.store.load();
                    }
                },
                change:function(me, v) {
                    var rc = me.findRecordByValue(v), clsData = rc ? rc.get('sub') : null, cls;
                    if(!Ext.isArray(clsData)) {
                        clsData = [];
                    }
                    try {
                        cls = me.ownerCt.down('combo[name=class_name]');
                        cls.store.loadData(clsData);
                        if(cls.displayAll) {
                            cls.store.insert(0, {text:'所有',value:''});
                        }
                        cls.setValue('');
                    } catch (e) {}

                },
                expand: function(){
                    var lastLoadConditions = this.lastLoadConditions,
                        willLoad = false,
                        p = this.up('grid');
                    if(bbt.UserInfo.isSchool()) {
                        if(typeof lastLoadConditions == "undefined") {
                            lastLoadConditions = this.lastLoadConditions = {};
                            willLoad = true;
                        }
                        Ext.each(['school_year', 'term_type', 'start_date', 'end_date'], function(name){
                            var combo = p.down('[name=' + name + ']'), v;
                            if(combo) {
                                v = combo.getValue();
                                if(Ext.isDate(v)) {
                                    v = Ext.Date.format(v, 'Y-m-d');
                                }
                                if(v !== lastLoadConditions[name]) {
                                    lastLoadConditions[name] = v;
                                    willLoad = true;
                                }
                            }
                        });
                        if(willLoad) {
                            this.store.expandOnLoad = true;
                            this.store.defaultValueOnLoad = this.getValue();
                            this.store.load({params: lastLoadConditions});
                        }
                    }
                }
            }
        };
    },
    computerclass: function(){
        var store, dv = '所有';
        var store = new Ext.data.Store({
            fields: ['name'],
            proxy: {
                type: 'ajax',
                url: '/classes/',
                extraParams: {only_computerclass: true},
                reader: {
                    type: 'json',
                    root: 'data'
                }
            },
            data: [{name: dv}],
            listeners: {
                beforeload: bbt.beforeCascadeLoad,
                load: function(s){
                    s.insert(0, {name: dv});
                    s.owner.setValue(dv);
                    if(s.expandOnLoad) {
                        s.owner.expand();
                        dv = s.defaultValueOnLoad;
                        if(s.owner.findRecordByValue(dv)) {
                            s.owner.setValue(dv);
                        }
                        delete s.expandOnLoad;
                        delete s.defaultValueOnLoad;
                    }
                }
            }
        });
        return {
            xtype: 'combo',
            fieldLabel : '电脑教室',
            labelWidth : 60,
            name: 'name',
            width : 145,
            queryMode : 'local',
            store : store,
            editable: false,
            displayField : 'name',
            valueField : 'name',
            listConfig: {
                minWidth: 40
            },
            value: dv,
            listeners: {
                afterrender: function(){
                    var me = this, term;
                    me.store.owner = me;
                    me.store.load();
                },
                expand: function(){
                    var lastLoadConditions = this.lastLoadConditions,
                        willLoad = false,
                        p = this.up('toolbar');
                    if(bbt.UserInfo.isSchool()) {
                        if(typeof lastLoadConditions == "undefined") {
                            lastLoadConditions = this.lastLoadConditions = {};
                            willLoad = true;
                        }
                        Ext.each(['school_year', 'term_type', 'start_date', 'end_date'], function(name){
                            var combo = p.down('[name=' + name + ']'), v;
                            if(combo) {
                                v = combo.getValue();
                                if(Ext.isDate(v)) {
                                    v = Ext.Date.format(v, 'Y-m-d');
                                }
                                if(v !== lastLoadConditions[name]) {
                                    lastLoadConditions[name] = v;
                                    willLoad = true;
                                }
                            }
                        });
                        if(willLoad) {
                            this.store.expandOnLoad = true;
                            this.store.defaultValueOnLoad = this.getValue();
                            this.store.load();
                        }
                    }
                }
            }
        };
    },
    'class' : function(){
        var store = new Ext.data.Store({
            fields:['name','uuid'],
            data: [{name: '所有'}],
            sorters: [{property: 'name', sorterFn: function(rc1, rc2){
                if(!rc1.get('name')) { return -1; }
                return parseInt(rc1.get('name')) - parseInt(rc2.get('name'));
            }}]
        });
        return {
            xtype : 'combo',
            name : 'class_name',
            fieldLabel : '班级',
            store: store,
            skipAutoValue: true,
            value: '',
            listConfig: {
                minWidth: 40
            },
            queryMode: 'local',
            displayField: 'name',
            valueField: 'uuid',
            submitField: 'name',
            editable: false,
            labelWidth : 40,
            width : 95,
            updateStore: function(rc){
                var s = this.store, raw = s.rawData, data = [{name: '所有'}], v = rc.get(this.valueField);
                s.removeAll();
                if(v) {
                    Ext.each(raw, function(item){
                        if(item.grade === v) {
                            data.push(item);
                        }
                    });
                }
                s.add(data);
                this.setValue('');
            }
        };
    },
    classOld: function(){
        var store = new Ext.data.Store({
            fields:['text','value'],
            data:[{text:'所有',value:''}],
            sorters: [{property: 'text', sorterFn: function(rc1, rc2){
                if(!rc1.get('value')) { return -1; }
                return parseInt(rc1.get('value')) - parseInt(rc2.get('value'));
            }}]
        });
        return {
            xtype : 'combo',
            name : 'class_name',
            fieldLabel : '班级',
            displayAll: true,
            store: store,
            value: '',
            listConfig: {
                minWidth: 40
            },
            queryMode: 'local',
            displayField: 'text',
            valueField: 'value',
            editable: false,
            labelWidth : 40,
            width : 95
        };
    },
    jieci: function(){
        var store = new Ext.data.Store({
            fields: ["sequence", 'uuid'],
            data: [{sequence: '所有'}],
            sorters: [{property: 'sequence', direction: 'ASC'}],
            proxy: {
                type: 'ajax',
                url: '/list/get-lesson-period/',
                reader: {
                    type: 'json',
                    root: 'data.lesson_period'
                }
            },
            pageSize: 1000,
            listeners: {
                beforeload: bbt.beforeCascadeLoad,
                load: function(s, rcs){
                    var rc = s.getAt(0);
                    if(!rc || (rc && rc.get('sequence') != '所有')) {
                        s.insert(0, {sequence:'所有'});
                    }
                    if(s.expandOnLoad) {
                        s.owner.expand();
                        dv = s.defaultValueOnLoad;
                        if(s.owner.findRecordByValue(dv)) {
                            s.owner.setValue(dv);
                        }
                        delete s.expandOnLoad;
                        delete s.defaultValueOnLoad;
                    }
                }
            }
        });
        return {
            xtype: 'combo',
            name: 'lesson_period',
            fieldLabel : '节次',
            store: store,
            skipAutoValue: true,
            listConfig: {
                minWidth: 40
            },
            queryMode: 'local',
            displayField: 'sequence',
            valueField: 'uuid',
            submitField: 'sequence',
            editable: false,
            labelWidth : 40,
            width : 100,
            value: '',
            listeners: {
                beforerender: function(){
                    this.store.owner = this;
                },
                expand: function(){
                    var lastLoadConditions = this.lastLoadConditions,
                        willLoad = false,
                        p = this.ownerCt.ownerCt;
                    if(bbt.UserInfo.isSchool()) {
                        if(typeof lastLoadConditions == "undefined") {
                            lastLoadConditions = this.lastLoadConditions = {};
                            willLoad = true;
                        }
                        Ext.each(['school_year', 'term_type', 'start_date', 'end_date'], function(name){
                            var combo = p.down('[name=' + name + ']'), v;
                            if(combo) {
                                v = combo.getValue();
                                if(Ext.isDate(v)) {
                                    v = Ext.Date.format(v, 'Y-m-d');
                                }
                                if(v !== lastLoadConditions[name]) {
                                    lastLoadConditions[name] = v;
                                    willLoad = true;
                                }
                            }
                        });
                        if(willLoad) {
                            this.store.expandOnLoad = true;
                            this.store.defaultValueOnLoad = this.getValue();
                            this.store.load();
                        }
                    }
                }
            }
        };
    },
    jieciOld: function(){
        var store = new Ext.data.Store({
            fields: ["sequence"],
            data: [{sequence: '所有'}],
            sorters: [{property: 'sequence', direction: 'ASC'}],
            proxy: {
                type: 'ajax',
                url: '/system/lesson-period/list-sequence/',
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            },
            pageSize: 1000,
            listeners: {
                load: function(s, rcs){
                    s.insert(0, {sequence:'所有'});
                }
            }
        });
        store.load();
        return {
            xtype: 'combo',
            name: 'lesson_period',
            fieldLabel : '节次',
            store: store,
            skipAutoValue: true,
            listConfig: {
                minWidth: 40
            },
            queryMode: 'local',
            displayField: 'sequence',
            valueField: 'sequence',
            editable: false,
            labelWidth : 40,
            width : 100,
            value: '',
            listeners: {
                
            }
        };
    },
    qdate: {
        xtype: 'combo',
        fieldLabel: '时间范围',
        editable: false,
        labelWidth: 60,
        name: '_',
        width: 140,
        store: [['7', '近一周'], ['1m', '近一个月'], ['3m', '近三个月'], ['custom', '自定义']],
        listeners: {
            change: function(me, v){
                var now, ms, sd, ed;
                sd = me.up('toolbar').down('datefield[name=start_date]');
                ed = me.up('toolbar').down('datefield[name=end_date]');
                if(v === '') {
                    sd.setDisabled(true);
                    sd.setValue('');
                    ed.setDisabled(true);
                    ed.setValue('');
                } else if(v == 'custom') {
                    sd.setDisabled(false);
                    ed.setDisabled(false);
                } else if(/^\d+m?$/.test(v)) {
                    sd.setDisabled(true);
                    ed.setDisabled(true);
                    ed.setValue(new Date());
                    now = new Date();
                    ms = parseInt(v);
                    if(v.indexOf('m') == -1) {
                        now.setDate(now.getDate() - ms);
                    } else {
                        now.setMonth(now.getMonth() - ms);
                    }
                    sd.setValue(now);
                }
            },
            afterrender: function(){
                var me = this;
                setTimeout(function(){ me.setValue('7'); }, 10);
            }
        }
    },
    startDate : {
        xtype : 'datefield',
        name : 'start_date',
        allowBlank: false,
        fieldLabel : '开始',
        editable: false,
        format: 'Y-m-d',
        labelWidth : 40,
        disabled: true,
        width : 140,
        validator: function(){
            var me = this, sv = me.getValue(), end, ev;
            end = me.up('toolbar').down('datefield[name=end_date]');
            ev = end.getValue();
            if(!sv && !ev) {
                me.allowBlank = true;
                end.allowBlank = true;
                return true;
            }
            if(ev) {
                if(sv > ev) {
                    return '开始时间不能大于结束时间！';
                } else {
                    end.validate();
                }
            } else {
                end.allowBlank = false;
                end.expand();
            }

            return true;
        }
    },
    endDate: {
        xtype : 'datefield',
        name : 'end_date',
        allowBlank: false,
        fieldLabel : '结束',
        editable: false,
        format: 'Y-m-d',
        labelWidth : 40,
        disabled: true,
        width : 140,
        validator: function(){
            var me = this, ev = me.getValue(), start ,sv;
            start = me.up('toolbar').down('datefield[name=start_date]');
            sv = start.getValue();
            if(!sv && !ev) {
                me.allowBlank = true;
                start.allowBlank = true;
                return true;
            }
            //in this case, allowBlank will validate failure, just return
            if(ev === null) {
                return true;
            }
            if(sv) {
                if(sv > ev) {
                    return '开始时间不能大于结束时间！';
                }
            } else {
                start.allowBlank = false;
                start.expand();
            }

            return true;
        }
    },
    queryMethod: {
        xtype : 'combo',
        name : '_',
        fieldLabel : '查询方式',
        queryMode: 'local',
        store: [['', '按学年学期'], ['natural', '按自然时间']],
        editable: false,
        labelWidth : 60,
        width : 160,
        defaultValue: '',
        _loaded: false,
        listeners: {
            afterrender: function(){
                this.setValue(this.defaultValue);
                //this.fireEvent(me, '');
            },
            change: function(me, v){
                var school_year, term, sd, ed, d;
                school_year = me.up('toolbar').down('combo[name=school_year]');
                term = me.up('toolbar').down('combo[name=term_type]');
                sd = me.up('toolbar').down('datefield[name=start_date]');
                ed = me.up('toolbar').down('datefield[name=end_date]');
                if(v == "natural") {
                    school_year.setDisabled(true);
                    school_year.setValue('');
                    term.setDisabled(true);
                    term.setValue('');
                    sd.setDisabled(false);
                    sd.setValue(new Date());
                    ed.setDisabled(false);
                    d = new Date();
                    d.setDate(d.getDate() - 7);
                    sd.setValue(d);
                    ed.setValue(new Date());
                } else {
                    school_year.setDisabled(false);
                    school_year.setValue('');
                    term.setDisabled(false);
                    term.setValue('');
                    sd.setDisabled(true);
                    sd.setValue(undefined);
                    ed.setDisabled(true);
                    ed.setValue(undefined);
                    me.store.loading = true;
                    bbt.loadCurrentSchoolYear(function(opts, _, resp){
                        var data = Ext.decode(resp.responseText), timer;
                        if(data.status == "success") {
                            timer = setInterval(function(){
                                if(school_year._loaded) {
                                    try {
                                        school_year.setValue(data.data.school_year);
                                        term.setValue(data.data.term_type);
                                    } catch(e) {
                                        //when fast navigate between function modules, code will goes here
                                    }
                                    clearInterval(timer);
                                }
                            }, 5);
                        }
                        me.store.loading = false;
                        me._loaded = true;
                    });
                }
            }
        }
    },
    queryMethodEx: {
        xtype : 'combo',
        name : '_',
        fieldLabel : '查询方式',
        queryMode: 'local',
        store: [['7', '近一周'], ['1m', '近一个月'], ['3m', '近三个月'], ['natural', '按自然时间'], ['term', '按学年学期']],
        editable: false,
        defaultValue: '7',
        labelWidth : 60,
        width : 160,
        listeners: {
            afterrender: function(){
                this.setValue(this.defaultValue);
            },
            change: function(me, v){
                var school_year, term, sd, ed, dre, d1, d2, mx;
                school_year = me.up('toolbar').down('combo[name=school_year]');
                term = me.up('toolbar').down('combo[name=term_type]');
                sd = me.up('toolbar').down('datefield[name=start_date]');
                ed = me.up('toolbar').down('datefield[name=end_date]');
                if(v == "term") {
                    school_year.setDisabled(false);
                    school_year.setValue('');
                    term.setDisabled(false);
                    term.setValue('');
                    sd.setDisabled(true);
                    sd.setValue(undefined);
                    ed.setDisabled(true);
                    ed.setValue(undefined);
                    me.store.loading = true;
                    bbt.loadCurrentSchoolYear(function(opts, _, resp){
                        var data = Ext.decode(resp.responseText);
                        if(data.status == "success") {
                            school_year.setValue(data.data.school_year);
                            term.setValue(data.data.term_type);
                        }
                        me.store.loading = false;
                    });
                } else {
                    school_year.setDisabled(true);
                    school_year.setValue('');
                    term.setDisabled(true);
                    term.setValue('');
                    sd.setDisabled(true);
                    ed.setDisabled(true);

                    dre = /^(\d+)m$/;
                    if(v == '7') {
                        d1 = new Date();
                        d1.setDate(d1.getDate()-7);
                        d2 = new Date();
                    } else if(dre.test(v)) {
                        mx = dre.exec(v)[1];
                        d1 = new Date();
                        d1.setMonth(d1.getMonth()-mx);
                        d2 = new Date();
                    } else {
                        d1 = new Date();
                        d1.setDate(d1.getDate()-7);
                        d2 = new Date();
                        sd.setDisabled(false);
                        ed.setDisabled(false);
                    }
                    if(d1 && d2) {
                        sd.setValue(d1);
                        ed.setValue(d2);
                        ed.collapse();
                    }
                }
            }
        }
    },
    schoolYear: function(){
        var store = new Ext.data.Store({
            fields: ["school_year", 'terms', 'start_date', 'end_date'],
            pageSize: 100,
            listeners: {
                beforeload: function(s, rcs){
                    Ext.Ajax.request({
                        url: bbt.UserInfo.isSchool() ? '/system/term/list/' : '/system/newterm/list/',
                        callback: function(_1, _2, resp){
                            var data = Ext.decode(resp.responseText), ret = {}, rc;
                            if(data.status == "success") {
                                Ext.each(data.data.records, function(item){
                                    //if(item.deleted) { return; }
                                    if(!(item.school_year in ret)) {
                                        item.terms = [{text:item.term_type, start_date: item.start_date, end_date: item.end_date}];
                                        delete item.term_type;
                                        ret[item.school_year] = item;
                                    } else {
                                        ret[item.school_year].terms.push({text:item.term_type, start_date: item.start_date, end_date: item.end_date});
                                    }
                                });
                                rc = Ext.Object.getValues(ret);
                                if(rc.length) {
                                    s.loadData(rc);
                                    if(s.owner) {
                                        if(s.owner.useFirst) {
                                            s.owner.setValue(rc[0].school_year);
                                        } else if(s.owner.useCurrent) {
                                            s.owner.loadCurrent();
                                        }
                                    }
                                }
                            }
                            s.owner._loaded = true;
                        }
                    });
                    return false;
                }
            }
        });
        return {
            xtype: 'combo',
            name: 'school_year',
            fieldLabel : '学年',
            store: store,
            queryMode: 'local',
            displayField: 'school_year',
            valueField: 'school_year',
            editable: false,
            labelWidth : 40,
            width : 130,
            _loaded: false,
            loadCurrent: function(){
                var me = this;
                bbt.loadCurrentSchoolYear(function(opts, _, resp){
                    var data = Ext.decode(resp.responseText), sy, term;
                    if(data.status == "success") {
                        sy = data.data.school_year;
                        term = data.data.term_type;
                        me.setValue(sy);
                        me.ownerCt.down('[name=term_type]').setValue(term);
                    }
                });
            },
            listeners: {
                afterrender: function(){
                    this.store.owner = this;
                    this.store.load();
                },
                change: function(me, v){
                    var rc = me.findRecordByValue(v), term, dv;
                    if(rc) {
                        term = me.ownerCt.down('[name=term_type]');
                        if(!term) { return; }
                        dv = term.getValue();
                        term.store.loadData(rc.get('terms'));
                        if(term.findRecordByValue(dv)) {
                            term.setValue(dv);
                        } else {
                            term.setValue(rc.get('terms')[0].text);
                        }
                        if(term.getValue() == dv) {
                            term.fireEvent('change', term, dv);
                        }
                    }
                }
            }
        };
    },
    iTeacherName: {
        xtype: 'textfield',
        name: 'teacher_name',
        labelWidth: 60,
        fieldLabel: '授课教师',
        qtip: '输入教师姓名',
        maxLength: 100,
        width: 160,
        listeners: {
            boxready: function(){
                bbt.utils.makeTipFor(this.qtip, this.getInputId());
            }
        }
    },
    teacherName : function(){
        var store = new Ext.data.Store({
            fields: ['text', 'value', 'name', 'uuid', 'birthday'],
            proxy: {
                type: 'ajax',
                url: '/system/teacher/list/',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            },
            sorters: [{property: 'name'}],
            pageSize: 1000,
            listeners: {
                load: function(s, rcs){
                    s.each(function(rc){
                        rc.data.text = rc.data.value = rc.get('name');
                    });
                    s.insert(0, {text:'所有',value:''});
                }
            }
        });
        store.load();
        return {
            xtype : 'combo',
            name : 'teacher_name',
            fieldLabel : '授课教师',
            labelWidth : 60,
            width : 160,
            hideTrigger: true,
            store: store,
            displayField: 'text',
            valueField: 'value',
            value: '',
            queryMode: 'local',
            typeAhead: true,
            validator: function(){
                var v = this.getValue();
                return this.findRecordByValue(v) ? true : '请选择教师';
            },
            listeners: {
                boxready: function(){
                    var me = this;
                    Ext.create('Ext.tip.ToolTip', {
                        target: me.getInputId(),
                        html: '输入教师名字可以快速选择哦'
                    });
                }
            }
        };
    },
    assetReportType: {
        xtype : 'combo',
        name : 'log_type',
        fieldLabel : '申报类型',
        labelWidth : 60,
        width : 120,
        queryModel : 'local',
        value: '',
        editable: false,
        store: [['', '所有'], ['新增', '新增'], ['停用', '停用']]
    },
    assetname: {
        xtype : 'textfield',
        name : 'name',
        fieldLabel : '资产名称',
        labelWidth : 60,
        emptyText: '请输入资产名称',
        width : 160
    },
    report_user: {
        xtype : 'textfield',
        name : 'reported_by',
        fieldLabel : '申报用户',
        maxLength: 20,
        labelWidth : 60,
        qtip: '输入申报用户',
        width : 160,
        listeners: {
            boxready: function(){
                Ext.create('Ext.tip.ToolTip', {
                    target: this.getInputId(),
                    html: this.qtip
                });
            }
        }
    },
    course : function(){
        var store = new Ext.data.Store({
            fields: ['name'],
            data: [{name: '所有'}],
            proxy: {
                type: 'ajax',
                url: '/list/get-lesson-name/',
                reader: {
                    type: 'json',
                    root: 'data.lesson_name'
                }
            },
            pageSize: 1000,
            listeners: {
                beforeload: bbt.beforeCascadeLoad,
                load: function(s, rcs){
                    var rc = s.getAt(0), dv;
                    if(!rc || (rc && rc.get('name') != "所有")) {
                        s.insert(0, {name:'所有'});
                    }
                    if(s.expandOnLoad) {
                        s.owner.expand();
                        dv = s.defaultValueOnLoad;
                        if(s.owner.findRecordByValue(dv)) {
                            s.owner.setValue(dv);
                        }
                        delete s.expandOnLoad;
                        delete s.defaultValueOnLoad;
                    } else {
                        s.owner.setValue('所有');
                    }
                }
            }
        });
        
        return {
            xtype : 'combo',
            name : 'lesson_name',
            fieldLabel : '课程',
            editable:false,
            skipAutoValue: true,
            labelWidth : 40,
            width : 135,
            displayField: 'name',
            valueField: 'name',
            submitField: 'name',
            queryMode: 'local',
            store : store,
            value: '所有',
            listeners: {
                beforerender: function(){
                    this.store.owner = this;
                },
                expand: function(){
                    var lastLoadConditions = this.lastLoadConditions,
                        willLoad = false,
                        p = this.up('grid');
                    if(bbt.UserInfo.isSchool()) {
                        if(typeof lastLoadConditions == "undefined") {
                            lastLoadConditions = this.lastLoadConditions = {};
                            willLoad = true;
                        }
                        Ext.each(['school_year', 'term_type', 'start_date', 'end_date'], function(name){
                            var combo = p.down('[name=' + name + ']'), v;
                            if(combo) {
                                v = combo.getValue();
                                if(Ext.isDate(v)) {
                                    v = Ext.Date.format(v, 'Y-m-d');
                                }
                                if(v !== lastLoadConditions[name]) {
                                    lastLoadConditions[name] = v;
                                    willLoad = true;
                                }
                            }
                        });
                        if(willLoad) {
                            this.store.expandOnLoad = true;
                            this.store.defaultValueOnLoad = this.getValue();
                            this.store.load();
                        }
                    }
                }
            }
        };
    },
    courseOld: function(){
        var store = new Ext.data.Store({
            fields: ['name'],
            proxy: {
                type: 'ajax',
                url: '/system/lesson-name/list/',
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            },
            pageSize: 1000,
            listeners: {
                load: function(s, rcs){
                    var rc = s.getAt(0), dv;
                    if(s.owner.displayAll) {
                        if(!rc || (rc && rc.get('name') != "所有")) {
                            s.insert(0, {name:'所有'});
                        }
                        s.owner.setValue('所有');
                    }
                    
                }
            }
        });
        
        return {
            xtype : 'combo',
            name : 'lesson_name',
            fieldLabel : '课程',
            editable:false,
            skipAutoValue: true,
            labelWidth : 40,
            width : 135,
            displayAll: true,
            displayField: 'name',
            valueField: 'name',
            submitField: 'name',
            queryMode: 'local',
            store : store,
            listeners: {
                afterrender: function(){
                    this.store.owner = this;
                    this.store.load();
                }
            }
        };
    },
    assetType: function(){
        var store = new Ext.data.Store({
            fields: ['name', 'uuid'],
            proxy: {
                type: 'ajax',
                url: '/asset/asset-type/',
                reader: {
                    type: 'json',
                    root: 'data.records'
                },
                extraParams: {distinct: true}
            },
            listeners: {
                load: function(s, rcs){
                    var rc = s.getAt(0);
                    if(s.owner.displayAll) {
                        if(!rc || (rc && rc.get('name') != "所有")) {
                            s.insert(0, {name: '所有'});
                        }
                        s.owner.setValue('所有');
                    }
                }
            }
        });
        return {
            xtype : 'combo',
            name : 'asset_type',
            editable: false,
            fieldLabel : '资产类型',
            labelWidth : 60,
            width : 160,
            queryModel : 'local',
            store: store,
            displayField: 'name',
            valueField: 'name',
            submitField: 'name',
            displayAll: true,
            listeners: {
                afterrender: function(){
                    this.store.owner = this;
                    this.store.load();
                }
            }
        };
    },
    iDeviceModel: {
        xtype: 'textfield',
        name: 'device_model',
        fieldLabel: '设备型号',
        maxLength: 100,
        labelWidth: 60,
        width: 160,
        qtip: '输入设备型号',
        listeners: {
            boxready: function(){
                Ext.create('Ext.tip.ToolTip', {
                    target: this.getInputId(),
                    html: this.qtip
                });
            }
        }
    },
    deviceModel: function(){
        var store = new Ext.data.Store({
            fields: ['uuid', 'device_model'],
            proxy: {
                type:'ajax',
                url:'',
                reader: {
                    type: 'json',
                    root: 'data.records'
                },
                extraParams: {status: '在用'}
            }
        });
        return {
            xtype : 'combo',
            name : 'device_model',
            fieldLabel : '设备型号',
            labelWidth : 60,
            editable: false,
            hideTrigger: true,
            width : 160,
            queryMode: 'local',
            displayField: 'device_model',
            valueField: 'device_model',
            store: store
        };
    },
    remark: {
        xtype : 'textfield',
        name : 'remark',
        fieldLabel : '备注',
        labelWidth : 40,
        maxLength: 180,
        qtip: '输入备注',
        width : 160,
        listeners: {
            boxready: function(){
                Ext.create('Ext.tip.ToolTip', {
                    target: this.getInputId(),
                    html: this.qtip
                });
            }
        }
    },
    assetStatus: {
        xtype : 'combo',
        name : 'status',
        fieldLabel : '资产状态',
        editable: false,
        labelWidth : 60,
        width : 125,
        queryModel : 'local',
        value: '在用',
        store: [['', '所有'], ['在用', '在用'], ['停用', '停用']],
        queryMode: 'local'
    },
    year : function(){
        var y = new Date().getFullYear(), r=[{text: '所有', value: ''}], len = -2, store;
        while(len++<10){
            r.push({text: y-len, value: y-len});
        }
        store = new Ext.data.Store({fields: ['text', 'value'], data: r});
        return {
            xtype : 'combo',
            name : 'year',
            fieldLabel : '年份',
            labelWidth : 40,
            width : 105,
            queryModel : 'local',
            editable: false,
            displayField: 'text',
            valueField: 'value',
            value: '',
            listeners: {
                change: function(me, v){
                    var mc = me.up('toolbar').down('combo[name=month]');
                    if(mc) {
                        if(v) { mc.isDisabled() ? mc.setDisabled(false) : ''; }
                        else { mc.setDisabled(true); mc.setValue(undefined); }
                    }
                }
            },
            store : store
        };
    },
    month : function(){
        var i=1,d=[['', '所有']];
        for(;i<=12;i++){
            d.push([i+'', i+'月份']);
        }
        return {
            xtype : 'combo',
            name : 'month',
            fieldLabel : '月份',
            labelWidth : 40,
            editable: false,
            disabled: true,
            width : 140,
            queryMode : 'local',
            value: '',
            multiSelect: true,
            store : d,
            listeners: {
                change: function(me, v){
                    var day = me.up('toolbar').down('combo[name=day]'),
                        store, maxDayInStore, i = 1, cy, runDay;
                    if(!day) { return; }
                    store = day.store;
                    maxDayInStore = store.getAt(store.count()-1).get(me.valueField)*1;
                    if(v in {'1':'','3':'','5':'','7':'','8':'','10':'','12':''}) {
                        if(maxDayInStore < 31) {
                            for(;i<maxDayInStore;i++) { store.add({text:''+i, value:''+i}); }
                        }
                    } else if (v in {'4':'','6':'','9':'','11':''}) {
                        if(maxDayInStore === 31) {
                            store.remove(store.getAt(store.count()-1));
                        } else if(maxDayInStore < 30) {
                            for(;i<maxDayInStore;i++) { store.add({text:''+i, value:''+i}); }
                        }
                    } else if(v == '2') {
                        cy = new Date().getFullYear();
                        runDay = (cy/4===0&&cy/100!==0||cy/400===0) ? 29 : 28;
                        if(runDay < maxDayInStore) {
                            i = maxDayInStore;
                            for(;i!=runDay;i--) {
                                store.remove(store.getAt(store.count()-1));
                            }
                        } else if(runDay > maxDayInStore) {
                            for(;i<maxDayInStore;i++) { store.add({text:''+i, value:''+i}); }
                        }
                    }
                }
            }
        };
    },
    edubg: {
        xtype: 'combo',
        name: 'edu_background',
        editable: false,
        fieldLabel: '学历',
        labelWidth: 40,
        width: 120,
        value: '',
        store: [['', '所有'], ['大专', '大专'], ['本科', '本科'], ['硕士', '硕士'], ['博士', '博士'], ['其他', '其他']]
    },
    sex: {
        xtype: 'combo',
        name: 'sex',
        fieldLabel: '性别',
        labelWidth: 40,
        width: 120,
        editable: false,
        value: '',
        store: [['', '所有'], ['男', '男'], ['女', '女']]
    },
    ttitle: {
        xtype: 'combo',
        name: 'title',
        fieldLabel: '教师职称',
        labelWidth: 60,
        width: 140,
        value: '',
        editable: false,
        store: [['', '所有'], ['正高级', '正高级'], ['高级', '高级'], ['一级', '一级'], ['二级', '二级'], ['三级', '三级']]
    },
    tstatus: {
        xtype: 'combo',
        name: 'status',
        fieldLabel: '状态',
        labelWidth: 40,
        width: 120,
        editable: false,
        value: '',
        store: [['', '所有'], ['授课', '授课'], ['停课', '停课']]
    },
    faketb: {
        xtype: 'tbtext',
        cls: 'icon-toolbar',
        width: 10,
        height: 20,
        style: {marginLeft: '10px', marginTop: '-1px', marginBottom: '-1px'}
    },
    day : {
        xtype : 'combo',
        name : 'day',
        fieldLabel : '日',
        labelWidth : 25,
        width : 105,
        queryMode : 'local',
        store : new Ext.data.Store({fields:['text','value']}),
        displayField : 'text',
        valueField : 'value'
    },
    term: function(){
        return {
            xtype: 'combo',
            fieldLabel: '学期',
            labelWidth: 40,
            width: 120,
            name: 'term_type',
            editable: false,
            value: '',
            displayField: 'text',
            valueField: 'text',
            queryMode: 'local',
            store: new Ext.data.Store({fields: ['text', 'start_date', 'end_date']})
        };
    },
    query : {
        xtype : 'button',
        text : '查询',
        iconCls: 'icon-query',
        action: 'query',
        handler: function(){
            var me = this, toolbar = this.up('toolbar[dock=top]'), fields = [], params={}, owner, op, isValid = true;
            owner = toolbar.ownerCt;
            Ext.each(owner.query('toolbar[dock=top]'), function(tb){
                var cFields = tb.query('field[name]');
                fields = fields.concat(cFields);
            });
            Ext.each(fields, function(f){
                var v = f.getValue(), rc;
                if(f.submitField) {
                    rc = f.findRecordByValue(v);
                    if(rc) {
                        v = rc.get(f.submitField);
                    }
                    
                }
                if(f.name == '_') { return; }
                if(f.isValid()) {
                    if(Ext.isDate(v)) {
                        v = Ext.Date.format(v, f.format);
                    }
                    params[f.name] = v == '所有' ? '' : v;
                } else {
                    isValid = false;
                    Ext.Msg.alert('提示', f.getActiveError(), function(){
                        switch(f.xtype) {
                            case 'combo':
                            case 'datefield':
                                f.expand(); break;
                            case 'textfield':
                                f.focus();
                        }
                    });
                    return false;
                }
            });
            if(!isValid) {
                return;
            }

            if(owner.store) {
                owner.store.currentPage = 1;
                if(!owner.store.proxy.extraParams) {
                    owner.store.proxy.extraParams = {};
                }
                Ext.apply(owner.store.proxy.extraParams, params);
                owner.store.load();
            }

        }
    },
    viewReport: {
        xtype: 'button',
        text: '报表显示',
        handler: function(){
            var grid = this.up('grid');
            if(!grid) { return; }
            var c = grid.chart, config;
            if(!c) {
                Ext.Msg.alert('提示', '报表不可用！');
                return;
            }
            config = {
                title: c.title,
                autoShow: true,
                width: 800,
                height: 480,
                modal: true,
                layout: 'fit',
                items: [{
                    xtype: 'chart',
                    style: {backgroundColor: '#FFF'},
                    shadow: true,
                    theme: 'bbt',
                    legend: {position: 'right', update: false},
                    store: grid.store,
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: c.y.push ? c.y : [c.y],
                        title: c.ytitle,
                        grid: true,
                        minimum: 0,
                        maximum: 10,
                        adjustMaximumByMajorUnit: 1
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: c.x.push ? c.x : [c.x],
                        title: c.xtitle,
                        label: {color: "#000", rotate: {degrees: 300}}
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        gutter: 80,
                        showInLegend: true,
                        highlight: true,
                        style: {width: 35},
                        title: c.seriesTitle,
                        xField: c.x,
                        yField: c.y,
                        label: {
                            display: 'outside',
                            //contrast: true,
                            color: '#000',
                            field: c.y
                        }
                    }],
                    listeners: {
                        beforerender: function(){
                            var store = this.store,
                                axis = this.axes.getAt(0),
                                fields = axis.fields, max = 0;
                            store.each(function(rc){
                                var i, len, tmp;
                                for(i=0,len=fields.length;i<len;i++) {
                                    tmp = rc.get(fields[i])||0;
                                    max = max > tmp ? max : tmp;
                                }
                            });
                            max = max < 10 ? 10 : max;
                            this.series.getAt(0);
                            axis.maximum = max;
                        },
                        afterrender: function(){
                            var items = this.legend.items;
                            setTimeout(function(){
                                Ext.each(items, function(item) {
                                    item.un('mousedown', item.events.mousedown.listeners[0].fn);
                                });
                            });
                        }
                    }
                }],
                listeners: {
                    afterrender: function(){
                        var win = this, cb = function(){
                            win.center();
                        };
                        Ext.get(window).on('resize', cb);
                        win.on('beforedestroy', function(){
                            Ext.get(window).un('resize', cb);
                        });
                    }
                }
            };
            Ext.create('Ext.window.Window', config);
        }
    },
    'export': {
        text: '导出',
        iconCls: 'tool-icon icon-export',
        handler: function(){
            var grid = this.up('grid'), params;
            if(!grid.exportUrl) {
                alert('没有配置导出 url');
                return;
            }
            if(grid) {
                params = grid.store.lastOptions.params || grid.store.proxy.extraParams;
            }
            Ext.Ajax.request({
                url:grid.exportUrl,
                params: params,
                success: function(resp){
                    var data;
                    try {
                        data = Ext.decode(resp.responseText);
                        if(data.status == "success") {
                            downloadFile(data.url, '');
                        } else {
                            Ext.Msg.alert('提示', data.msg);
                        }
                    } catch(e) {
                        data = data || {};
                        Ext.Msg.alert('提示', data.msg||'服务器错误！');
                    }
                },
                failure: function(resp){
                    var data;
                    try {
                        data = Ext.decode(resp.responseText);
                        Ext.Msg.alert('提示', getErrorMsg(data));
                    } catch(e) {}
                }
            });
        }
    },
    assetFrom: {
        xtype: 'combo',
        fieldLabel: '资产来源',
        editable: false,
        value: '',
        store: [['', '所有'],['校自主采购', '校自主采购'], ['县级电教采购', '县级电教采购'], ['地级电教采购', '地级电教采购'], ['省级电教采购', '省级电教采购'], ['其他', '其他']],
        name: 'asset_from',
        labelWidth: 60,
        width: 160
    },
    asset_repair: {
        text: '资产报修',
        handler: function(){
            var winc, assetType, model, grade, clazz, dataCB, gridTarget;
            assetType = bbt.ToolBox.get('assetType', {displayAll: false});
            assetType.store.proxy.url = "/asset/asset-type/get-assettype-for-repair/";
            assetType.valueField = 'uuid';
            delete assetType.labelWidth;
            //remove: ['', '所有']
            Ext.merge(assetType, {
                listeners: {
                    change: function(me, v){
                        var rc = me.findRecordByValue(v), murl, cm;
                        murl = '/asset/get-devicemodel-by-assettype/?uuid=' + rc.raw.uuid;
                        cm = me.ownerCt.down('[name=device_model]');
                        cm.store.proxy.url = murl;
                        cm.setValue('');
                        cm.store.load();
                    }
                }
            });
            model = bbt.ToolBox.get('deviceModel');
            model.editable = false;
            delete model.hideTrigger;
            Ext.merge(model, {
                listeners: {
                    change: function(me, v){
                        var rc = me.findRecordByValue(v);
                        if(rc) {
                            me.up('form').getForm().findField('asset').setValue(rc.raw.uuid);
                        }
                    }
                }
            });
            delete model.labelWidth;
            grade = bbt.ToolBox.get('gradeOld', {displayAll: false, computerclass: true/*labelWidth:0, fieldLabel: '', emptyText: '请选择年级'*/});
            delete grade.labelWidth;
            clazz = bbt.ToolBox.get('classOld', {displayAll: false/*labelWidth: 0, fieldLabel: '', emptyText: '请选择班级'*/});
            delete clazz.labelWidth;

            clazz.store.removeAll();

            winc = {
                title: '资产报修',
                modal: true,
                width: 400,
                closable: false,
                layout: 'fit',
                items: [{
                    xtype: 'form',
                    margin: 30,
                    border: false,
                    bodyCls: 'no-bg',
                    defaultType: 'combo',
                    layout: 'anchor',
                    defaults: {anchor: '100%', allowBlank: false},
                    items: [assetType, model, grade, clazz, /*{ TODO remote this comment on next dev iteration
                        xtype: 'panel',
                        layout: {type: 'hbox'},
                        bodyCls: 'no-bg',
                        border: false,
                        items: [{
                            xtype: 'component',
                            html: '所属位置:',
                            componentCls: 'no-bg',
                            width: 105
                        }, {
                            xtype: 'panel',
                            flex: 1,
                            border: false,
                            bodyCls: 'no-bg',
                            layout: {type:'vbox',align: 'stretch'},
                            items: [{
                                xtype: 'radiogroup',
                                layout: 'hbox',
                                border: false,
                                defaultType: 'radio',
                                items: [{
                                    boxLabel: '常规',
                                    inputValue: 'normal',
                                    name: 'class_type',
                                    checked: true
                                }, {
                                    boxLabel: '其它',
                                    name: 'class_type',
                                    inputValue: 'other',
                                    margin: '0 0 0 50'
                                }],
                                listeners: {
                                    change: function(me, v){
                                        var items = me.up('panel').items, ct = v.class_type;
                                        if(ct == 'normal') {
                                            items.get(1).show();
                                            items.get(2).hide();
                                        } else if(ct == 'other'){
                                            items.get(1).hide();
                                            items.get(2).show();
                                        }
                                    }
                                }
                            }, {
                                xtype: 'panel',
                                border: false,
                                layout: 'hbox',
                                defaults: {flex: 1},
                                items: [grade, clazz],
                                margin: '0 0 5 0'
                            }, {
                                xtype: 'textfield',
                                emptyText: '请输入位置信息',
                                hidden: true,
                                labelWidth: 0
                            }]
                        }]
                    }*/, {
                        xtype: 'textarea',
                        fieldLabel: '备注',
                        allowBlank: true,
                        name: 'remark'
                    }, {
                        xtype: 'hidden',
                        name: 'asset'
                    }]
                }],
                buttons: [{
                    text: '报修',
                    handler: function (){
                        var win = this.up('window'),
                            fm = win.down('form'), msg;
                        msg = checkForm(fm);
                        if(msg !== true) {
                            //Ext.Msg.alert('提示', msg);
                            return;
                        }
                        fm.getForm().submit({
                            url: '/asset/asset-repair/add/',
                            success: function(_fm, data){
                                gridTarget.store.reload();
                                win.destroy();
                            },
                            failure: function(_, a){
                                Ext.Msg.alert('提示', getErrorMsg(a.result));
                            }
                        });
                    }
                }, {
                    text: '关闭',
                    handler: function(b){b.up('window').destroy();}
                }],
                buttonAlign: 'right'
            };
            new Ext.window.Window(winc).show();
            gridTarget = this.up('grid');
        }
    },
    assetPos: {
        xtype: 'textfield',
        name: 'asset_pos',
        fieldLabel: '所属位置',
        labelWidth: 60,
        width: 160,
        qtip: '请输入资产所在的年级班级',
        listeners: {
            boxready: function(){
                Ext.create('Ext.tip.ToolTip', {
                    target: this.getInputId(),
                    html: this.qtip
                });
            }
        }
    },
    report_status: {
        xtype : 'combo',
        name : 'status',
        fieldLabel : '申报状态',
        editable: false,
        labelWidth : 60,
        width : 125,
        queryModel : 'local',
        value: '',
        store: [['', '所有'], ['已申报', '已申报'], ['未申报', '未申报']],
        queryMode: 'local'
    }
});
Ext.define("Ext.form.field.Tag",{extend:"Ext.form.field.ComboBox",requires:["Ext.selection.Model","Ext.data.Store"],xtype:"tagfield",multiSelect:true,forceSelection:true,createNewOnEnter:false,createNewOnBlur:false,encodeSubmitValue:false,triggerOnClick:true,stacked:false,pinList:true,filterPickList:false,selectOnFocus:true,grow:true,growMin:false,growMax:false,fieldSubTpl:['<div id="{cmpId}-listWrapper" class="'+Ext.baseCSSPrefix+'tagfield {fieldCls} {typeCls}">','<ul id="{cmpId}-itemList" class="'+Ext.baseCSSPrefix+'tagfield-list">','<li id="{cmpId}-inputElCt" class="'+Ext.baseCSSPrefix+'tagfield-input">','<div id="{cmpId}-emptyEl" class="{emptyCls}">{emptyText}</div>','<input id="{cmpId}-inputEl" type="{type}" ','<tpl if="name">name="{name}" </tpl>','<tpl if="value"> value="{[Ext.util.Format.htmlEncode(values.value)]}"</tpl>','<tpl if="size">size="{size}" </tpl>','<tpl if="tabIdx">tabIndex="{tabIdx}" </tpl>','<tpl if="disabled"> disabled="disabled"</tpl>','class="'+Ext.baseCSSPrefix+'tagfield-input-field {inputElCls}" autocomplete="off">',"</li>","</ul>","</div>",{disableFormats:true}],childEls:["listWrapper","itemList","inputEl","inputElCt","emptyEl"],emptyInputCls:Ext.baseCSSPrefix+"tagfield-emptyinput",initComponent:function(){var b=this,a=b.typeAhead;if(a&&!b.editable){Ext.Error.raise("If typeAhead is enabled the combo must be editable: true -- please change one of those settings.")}b.typeAhead=false;b.listConfig=Ext.apply({refreshSelmodelOnRefresh:false},b.listConfig);b.callParent();b.typeAhead=a;b.selectionModel=new Ext.selection.Model({store:b.valueStore,mode:"MULTI",lastFocused:null,onSelectChange:function(c,e,d,f){f()}});if(!Ext.isEmpty(b.delimiter)&&b.multiSelect){b.delimiterRegexp=new RegExp(String(b.delimiter).replace(/[$%()*+.?\[\\\]{|}]/g,"\\$&"))}},initEvents:function(){var a=this;a.callParent(arguments);if(!a.enableKeyEvents){a.mon(a.inputEl,"keydown",a.onKeyDown,a)}a.mon(a.inputEl,"paste",a.onPaste,a);a.mon(a.listWrapper,"click",a.onItemListClick,a);a.mon(a.selectionModel,{selectionchange:a.onSelectionChange,focuschange:a.onFocusChange,scope:a})},onBindStore:function(a){var b=this;if(a){b.valueStore=new Ext.data.Store({model:a.model});b.mon(b.valueStore,{datachanged:b.onValueStoreChange,remove:b.onValueStoreRemove,scope:b});if(b.selectionModel){b.selectionModel.bindStore(b.valueStore)}b.store.filters.add(b.selectedFilter=new Ext.util.Filter({filterFn:function(c){return !b.valueStore.data.contains(c)},disabled:!b.filterPickList}))}},onUnbindStore:function(a){var b=this,c=b.valueStore;if(c){b.mun(c,{datachanged:b.onValueStoreChange,remove:b.onValueStoreRemove,scope:b});c.destroy()}if(b.selectionModel){b.selectionModel.destroy()}b.store.filters.remove(b.selectedFilter);b.valueStore=b.selectionModel=null;b.callParent(arguments)},onValueStoreRemove:function(){if(this.filterPickList){this.store.filter()}},onValueStoreChange:function(){if(this.filterPickList){this.store.filter()}this.applyMultiselectItemMarkup()},onSelectionChange:function(a,b){this.applyMultiselectItemMarkup();this.fireEvent("valueselectionchange",this,b)},onFocusChange:function(a,c,b){this.fireEvent("valuefocuschange",this,c,b)},createPicker:function(){var b=this,a=b.callParent(arguments);b.mon(a,{beforerefresh:b.onBeforeListRefresh,scope:b});return a},onDestroy:function(){var a=this;Ext.destroyMembers(a,"valueStore","selectionModel");a.callParent(arguments)},getSubTplData:function(){var a=this,b=a.callParent(),c=a.emptyText&&b.value.length<1;b.value="";if(c){b.emptyText=a.emptyText;b.emptyCls=a.emptyCls;b.inputElCls=a.emptyInputCls}else{b.emptyText="";b.emptyCls=a.emptyInputCls;b.inputElCls=""}return b},afterRender:function(){var a=this;if(Ext.supports.Placeholder&&a.inputEl&&a.emptyText){delete a.inputEl.dom.placeholder}a.bodyEl.applyStyles("vertical-align:top");if(a.grow){if(Ext.isNumber(a.growMin)&&(a.growMin>0)){a.listWrapper.applyStyles("min-height:"+a.growMin+"px")}if(Ext.isNumber(a.growMax)&&(a.growMax>0)){a.listWrapper.applyStyles("max-height:"+a.growMax+"px")}}if(a.stacked===true){a.itemList.addCls(Ext.baseCSSPrefix+"tagfield-stacked")}if(!a.multiSelect){a.itemList.addCls(Ext.baseCSSPrefix+"tagfield-singleselect")}a.applyMultiselectItemMarkup();a.callParent(arguments)},findRecord:function(d,c){var b=this.store,a;if(!b){return false}a=b.queryBy(function(e){return e.isEqual(e.get(d),c)});return(a.getCount()>0)?a.first():false},onLoad:function(){var b=this,a=b.valueField,c=b.valueStore,d=false;if(c){if(!Ext.isEmpty(b.value)&&(c.getCount()==0)){b.setValue(b.value,false,true)}c.suspendEvents();c.each(function(g){var f=b.findRecord(a,g.get(a)),e=f?c.indexOf(g):-1;if(e>=0){c.removeAt(e);c.insert(e,f);d=true}});c.resumeEvents();if(d){c.fireEvent("datachanged",c)}}b.callParent(arguments)},isFilteredRecord:function(a){var f=this,b=f.store,d=f.valueField,e,c=false;e=b.findExact(d,a.get(d));c=((e===-1)&&(!b.snapshot||(f.findRecord(d,a.get(d))!==false)));c=c||(!c&&(e===-1)&&(f.forceSelection!==true)&&(f.valueStore.findExact(d,a.get(d))>=0));return c},doRawQuery:function(){var a=this,b=a.inputEl.dom.value;if(a.multiSelect){b=b.split(a.delimiter).pop()}a.doQuery(b,false,true)},onBeforeListRefresh:function(){this.ignoreSelection++},onListRefresh:function(){this.callParent(arguments);if(this.ignoreSelection>0){--this.ignoreSelection}},onListSelectionChange:function(c,f){var b=this,d=b.valueStore,e=[],a;if((b.ignoreSelection<=0)&&b.isExpanded){d.each(function(g){if(Ext.Array.contains(f,g)||b.isFilteredRecord(g)){e.push(g)}});e=Ext.Array.merge(e,f);a=Ext.Array.intersect(e,d.getRange()).length;if((a!=e.length)||(a!=b.valueStore.getCount())){b.setValue(e,false);if(!b.multiSelect||!b.pinList){Ext.defer(b.collapse,1,b)}if(d.getCount()>0){b.fireEvent("select",b,d.getRange())}}if(!b.pinList){b.inputEl.dom.value=""}if(!Ext.supports.TouchEvents){b.inputEl.focus();if(b.selectOnFocus){b.inputEl.dom.select()}}}},syncSelection:function(){var f=this,d=f.picker,c=f.valueField,a,e,b;if(d){a=d.store;e=[];if(f.valueStore){f.valueStore.each(function(h){var g=a.findExact(c,h.get(c));if(g>=0){e.push(a.getAt(g))}})}f.ignoreSelection++;b=d.getSelectionModel();b.deselectAll();if(e.length>0){b.select(e)}if(f.ignoreSelection>0){--f.ignoreSelection}}},getCursorPosition:function(){var a;if(Ext.isIE){a=document.selection.createRange();a.collapse(true);a.moveStart("character",-this.inputEl.dom.value.length);a=a.text.length}else{a=this.inputEl.dom.selectionStart}return a},hasSelectedText:function(){var b,a;if(Ext.isIE){b=document.selection;a=b.createRange();return(a.parentElement()==this.inputEl.dom)}else{return this.inputEl.dom.selectionStart!=this.inputEl.dom.selectionEnd}},onKeyDown:function(d,i){var f=this,h=d.getKey(),b=f.inputEl.dom.value,j=f.valueStore,c=f.selectionModel,a=false;if(f.readOnly||f.disabled||!f.editable){return}if(f.isExpanded&&(h==d.A&&d.ctrlKey)){f.select(f.getStore().getRange());c.setLastFocused(null);c.deselectAll();f.collapse();f.inputEl.focus();a=true}else{if((j.getCount()>0)&&((b=="")||((f.getCursorPosition()===0)&&!f.hasSelectedText()))){var g=(c.getCount()>0)?j.indexOf(c.getLastSelected()||c.getLastFocused()):-1;if((h==d.BACKSPACE)||(h==d.DELETE)){if(g>-1){if(c.getCount()>1){g=-1}f.valueStore.remove(c.getSelection())}else{f.valueStore.remove(f.valueStore.last())}c.clearSelections();f.setValue(f.valueStore.getRange());if(g>0){c.select(g-1)}a=true}else{if((h==d.RIGHT)||(h==d.LEFT)){if((g==-1)&&(h==d.LEFT)){c.select(j.last());a=true}else{if(g>-1){if(h==d.RIGHT){if(g<(j.getCount()-1)){c.select(g+1,d.shiftKey);a=true}else{if(!d.shiftKey){c.setLastFocused(null);c.deselectAll();a=true}}}else{if((h==d.LEFT)&&(g>0)){c.select(g-1,d.shiftKey);a=true}}}}}else{if(h==d.A&&d.ctrlKey){c.selectAll();a=d.A}}}f.inputEl.focus()}}if(a){f.preventKeyUpEvent=a;d.stopEvent();return}if(f.isExpanded&&(h==d.ENTER)&&f.picker.highlightedItem){f.preventKeyUpEvent=true}if(f.enableKeyEvents){f.callParent(arguments)}if(!d.isSpecialKey()&&!d.hasModifier()){f.selectionModel.setLastFocused(null);f.selectionModel.deselectAll();f.inputEl.focus()}},onKeyUp:function(d,a){var b=this,c=b.inputEl.dom.value;if(b.preventKeyUpEvent){d.stopEvent();if((b.preventKeyUpEvent===true)||(d.getKey()===b.preventKeyUpEvent)){delete b.preventKeyUpEvent}return}if(b.multiSelect&&(b.delimiterRegexp&&b.delimiterRegexp.test(c))||((b.createNewOnEnter===true)&&d.getKey()==d.ENTER)){c=Ext.Array.clean(c.split(b.delimiterRegexp));b.inputEl.dom.value="";b.setValue(b.valueStore.getRange().concat(c));b.inputEl.focus()}b.callParent([d,a])},onPaste:function(d){var a=this,c=a.inputEl.dom.value,b=(d&&d.browserEvent&&d.browserEvent.clipboardData)?d.browserEvent.clipboardData:false;if(a.multiSelect&&(a.delimiterRegexp&&a.delimiterRegexp.test(c))){if(b&&b.getData){if(/text\/plain/.test(b.types)){c=b.getData("text/plain")}else{if(/text\/html/.test(b.types)){c=b.getData("text/html")}}}c=Ext.Array.clean(c.split(a.delimiterRegexp));a.inputEl.dom.value="";a.setValue(a.valueStore.getRange().concat(c));a.inputEl.focus()}},onTypeAhead:function(){var f=this,e=f.displayField,d=f.inputEl.dom,c=f.getPicker(),b=f.store.findRecord(e,d.value),g,a,h;if(b){g=b.get(e);a=g.length;h=d.value.length;c.highlightItem(c.getNode(b));if(h!==0&&h!==a){d.value=g;f.selectText(h,g.length)}}},onItemListClick:function(a){var c=this,b=a.getTarget("."+Ext.baseCSSPrefix+"tagfield-item"),d=b?a.getTarget("."+Ext.baseCSSPrefix+"tagfield-item-close"):false;if(c.readOnly||c.disabled){return}a.stopPropagation();if(b){if(d){c.removeByListItemNode(b);if(c.valueStore.getCount()>0){c.fireEvent("select",c,c.valueStore.getRange())}}else{c.toggleSelectionByListItemNode(b,a.shiftKey)}if(!Ext.supports.TouchEvents){c.inputEl.focus()}}else{if(c.selectionModel.getCount()>0){c.selectionModel.setLastFocused(null);c.selectionModel.deselectAll()}if(c.triggerOnClick){c.onTriggerClick()}}},getMultiSelectItemMarkup:function(){var a=this;if(!a.multiSelectItemTpl){if(!a.labelTpl){a.labelTpl="{"+a.displayField+"}"}a.labelTpl=a.getTpl("labelTpl");a.multiSelectItemTpl=new Ext.XTemplate(['<tpl for=".">','<li class="    '+Ext.baseCSSPrefix+"tagfield-item ",'<tpl if="this.isSelected(values)">'," selected","</tpl>","{%","values = values.data;","%}",'" qtip="{'+a.displayField+'}">','<div class="'+Ext.baseCSSPrefix+'tagfield-item-text">{[this.getItemLabel(values)]}</div>','<div class="'+Ext.baseCSSPrefix+'tagfield-item-close"></div>',"</li>","</tpl>",{isSelected:function(b){return a.selectionModel.isSelected(b)},getItemLabel:function(b){return a.labelTpl.apply(b)}}])}if(!a.multiSelectItemTpl.isTemplate){a.multiSelectItemTpl=this.getTpl("multiSelectItemTpl")}return a.multiSelectItemTpl.apply(this.valueStore.getRange())},applyMultiselectItemMarkup:function(){var c=this,a=c.itemList,b;if(a){while((b=c.inputElCt.prev())!=null){b.destroy()}c.inputElCt.insertHtml("beforeBegin",c.getMultiSelectItemMarkup())}setTimeout(function(){if(c.picker&&c.isExpanded){c.alignPicker()}if(c.hasFocus&&c.inputElCt&&c.listWrapper){c.inputElCt.scrollIntoView(c.listWrapper)}},30)},getRecordByListItemNode:function(b){var d=this,c=0,a=d.itemList.dom.firstChild;while(a&&a.nextSibling){if(a==b){break}c++;a=a.nextSibling}c=(a==b)?c:false;if(c===false){return false}return d.valueStore.getAt(c)},toggleSelectionByListItemNode:function(b,d){var c=this,e=c.getRecordByListItemNode(b),a=c.selectionModel;if(e){if(a.isSelected(e)){if(a.isFocused(e)){a.setLastFocused(null)}a.deselect(e)}else{a.select(e,d)}}},removeByListItemNode:function(a){var b=this,c=b.getRecordByListItemNode(a);if(c){b.valueStore.remove(c);b.setValue(b.valueStore.getRange())}},getRawValue:function(){var b=this,c=b.inputEl,a;b.inputEl=false;a=b.callParent(arguments);b.inputEl=c;return a},setRawValue:function(c){var b=this,d=b.inputEl,a;b.inputEl=false;a=b.callParent([c]);b.inputEl=d;return a},addValue:function(b){var a=this;if(b){a.setValue(Ext.Array.merge(a.value,Ext.Array.from(b)))}},removeValue:function(b){var a=this;if(b){a.setValue(Ext.Array.difference(a.value,Ext.Array.from(b)))}},setValue:function(j,b,l){var h=this,n=h.valueStore,m=h.valueField,g=[],e,f,d,a,k;if(Ext.isEmpty(j)){j=null}if(Ext.isString(j)&&h.multiSelect){j=j.split(h.delimiter)}j=Ext.Array.from(j,true);for(d=0,f=j.length;d<f;d++){e=j[d];if(!e||!e.isModel){a=n.findExact(m,e);if(a>=0){j[d]=n.getAt(a)}else{a=h.findRecord(m,e);if(!a){if(h.forceSelection){g.push(e)}else{a={};a[h.valueField]=e;a[h.displayField]=e;k=h.valueStore.getModel();a=new k(a)}}if(a){j[d]=a}}}}if((l!==true)&&(g.length>0)&&(h.queryMode==="remote")){var c={};c[h.valueParam||h.valueField]=g.join(h.delimiter);h.store.load({params:c,callback:function(){if(h.itemList){h.itemList.unmask()}h.setValue(j,b,true);h.autoSize();h.lastQuery=false}});return false}if(!h.multiSelect&&(j.length>0)){for(d=j.length-1;d>=0;d--){if(j[d].isModel){j=j[d];break}}if(Ext.isArray(j)){j=j[j.length-1]}}return h.callParent([j,b])},getValueRecords:function(){return this.valueStore.getRange()},getSubmitData:function(){var a=this,b=a.callParent(arguments);if(a.multiSelect&&a.encodeSubmitValue&&b&&b[a.name]){b[a.name]=Ext.encode(b[a.name])}return b},mimicBlur:function(){var a=this;if(a.selectOnTab&&a.picker&&a.picker.highlightedItem){a.inputEl.dom.value=""}a.callParent(arguments)},assertValue:function(){var a=this,c=a.inputEl.dom.value,d=!Ext.isEmpty(c)?a.findRecordByDisplay(c):false,b=false;if(!d&&!a.forceSelection&&a.createNewOnBlur&&!Ext.isEmpty(c)){b=c}else{if(d){b=d}}if(b){a.addValue(b)}a.inputEl.dom.value="";a.collapse()},checkChange:function(){if(!this.suspendCheckChange&&!this.isDestroyed){var c=this,f=c.valueStore,b=c.lastValue||"",a=c.valueField,e=Ext.Array.map(Ext.Array.from(c.value),function(g){if(g.isModel){return g.get(a)}return g},this).join(this.delimiter),d=c.isEqual(e,b);if(!d||((e.length>0&&f.getCount()<c.value.length))){f.suspendEvents();f.removeAll();if(Ext.isArray(c.valueModels)){f.add(c.valueModels)}f.resumeEvents();f.fireEvent("datachanged",f);if(!d){c.lastValue=e;c.fireEvent("change",c,e,b);c.onChange(e,b)}}}},isEqual:function(h,g){var b=Ext.Array.from,c=this.valueField,d,a,f,e;h=b(h);g=b(g);a=h.length;if(a!==g.length){return false}for(d=0;d<a;d++){f=h[d].isModel?h[d].get(c):h[d];e=g[d].isModel?g[d].get(c):g[d];if(f!==e){return false}}return true},applyEmptyText:function(){var b=this,a=b.emptyText,c,d;if(b.rendered&&a){d=Ext.isEmpty(b.value)&&!b.hasFocus;c=b.inputEl;if(d){c.dom.value="";b.emptyEl.setHtml(a);b.emptyEl.addCls(b.emptyCls);b.emptyEl.removeCls(b.emptyInputCls);b.listWrapper.addCls(b.emptyCls);b.inputEl.addCls(b.emptyInputCls)}else{b.emptyEl.addCls(b.emptyInputCls);b.emptyEl.removeCls(b.emptyCls);b.listWrapper.removeCls(b.emptyCls);b.inputEl.removeCls(b.emptyInputCls)}b.autoSize()}},preFocus:function(){var a=this,b=a.inputEl,c=(b.dom.value=="");a.emptyEl.addCls(a.emptyInputCls);a.emptyEl.removeCls(a.emptyCls);a.listWrapper.removeCls(a.emptyCls);a.inputEl.removeCls(a.emptyInputCls);if(a.selectOnFocus||c){b.dom.select()}},onFocus:function(){var c=this,b=c.focusCls,a=c.itemList;if(b&&a){a.addCls(b)}c.callParent(arguments)},onBlur:function(){var c=this,b=c.focusCls,a=c.itemList;if(b&&a){a.removeCls(b)}c.callParent(arguments)},renderActiveError:function(){var d=this,c=d.invalidCls,b=d.itemList,a=d.hasActiveError();if(c&&b){b[a?"addCls":"removeCls"](d.invalidCls+"-field")}d.callParent(arguments)},autoSize:function(){var a=this;if(a.grow&&a.rendered){a.autoSizing=true;a.updateLayout()}return a},afterComponentLayout:function(){var b=this,a;if(b.autoSizing){a=b.getHeight();if(a!==b.lastInputHeight){if(b.isExpanded){b.alignPicker()}b.fireEvent("autosize",b,a);b.lastInputHeight=a;b.autoSizing=false}}}});
/* grid base */
Ext.define('bbt.ManageGrid', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.mgrgridbase',
    initComponent: function(){
        var columnDefaults = {sortable: false, menuDisabled: true, draggable: false};
        Ext.each(this.columns, function(c){ Ext.applyIf(c, columnDefaults); });
        if(this.showOperateColumn) {
            if(this.columns[this.columns.length-1].text != '操作')
            this.columns.push({
                text: '操作',
                sortable: false,
                menuDisabled: true,
                draggable: false,
                dataIndex: '_',
                flex: 1,
                editRenderer: function(){ return ''; },
                renderer: this.operateRenderer ? this.operateRenderer() : this.getOperateFn()
            });
        }

        this.store = new Ext.data.Store({
            fields: this.fields,
            proxy: this.proxy||{
                type: 'ajax',
                url: this.listUrl,
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                },
                startParam: undefined,
                sortParam: 'order_field',
                directionParam: 'order_direction',
                simpleSortMode: true
            },
            pageSize: this.pageSize,
            sorters: this.sorters
        });
        if(typeof this.tbar != "undefined") {
            this.tbar = bbt.ToolBox.convert(this.tbar);
        }
        if(this.pagination) {
            this.bbar = {xtype: 'pagingtoolbar', displayInfo: true, store: this.store};
        }
        //this.addEvents(Ext.Array.map(Ext.Object.getKeys(this.actionMap), function(v){return 'beforeaction'+v;}));
        this.callParent();
        this.on('afterrender', function(){
            var me = this, tb;
            if(this.actionMap) {
                tb = this.down('toolbar[dock=top]');
                tb && Ext.Object.each(this.actionMap, function(k, v){
                    btn = tb.down('[action=' + k + ']');
                    if(btn) {
                        btn.setHandler(me[v], me);
                    }
                });
            }
        });
        this.on('itemclick', function(v, rc, ele, i, e){
            var t = Ext.get(e.target), action;
            if(t.is('[action]')) {
                action = t.getAttribute('action') || t.dom.getAttribute('action');
                this[this.actionMap[action]](v, rc, ele, i, e);
            }
        });
        this.fireEvent('show', this);
    },
    listUrl: null,
    addUrl: null,
    removeUrl: null,
    updateUrl: null,
    operates: null,
    actionMap: null,
    showOperateColumn: true,
    checkPrivilegeOnAction: false,
    alertOnFailure: true,
    pagination: false,
    request: function(url, params, options){
        var me = this, form, config, loadMask;
        options = options || {};
        options.method = options.method || 'POST';
        if(typeof params == "function") {
            options.success = params;
            params = {};
        }
        if(params.form) { form = params.form; delete params.form; }

        config = {
            url: url,
            params: params
        };
        if(form) {
            form = form.getForm();
            config.success = function(_form, action){
                options.maskId && me.destroyMask(options.maskId);
                options.success && options.success(action.result);
            };
            config.failure = function(_form, action){
                options.maskId && me.destroyMask(options.maskId);
                if(options.alertOnFailure !== false) {
                    Ext.Msg.alert('提示', getErrorMsg(action.result));
                } else {
                    options.failure && options.failure(action.result);
                }
            };
            form.submit(config);
        } else {
            config.method = options.method;
            config.callback = function(_options, _success, resp){
                var data;
                try {
                    data = Ext.decode(resp.responseText);
                    if(data.status == "success") {
                        options.success && options.success(data.data, data);
                    } else {
                        if(options.alertOnFailure !== false) {
                            Ext.Msg.alert('提示', data.msg);
                        } else {
                            options.failure && options.failure(data);
                        }
                    }
                } catch(e){
                    if(typeof data == "undefined") {
                        Ext.Msg.alert('提示', '失败！');
                    }
                } finally {
                    options.maskId && me.destroyMask(options.maskId);
                    options.callback && options.callback(data);
                }
            };
            Ext.Ajax.request(config);
        }
    },
    load: function(){
        this.store.load();
    },
    createMask: function(component, msg){
        var mask = new Ext.LoadMask(component||this, {msg:msg}),
            maskId = new Date().getTime() + '' + Math.random();
        if(!this._loadmask) {
            this._loadmask = {};
        }
        this._loadmask[maskId] = mask;
        mask.show();
        return maskId;
    },
    destroyMask: function(maskId){
        var mask;
        if(typeof maskId == "string") {
            mask = this._loadmask[maskId];
        }
        mask && mask.hide();
        mask.destroy && mask.destroy();
        delete this._loadmask[maskId];
    },
    getOperateFn: function(){
        var r = [];
        Ext.Object.each(this.operates, function(k, v){
            r.push('<a href="javascript:void(0);" action="' + k + '">' + v + '</a>');
        });
        r = r.join(' ');
        return function(){ return r; };
    },
    checkForm: function(form) {
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
});
//定义校级的系统设置项
if(bbt.UserInfo.isSchool()) {


/* 班班通教室: 年级班级管理 */
Ext.define('bbt.GradeClass', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.gc',
    fields: ['grade__name', 'name', 'classmacv2__mac', 'uuid', 'grade__term__school_year', 'grade__term__term_type', 'teacher', 'teacher__name', 'teacher__birthday'],
    importUrl: '/system/class/import/',
    addUrl: '/system/class/add/',
    updateUrl: '/system/class/edit/',
    removeUrl: '/system/class/delete/',
    listUrl: '/system/class/list/',
    bingMacUrl: '/system/class/clear_mac/',
    tbar: [{
        text: '批量添加班级',
        action: 'batchAdd',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '添加班级',
        action: 'add',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '编辑班级',
        action: 'edit',
        iconCls: 'tool-icon icon-edit'
    }, {
        text: '清除绑定',
        action: 'clear_mac',
        iconCls: 'tool-icon icon-clear'
    }, {
        text: '删除班级',
        action: 'remove',
        iconCls: 'tool-icon icon-delete'
    }/*, {
        xtype: 'form',
        bodyCls: 'no-bg',
        border: false,
        items: [{
            xtype : 'fileuploadfield',
            name : 'excel',
            buttonOnly : true,
            margin : 0,
            padding : 0,
            buttonConfig : {text : '导入', iconCls: 'icon-import'},
            listeners: {
                change: function(f, path){
                    var grid = f.up('gc');
                    if(!/\.xlsx?$/.test(path)) {
                        //Ext.Msg.alert('提示', '请选择 excel 文件！');
                        f.reset();
                        return;
                    }
                    f.up('form').submit({
                        url: grid.importUrl,
                        success: function(form, a){ f.reset(); grid.store.load(); },
                        failure: function(){ f.reset(); }
                    });
                }
            }
        }]
    }*/],
    columns: [{
        text: '学年',
        dataIndex: 'grade__term__school_year'
    }, {
        text: '学期类型',
        dataIndex: 'grade__term__term_type'
    }, {
        text: '年级',
        dataIndex: 'grade__name',
        width: 120,
        regex: /^[1-9]\d+$/,
        regexText: '无效的数字',
        renderer: function(v) {
            return v ? v + '年级' : '';
        }
    }, {
        text: '班级',
        dataIndex: 'name',
        width: 120,
        renderer: function(v) {
            return v ? v + '班' : '';
        },
        regex: /^[1-9]\d+$/,
        regexText: '无效的数字'
    }, {
        text: '本学期班主任',
        dataIndex: 'teacher__name'
    }, {
        text: '出生年月',
        dataIndex: 'teacher__birthday'
    }, {
        text: 'MAC地址绑定',
        width: 240,
        dataIndex: 'classmacv2__mac'
    }],
    pagination: true,
    showOperateColumn: false,
    operates: {remove: '删除'},
    actionMap: {add: 'addGradeClass', batchAdd: 'batchAddGradeClass', edit: 'editGradeClass', remove: 'removeGradeClass', clear_mac: 'onClearMac'},
    listeners: {
        edit: function(_, e){
            if(this.myAfterEdit) {
                this.myAfterEdit();
                delete this.myAfterEdit;
            } else {
                e.record.commit();
            }
        },
        show: function(){
            this.store.load();
        }
    },
    onClearMac: function(v, rc){
        var me = this, select, gc, cb;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            gc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        cb = function(){
            me.request('/system/class/clear_mac/', {uuid: gc.get('uuid')}, {
                maskId: me.createMask(me, '正在清除 MAC 地址绑定！'),
                success: function(){
                    gc.store.reload();
                }
            });
        };
        if(!gc.get('classmacv2__mac')) { return; }
        Ext.Msg.confirm('提示', '是否确认清除绑定信息？', function(b){
            if(b == "yes") { cb(); }
        });
    },
    batchAddGradeClass: function(){
        var winc, win;
        winc = {
            xtype: 'window',
            owner: this,
            title: '批量添加班级',
            width: 450,
            closable: false,
            resizable: false,
            modal: true,
            constraint: true,
            layout: 'fit',
            items: [{
                xtype: 'form',
                margin: 20,
                bodyCls: 'no-bg',
                border: false,
                layout: 'column',
                defaultType: 'numberfield',
                defaults: {
                    columnWidth: 0.5,
                    margin: 5,
                    value: 0,
                    minValue: 0,
                    maxValue: 100,
                    labelWidth: 80
                },
                items: [{
                    xtype: 'displayfield',
                    columnWidth: 1,
                    labelWidth: 0,
                    labelSeparator: '',
                    value: '',
                    fieldStyle: {textAlign: 'center'}
                }, {
                    fieldLabel: '一年级',
                    name: 'grade_1'
                }, {
                    fieldLabel: '七年级',
                    name: 'grade_7'
                }, {
                    fieldLabel: '二年级',
                    name: 'grade_2'
                }, {
                    fieldLabel: '八年级',
                    name: 'grade_8'
                }, {
                    fieldLabel: '三年级',
                    name: 'grade_3'
                }, {
                    fieldLabel: '九年级',
                    name: 'grade_9'
                }, {
                    fieldLabel: '四年级',
                    name: 'grade_4'
                }, {
                    fieldLabel: '十年级',
                    name: 'grade_10'
                }, {
                    fieldLabel: '五年级',
                    name: 'grade_5'
                }, {
                    fieldLabel: '十一年级',
                    name: 'grade_11'
                }, {
                    fieldLabel: '六年级',
                    name: 'grade_6'
                }, {
                    fieldLabel: '十二年级',
                    name: 'grade_12'
                }]
            }],
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'), fm = win.down('form'), msg;
                    msg = win.owner.checkForm(fm);
                    if(msg !== true) { return }
                    win.owner.request('/system/class/batch_add/', {form: fm}, {
                        maskId: win.owner.createMask(win, '正在添加年级和班级……'),
                        success: function(){
                            win.owner.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '取消',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        };
        win = Ext.widget(winc);
        win.show();
        this.hasSchoolYear(win);
    },
    addGradeClass: function(){
        var win = Ext.create('Ext.window.Window', this.getGradeClassWindowConfig());
        win.down('[action=submit]').setHandler(function(b){
            var me = this, fm = win.down('form'), msg, maskId, cb;
            msg = me.checkForm(fm);
            if(msg !== true) {
                //Ext.Msg.alert('提示', msg);
                return;
            }
            me.request(me.addUrl, {form: fm}, {
                maskId: me.createMask(win, '正在添加年级和班级……'),
                success: function(){
                    me.store.reload();
                    win.destroy();
                }
            });
        }, this);
        win.show();
        this.hasSchoolYear(win);
    },
    editGradeClass: function(){
        var me = this, win, fm, select, gc, d, times;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            gc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        win = Ext.create('Ext.window.Window', this.getGradeClassWindowConfig('编辑班级'));
        win.down('[action=submit]').setHandler(function(b){
            var me = this, fm = win.down('form'), msg, maskId, cb;
            msg = me.checkForm(fm);
            if(msg !== true) {
                //Ext.Msg.alert('提示', msg);
                return;
            }
            me.request(me.updateUrl, {form: fm, uuid: gc.get('uuid')}, {
                maskId: me.createMask(win, '正在编辑年级和班级……'),
                success: function(){
                    me.store.reload();
                    win.destroy();
                }
            });
        }, this);
        win.show();
        win.down('[name=school_year]').setValue(gc.get('grade__term__school_year') + ' （' + gc.get('grade__term__term_type') + '）');
        win.down('[name=grade_name]').setValue(gc.get('grade__name')).setReadOnly(true);
        win.down('[name=teacher_uuid]')._value = gc.get('teacher');
        win.down('[name=name]').setValue(gc.get('name')).setReadOnly(true);
    },
    removeGradeClass: function(){
        var me = this, gc, select, maskId, msg;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择年级和班级！');
            return;
        }
        gc = select[0];
        passCB = function(){
            me.request(me.removeUrl, {uuid:gc.get('uuid')}, {
                success: function(){
                    me.store.reload();
                },
                maskId: me.createMask(me, '正在删除班级')
            });
        };

        msg = Ext.Msg.show({
            title: '提示',
            buttons: Ext.MessageBox.YESNO,
            icon: Ext.MessageBox.ERROR,
            msg: '<p style="color:red;font-size:14px;">删除该班级，将同步删除该班级课程表和班级所关联的授课老师信息，是否执行？</p>',
            fn: function(b){
                b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
            }
        });
        msg.defaultFocus = msg.queryById('no');
        msg.defaultFocus.focus(false, 50);
    },
    hasSchoolYear: function(win){
        bbt.loadCurrentSchoolYear(function(opts, _, resp){
            var data = Ext.decode(resp.responseText);
            if(data.status == "success") {
                win.down('displayfield').setValue(data.data.school_year+' （'+data.data.term_type+'）');
            } else {
                Ext.Msg.alert('提示', '当前没有学年学期!', function(){
                    win.destroy();
                });
            }
        });
    },
    askNext: function(msg, yescb, nocb){
        Ext.widget('window', {
            title: '提示',
            width: 250,
            modal: true,
            height: 140,
            closable: false,
            items: [{
                bodyCls: 'no-bg',
                html: msg + '\n要继续添加吗？',
                border: false,
                margin: 30
            }],
            buttons: [{
                text: '继续添加 >>',
                handler: function(){
                    yescb && yescb();
                    this.up('window').destroy();
                }
            }, {
                text: '不了，谢谢',
                handler: function(){
                    nocb && nocb();
                    this.up('window').destroy();
                }
            }],
            buttonAlign: 'center'
        }).show();
    },
    getGradeClassWindowConfig: function(title){
        var classes, winc;
        winc = {
            xtype: 'window',
            modal: true,
            title: title||'添加班级',
            width: 350,
            //height: 200,
            closable: false,
            items: [{
                xtype: 'form',
                margin: 20,
                bodyCls: 'no-bg',
                border: false,
                layout: 'anchor',
                defaults: {anchor: '100%', allowBlank: false, margin: '15 0 0 0'},
                items: [{
                    xtype: 'displayfield',
                    name: 'school_year',
                    value: '',
                    fieldLabel: '学年学期'
                }, {
                    xtype: 'combo',
                    name: 'grade_name',
                    fieldLabel: '年级',
                    editable: false,
                    store: Ext.Array.map(['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'], function(v){ return [v, bbt.fullgrade(v)]; }),
                    listeners: {
                        change: function(me, v){
                            var cls = me.ownerCt.down('[name=name]');
                            cls.store.proxy.extraParams.grade_name = v;
                            cls.needReload = true;
                            cls.setValue('');
                        }
                    }
                }, {
                    xtype: 'combo',
                    margin: '15 0 20 0',
                    name: 'name',
                    displayField: 'text',
                    valueField: 'text',
                    fieldLabel: '班级',
                    editable: false,
                    queryMode: 'local',
                    needReload: true,
                    store: new Ext.data.Store({
                        fields: ['text'],
                        proxy: {
                            type: 'ajax',
                            url: '/classes/available-choices/',
                            reader: {
                                type: 'json',
                                root: 'data'
                            }
                        },
                        listeners: {
                            load: function(){
                                this.owner.expand();
                            }
                        }
                    }),
                    listeners: {
                        afterrender: function(){
                            this.store.owner = this;
                        },
                        expand: function(){
                            if(this.needReload) {
                                this.store.load();
                                delete this.needReload;
                            }
                        }
                    }
                }, bbt.ToolBox.get('teacherName', {
                    fieldLabel: '班主任',
                    labelWidth: 100,
                    allowBlank: true,
                    name: 'teacher_uuid',
                    valueField: 'uuid',
                    //editable: false,
                    hideTrigger: false,
                    validator: undefined,
                    editable: false,
                    listeners: {
                        afterrender: function(){
                            this.store.on('load', function(s){
                                var rc = s.getAt(0);
                                if(rc.data.value === "") { s.remove(rc); }
                                this._value && this.setValue(this._value);
                            }, this);
                            this.store.fireEvent('load', this.store);
                        },
                        change: function(me, v){
                            var birth = me.ownerCt.down('[name=birthday]'),
                                rc = me.findRecordByValue(v);
                            if(birth && rc) {
                                birth.setValue(rc.get('birthday'));
                            }
                        },
                        blur: function(){
                            var v = this.getValue(), rc;
                            //if user select a teacher
                            if(this.findRecordByValue(v)) {
                                return;
                            }
                            //test for user input name
                            rc = this.findRecordByDisplay(v);
                            if(!rc) {
                                this.setValue('');
                            } else {
                                this.setValue(rc.get(this.valueField));
                            }
                        }
                    }
                }), {
                    xtype: 'displayfield',
                    name: 'birthday',
                    fieldLabel: '出生年月',
                    labelWidth: 100
                }]
            }],
            buttons: [{
                text: '确定',
                action: 'submit'
            }, {
                text: '关闭',
                handler: function(){ this.up('window').destroy(); }
            }],
            buttonAlign: 'right'
        };
        return winc;
    }
});
/* 电脑教室: 年级班级管理 */
Ext.define('bbt.ComputerGradeClass', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.computerclass',
    fields: ['school_year', 'term_type', 'number', 'mac', 'name', 'uuid', 'computerclass_uuid', 'client_number', 'lesson_range', 'grade_name'],
    tbar: [{
        text: '添加教室',
        action: 'add',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '编辑教室',
        action: 'edit',
        iconCls: 'tool-icon icon-edit'
    }, {
        text: '清除绑定',
        action: 'clear_mac',
        iconCls: 'tool-icon icon-clear'
    }, {
        text: '删除教室',
        action: 'remove',
        iconCls: 'tool-icon icon-delete'
    }, {
        text: '查看课表',
        action: 'viewtable',
        iconCls: 'tool-icon icon-view'
    }],
    columns: [{
        text: '学年',
        dataIndex: 'school_year'
    }, {
        text: '学期类型',
        dataIndex: 'term_type'
    }, {
        text: '教室名称',
        dataIndex: 'name'
    }, {
        text: '室号',
        dataIndex: 'number'
    }, {
        text: '学生机数量',
        dataIndex: 'client_number'
    }, {
        text: '授课课程范围',
        flex: 1,
        dataIndex: 'lesson_range',
        renderer: function(v){
            try {
                return v.map(function(item){return item[1]}).join('，');
            } catch(e) {
                return '';
            }
        }
    }, {
        text: 'MAC地址绑定',
        dataIndex: 'mac',
        width: 200
    }],
    listeners: {
        /*deselect: function(){
            var rc = arguments[1],
                btn = this.down('toolbar[dock=top]').down('[action=clear_mac]');
            btn.setDisabled(true);
        },
        select: function(){
            var rc = arguments[1],
                btn = this.down('toolbar[dock=top]').down('[action=clear_mac]');
            btn.setDisabled(!rc.get('mac'));
        },*/
        show: function(){
            this.store.load();
        }
    },
    importUrl: '/system/computer-class/import/',
    addUrl: '/system/computer-class/add/',
    updateUrl: '/system/computer-class/edit/',
    removeUrl: '/system/computer-class/delete/',
    listUrl: '/system/computer-class/all/',
    bindMacUrl: '/system/computer-class/clear_mac/',
    viewUrl: '/system/computer-class/curriculum/',
    pagination: true,
    showOperateColumn: false,
    actionMap: {add: 'addGradeClass', edit: 'editGradeClass', remove: 'removeGradeClass', clear_mac: 'onClearMac', viewtable: 'viewCourseTable'},
    onClearMac: function(){
        var me = this, select, gc, cb = function(){
            me.request(me.bindMacUrl, {uuid: gc.get('uuid')}, {
                maskId: me.createMask(me, '正在清除 MAC 地址绑定！'),
                success: function(){
                    gc.store.reload();
                }
            });
        };
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            gc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        if(!gc.get('mac')) { return; }
        Ext.Msg.confirm('提示', '是否确认清除绑定信息？', function(b){
            if(b == "yes") { cb(); }
        });
    },
    addGradeClass: function(){
        var win = Ext.create('Ext.window.Window', this.getGradeClassWindowConfig());
        win.down('[action=submit]').setHandler(function(b){
            var me = this, fm = win.down('form'), msg, maskId, cb;
            msg = me.checkForm(fm);
            if(msg !== true) {
                //Ext.Msg.alert('提示', msg);
                return;
            }
            me.request(me.addUrl, {form: fm}, {
                maskId: me.createMask(win, '正在添加电脑教室'),
                success: function(){
                    me.store.reload();
                    win.destroy();
                }
            });
        }, this);
        win.show();
        this.hasSchoolYear(win);
    },
    editGradeClass: function(){
        var me = this, win, fm, select, gc, d, times, range;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            gc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        win = Ext.create('Ext.window.Window', this.getGradeClassWindowConfig('编辑电脑教室', 'edit'));
        win.down('[action=submit]').setHandler(function(b){
            var me = this, fm = win.down('form'), msg, maskId, cb;
            msg = me.checkForm(fm);
            if(msg !== true) {
                //Ext.Msg.alert('提示', msg);
                return;
            }
            me.request(me.updateUrl, {form: fm, uuid: gc.get('uuid')}, {
                maskId: me.createMask(win, '正在电脑教室'),
                success: function(){
                    me.store.reload();
                    win.destroy();
                }
            });
        }, this);
        win.show();
        fm = win.down('form').getForm();
        fm.setValues(gc.data);
        fm.findField('school_year').setValue(gc.get('school_year')+' （'+gc.get('term_type')+'）');
        range = fm.findField('lesson_range');
        range._value = gc.get('lesson_range').map(function(v){return v[1]});
        range.store.owner = range;
        range.store.on('load', function(){
            var s = this, o = s.owner, vs = [];
            s.each(function(m){
                if(Ext.Array.indexOf(o._value, m.get('name')) != -1) {
                    vs.push(m.get('uuid'));
                }
            });
            setTimeout(function(){ o.setValue(vs); }, 100);
            range.store.un('load', arguments.callee);
        });
        range.setValue('xx');
    },
    removeGradeClass: function(){
        var me = this, gc, select, maskId;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择电脑教室！');
            return;
        }
        gc = select[0];
        passCB = function(){
            me.request(me.removeUrl, {uuid:gc.get('uuid')}, {
                success: function(){
                    me.store.reload();
                },
                maskId: me.createMask(me, '正在删除电脑教室')
            });
        };
        Ext.Msg.show({
            title: '提示',
            buttons: Ext.MessageBox.YESNO,
            icon: Ext.MessageBox.ERROR,
            msg: '删除该教室，是否执行？',
            fn: function(b){
                b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
            }
        });
    },
    hasSchoolYear: function(win){
        bbt.loadCurrentSchoolYear(function(opts, _, resp){
            var data = Ext.decode(resp.responseText);
            if(data.status == "success") {
                win.down('displayfield').setValue(data.data.school_year+' （'+data.data.term_type+'）');
            } else {
                Ext.Msg.alert('提示', '当前没有学年学期!', function(){
                    win.destroy();
                });
            }
        });
    },
    getGradeClassWindowConfig: function(title, method){
        var classes, winc;
        bbt.loadClasses(function(data){
            classes = data;
        });
        winc = {
            xtype: 'window',
            modal: true,
            title: title||'添加电脑教室',
            width: 350,
            //height: 200,
            closable: false,
            items: [{
                xtype: 'form',
                margin: 20,
                bodyCls: 'no-bg',
                border: false,
                layout: 'anchor',
                defaults: {anchor: '100%', allowBlank: false, margin: '10 0 0 0'},
                items: [{
                    xtype: 'displayfield',
                    name: 'school_year',
                    value: '',
                    fieldLabel: '学年学期'
                }, {
                    xtype: 'hidden',
                    name: 'grade_name',
                    value: '电脑教室'
                }, {
                    xtype: 'textfield',
                    fieldLabel: '教室名称',
                    name: 'name',
                    maxLength: 10,
                    emptyText: '请自定义名称，如“301电脑教室”',
                    validator: function(v){
                        if(Ext.String.trim(v) === "") {
                            return "教室名称应该不允许为空格";
                        } else {
                            return true;
                        }
                    }
                }, {
                    xtype: 'textfield',
                    name: 'client_number',
                    fieldLabel: '学生机数量',
                    regex: /^[0-9]\d*$/,
                    regexText: '无效的数字',
                    emptyText: '非机房类专业课教室，请填0'
                }, {
                    xtype: 'tagfield',
                    //readOnly: method == 'edit',
                    fieldLabel: '授课课程范围',
                    name: 'lesson_range',
                    displayField: 'name',
                    valueField: 'uuid',
                    hideTrigger: true,
                    store: new Ext.data.Store({
                        fields: ['number', 'name', 'types', 'remark', 'uuid'],
                        proxy: {
                            url: '/system/baseinfo/lesson-name/',
                            extraParams: {donot_pagination:true},
                            type: 'ajax',
                            reader: {type: 'json', root: 'data.records',totalProperty: 'data.record_count'}
                        }
                    })
                }]
            }],
            buttons: [{
                text: '确定',
                action: 'submit'
            }, {
                text: '关闭',
                handler: function(){ this.up('window').destroy(); }
            }],
            buttonAlign: 'right'
        };
        return winc;
    },
    viewCourseTable: function(){
        var me = this, select, gc, win;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            gc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        win = Ext.widget({
            xtype: 'window',
            modal: true,
            title: '课程表: ' + gc.get('name'),
            layout: 'fit',
            width: 800,
            items: [{
                xtype: 'grid',
                border: false,
                overflowX: 'hidden',
                store: new Ext.data.Store({
                    fields: ['jieci', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
                    sorters: [{property: 'jieci', direction: 'ASC'}]
                }),
                columns: {
                    defaults: {
                        sortable: false,
                        menuDisabled: true,
                        draggable: false,
                        height: 22,
                        width: 95
                    },
                    items: [{
                        text: '节次',
                        dataIndex: 'jieci',
                        width: 130,
                        renderer: function(v,m,r){
                            return v + ' (' + r.raw.start_time + '~' + r.raw.end_time + ')';
                        }
                    }, {
                        text: '周一',
                        dataIndex: 'mon'
                    }, {
                        text: '周二',
                        dataIndex: 'tue'
                    }, {
                        text: '周三',
                        dataIndex: 'wed'
                    }, {
                        text: '周四',
                        dataIndex: 'thu'
                    }, {
                        text: '周五',
                        dataIndex: 'fri'
                    }, {
                        text: '周六',
                        dataIndex: 'sat'
                    }, {
                        text: '周日',
                        dataIndex: 'sun',
                        flex: 1
                    }]
                }
            }],
            loadTable: function(){
                var w = this;
                Ext.Ajax.request({
                    url: me.viewUrl,
                    params: {
                        uuid: gc.get('uuid')
                    },
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText);
                        if(data.status == "success") {
                            w.feed(data.data);
                        }
                    }
                });
            },
            feed: function(data){
                var rows = [], store = this.down('grid').store;
                
                Ext.each(data, function(cell){
                    var row_num = cell.lesson_period__sequence,
                        obj = rows[row_num];
                    if(typeof obj == "undefined") { obj = rows[row_num] = {}; }
                    obj[cell.weekday] = cell.lesson_name__name;
                    obj.jieci = row_num;
                    if(!obj.start_time) {
                        obj.start_time = cell.lesson_period__start_time.substring(0, 5);
                        obj.end_time = cell.lesson_period__end_time.substring(0, 5);
                    }
                });
                rows = Ext.Array.filter(rows, function(row){ return !!row; });
                store.add(rows);
            }
        });
        win.loadTable();
        win.show();
    }
});
/* 学校作息时间管理 */
Ext.define('bbt.Worktime', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.worktime',
    fields: ['sequence', 'start_time', 'end_time', 'uuid', 'term__school_year', 'term__term_type'],
    pagination: true,
    columns: [{
        text: '学年',
        dataIndex: 'term__school_year'
    }, {
        text: '学期类型',
        dataIndex: 'term__term_type'
    }, {
        text: '节次',
        dataIndex: 'sequence',
        width: 50,
        editor: {xtype: 'textfield', regex: /^\d+$/, regexText: '无效的数字'}
    }, {
        text: '开始时间',
        dataIndex: 'start_time',
        width: 150,
        editor: {xtype: 'timefield', format: 'H:i'},
        renderer: function(v) {
            if(Ext.isDate(v)) {
                return Ext.Date.format(v, 'H:i');
            } else {
                return v;
            }
        }
    }, {
        text: '结束时间',
        dataIndex: 'end_time',
        editor: {xtype: 'timefield', format: 'H:i'},
        renderer: function(v) {
            if(Ext.isDate(v)) {
                return Ext.Date.format(v, 'H:i');
            } else {
                return v;
            }
        }
    }],
    //showOperateColumn: false,
    tbar: [{
        text: '添加节次',
        action: 'add',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '编辑节次',
        action: 'edit',
        iconCls: 'tool-icon icon-edit'
    }, {
        text: '删除',
        action: 'remove',
        iconCls: 'tool-icon icon-delete'
    }/*, {
        xtype: 'form',
        bodyCls: 'no-bg',
        border: false,
        items: [{
            xtype : 'fileuploadfield',
            name : 'excel',
            buttonOnly : true,
            margin : 0,
            padding : 0,
            buttonConfig : {text : '导入', iconCls: 'icon-import'},
            listeners: {
                change: function(f, path){
                    var grid = f.up('worktime');
                    if(!/\.xlsx?$/.test(path)) {
                        //Ext.Msg.alert('提示', '请选择 excel 文件！');
                        f.reset();
                        return;
                    }
                    f.up('form').submit({
                        url: grid.importUrl,
                        success: function(form, a){ f.reset(); grid.store.load(); },
                        failure: function(){ f.reset(); }
                    });
                }
            }
        }]
    }*/, '->', '注：编辑作息时间后，需重启服务器生效。'],
    listUrl: '/system/lesson_period/list/',
    addUrl: '/system/lesson_period/add/',
    updateUrl: '/system/lesson_period/edit/',
    removeUrl: '/system/lesson_period/delete/',
    importUrl: '/system/lesson_period/import/',
    actionMap: {add: 'addJieci', edit: 'editJieci', remove: 'removeJieci'},
    showOperateColumn: false,
    listeners: {
        show: function(){ this.store.load(); }
    },
    addJieci: function(){
        var me = this, win = new Ext.window.Window(Ext.apply(this.getJieciWindowConfig(), {
            title: '添加节次',
            buttons: [{
                text: '添加',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),msg;
                    msg = me.checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加节次……'),
                        success: function(){
                            me.store.reload();
                            win.destroy();
                        },
                        failure: function(d){
                            Ext.Msg.alert('提示', getErrorMsg(d));
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 30 0 20',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        })), newSequence, last, d = new Date(), span;
        newSequence = me.store.proxy.reader.rawData.data.max_sequence+1;
        last = me.store.getAt(newSequence-2);
        win.down('textfield[name=sequence]').setValue(newSequence||1);
        if(last) {
            span = last.get('end_time').split(':');
            d.setHours(parseInt(span[0]));
            d.setMinutes(parseInt(span[1]));
            win.down('timefield[name=start_time]').setMinValue(d);
            win.down('timefield[name=end_time]').setMinValue(d);
        }
        win.show();
        me.hasSchoolYear(win);
    },
    editJieci: function() {
        var me = this, win, fm, select, jieci, d, times;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            jieci = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        win = new Ext.window.Window(Ext.apply(this.getJieciWindowConfig(), {
            title: '编辑节次',
            buttons: [{
                text: '保存',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),msg;
                    msg = me.checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    me.request(me.updateUrl, {uuid: jieci.get('uuid'), form: fm}, {
                        maskId: me.createMask(win, '正在更新节次……'),
                        success: function(){
                            me.store.load();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 30 0 20',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        }));
        fm = win.down('form').getForm();

        fm.findField('sequence').setValue(jieci.get('sequence'));
        d = new Date();
        times = jieci.get('start_time').split(':');
        d.setHours(parseInt(times[0]));
        d.setMinutes(parseInt(times[1]));
        fm.findField('start_time').setValue(d);
        //
        d = new Date();
        times = jieci.get('end_time').split(':');
        d.setHours(parseInt(times[0]));
        d.setMinutes(parseInt(times[1]));
        fm.findField('end_time').setValue(d);
        fm.findField('school_year').setValue(jieci.get('term__school_year') + ' （' + jieci.get('term__term_type') + '）');
        win.show();
    },
    removeJieci: function(){
        var me = this, rc, i;
        rc = me.getSelectionModel().getSelection();
        if(rc.length) {
            rc = rc[0];
            i = me.store.indexOf(rc);
            //if(i+1 !== me.store.count()) {
            //    Ext.Msg.alert('提示', '只能删除最后一节！');
            //    return ;
            //}
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        passCB = function(){
            me.request(me.removeUrl, {uuid:rc.get('uuid')}, {
                maskId: me.createMask(me, '正在删除节次……'),
                success: function(){
                    me.store.reload();
                }
            });
        };
        Ext.Msg.confirm('提示', '删除作息时间将会影响班级课程表，班级课程授课教师等，确认要删除吗？', function(b){
            b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
        });
    },
    hasSchoolYear: function(win){
        bbt.loadCurrentSchoolYear(function(opts, _, resp){
            var data = Ext.decode(resp.responseText);
            if(data.status == "success") {
                win.down('displayfield').setValue(data.data.school_year+' （'+data.data.term_type+'）');
            } else {
                Ext.Msg.alert('提示', '当前没有学年学期!', function(){
                    win.destroy();
                });
            }
        });
    },
    getJieciWindowConfig: function(){
        var config, school_yearStore;
        school_yearStore = new Ext.data.Store({
            autoLoad: true,
            fields: ['school_year'],
            proxy: {
                type: 'ajax',
                url: '/system/term/list_school_year/',
                reader: {type: 'json', root: 'data.records'}
            }
        });
        config = {
            xtype: 'window',
            modal: true,
            closable: false,
            resizable: false,
            width: 350,
            //height: 205,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls:'no-bg',
                layout: 'anchor',
                margin: 30,
                border: false,
                defaults: {allowBlank: false, anchor: '100%'},
                items: [{
                    xtype: 'displayfield',
                    name: 'school_year',
                    fieldLabel: '学年学期',
                    value: ''
                }, {
                    xtype: 'textfield',
                    name: 'sequence',
                    fieldLabel: '节次',
                    regex: /^\d+$/,
                    regexText: '无效的数字',
                    readOnly: true
                }, {
                    xtype: 'timefield',
                    fieldLabel: '开始时间',
                    format: 'H:i',
                    name: 'start_time'
                }, {
                    xtype: 'timefield',
                    fieldLabel: '结束时间',
                    format: 'H:i',
                    name: 'end_time'
                }]
            }],
            buttonAlign: 'right'
        };
        return config;
    }
});

/* 教职人员信息管理 */
Ext.define('bbt.Teacher', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.teacher',
    //selModel: Ext.create('Ext.selection.CheckboxModel'),
    fields: ['uuid', 'sequence', 'status_count', 'name', 'password', 'sex', 'edu_background', 'birthday', 'title', 'mobile', 'qq', 'remark', 'register_at', 'school'],
    pagination: true,
    columns: [{
        text : 'ID',
        dataIndex : 'sequence',
        width: 50
    }, {
        text : '姓名',
        dataIndex : 'name'
    }, {
        text: '性别',
        dataIndex: 'sex',
        width: 40,
        renderer: function(v){ return {"male": "男", "female": "女"}[v] || v; }
    }, {
        text : '学历',
        dataIndex : 'edu_background'
    }, {
        text: '出生年月',
        dataIndex: 'birthday',
        renderer: bbt.utils.strftime
    }, {
        text : '教师职称',
        dataIndex : 'title'
    }, {
        text: '注册时间',
        dataIndex: 'register_at',
        renderer: function(v){ return v ? v.substring(0, 10) : ''; }
    }, {
        text: '移动电话',
        dataIndex: 'mobile'
    }, {
        text: 'QQ',
        dataIndex: 'qq'
    }, {
        text: '状态',
        dataIndex: 'status',
        width: 50,
        renderer: function(v,m,r) {
            return r.get('status_count') > 0 ? '授课' : '停课';
        }
    }, {
        text: '备注',
        dataIndex: 'remark',
        flex: 1
    }],
    showOperateColumn: true,
    dockedItems: [{
        xtype: 'toolbar',
        layout: {overflowHandler: 'Menu'},
        items: [{
            text: '添加',
            action: 'add',
            iconCls: 'tool-icon icon-add'
        }, {
            text: '删除',
            action: 'remove',
            iconCls: 'tool-icon icon-delete'
        }, {
            xtype: 'form',
            bodyCls: 'no-bg',
            border: false,
            items: [{
                xtype : 'fileuploadfield',
                name : 'excel',
                buttonOnly : true,
                margin : 0,
                padding : 0,
                buttonConfig : {text : '导入', iconCls: 'tool-icon icon-import'},
                listeners: {
                    change: function(f, path){
                        var grid = f.up('teacher');
                        if(!/\.xlsx?$/.test(path)) {
                            //Ext.Msg.alert('提示', '请选择 excel 文件！');
                            f.reset();
                            return;
                        }
                        f.up('form').submit({
                            url: grid.importUrl,
                            success: function(form, a){ f.reset(); Ext.Msg.alert('提示', '导入成功！'); grid.load(); },
                            failure: function(){ f.reset(); }
                        });
                    }
                }
            }]
        }, '->',
        bbt.ToolBox.get('export'),
        {
            text: '教师 UKey 生产程序',
            iconCls: 'tool-icon icon-download',
            href: '/download/usbkey.zip'
        }]
    }, {
        xtype: 'toolbar',
        layout: {overflowHandler: 'Menu'},
        items: [bbt.ToolBox.get('iTeacherName'),
            bbt.ToolBox.get('sex'),
            bbt.ToolBox.get('edubg'),

            bbt.ToolBox.get('ttitle'),
            bbt.ToolBox.get('tstatus'),

            bbt.ToolBox.get('query')
        ]
    }],
    operates: {edit: '编辑', reset: '重置密码'},
    actionMap: {
        add: 'addTeacher',
        edit: 'editTeacher',
        remove: 'removeTeacher',
        reset: 'resetPassword'
    },
    listeners: {
        show: function(){ this.store.load(); }
    },
    listUrl: '/system/teacher/list/',
    addUrl: '/system/teacher/add/',
    updateUrl: '/system/teacher/edit/',
    removeUrl: '/system/teacher/delete/',
    exportUrl: '/system/teacher/export/',
    importUrl: '/system/teacher/import/',
    checkPassword: function(fm, name, name2) {
        if(arguments.length === 1) {
            name = 'password',
            name2 = 'password_confirmation';
        }
        fm.xtype === "form" && (fm = fm.getForm());
        var v1 = fm.findField(name).getValue();
        var v2 = fm.findField(name2).getValue();
        return v1 === v2;
    },
    resetPassword: function(){
        var me = this, select, cb;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择教师！');
            return;
        }
        select = select[0];
        cb = function(){
            Ext.Ajax.request({
                url: '/system/teacher/password-reset/',
                method: 'POST',
                params: {uuid: select.get('uuid')},
                callback: function(_1, _2, resp){
                    var data = Ext.decode(resp.responseText);
                    if(data.status == "success") {
                        Ext.Msg.alert('提示', '教师 ' + select.get('name') + ' 密码已重置为：' + data.data.pwd);
                    }
                }
            });
        };
        Ext.Msg.confirm('提示', '确定要重置教师 ' + select.get('name') + ' 的密码吗？', function(b){
            (b == 'yes') && cb();
        });
    },
    addTeacher: function(){
        var me = this, config, win, values;
        config = Ext.apply(me.getTeacherWindowConfig(), {
            title: '添加教师信息',
            buttons: [{
                text : '确定',
                handler : function (b) {
                    var win = b.up('window'), fm, f, validateMsg, params;
                    fm = win.down('form');
                    validateMsg = me.checkForm(fm);
                    if (validateMsg !== true) {
                        //Ext.Msg.alert('提示', validateMsg);
                        return;
                    }
                    f = Ext.Date.format(fm.down('[name=birthday]').getValue(), 'md');
                    params = {password: f, password_confirmation: f, form: fm};
                    me.request(me.addUrl, params, {
                        form: fm,
                        maskId: me.createMask(win, '正在添加教师'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        },
                        failure: function(){
                            console.log('[beer]:', arguments);
                        }
                    });
                }
            }, {
                text : '关闭',
                margin : '0 10 0 20',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        //me.initTeacherWindowEvents(win, 'add');
        win.show();
    },
    editTeacher: function(){
        var me = this, config, win, teacher, select, fm, values, f;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择教师！');
            return;
        }
        teacher = select[0];
        config = Ext.apply(me.getTeacherWindowConfig(), {
            title: '编辑教师信息',
            buttons: ['->', {
                text : '确定',
                handler : function (b) {
                    var win = b.up('window'), fm, f, validateMsg, params = {};
                    fm = win.down('form');

                    validateMsg = checkForm(fm);
                    if (validateMsg !== true) {
                        //Ext.Msg.alert('提示', validateMsg);
                        return;
                    }
                    if(fm.setPassword === true) {
                        f = Ext.Date.format(fm.down('[name=birthday]').getValue(), 'md');
                        params.password = f;
                        params.password_confirmation = f;
                    }
                    params.uuid = teacher.get('uuid');
                    params.form = fm;
                    me.request(me.updateUrl, params, {
                        form: fm,
                        maskId: me.createMask(win, '正在修改教师'),
                        success: function(data){
                            teacher.set(data.data);
                            teacher.commit();
                            Ext.Msg.alert('提示', '修改成功！');
                            win.destroy();
                        },
                        alertOnFailure: true
                    });
                }
            }, {
                text : '关闭',
                margin : '0 10 0 20',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        //me.initTeacherWindowEvents(win, 'edit');
        fm = win.down('form').getForm();
        fm.setValues(teacher.data);
        fm.findField('name').setReadOnly(true);
        //f = fm.findField('password');
        //f.setDisabled(true);
        //f.hide();
        //f = fm.findField('password_confirmation');
        //f.setDisabled(true);
        //f.hide();
        win.show();
    },
    removeTeacher: function(){
        var me = this, msg, teacher, select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '未选择教师！');
            return;
        }
        teacher = select[0];
        if(me.removeUrl) {
            me.request(me.removeUrl, {uuid:teacher.get('uuid')}, {
                maskId: me.createMask(this, '确定要删除教师 ' + teacher.get('username') + ' 吗？'),
                success: function(){
                    me.store.reload();
                }
            });
        } else {
            me.store.remove(teacher);
        }
    },
    getTeacherWindowConfig: function(){
        var config = {
            xtype: 'window',
            closable: false,
            resizable: false,
            modal : true,
            width : 475,
            items : [{
                xtype : 'form',
                bodyCls : 'no-bg',
                border : false,
                margin : 10,
                layout: {type: 'vbox', align: 'stretch'},
                items : [{
                    defaults : {
                        layout : {type : 'vbox',align : 'stretch'},
                        border : false,
                        bodyCls : 'no-bg',
                        flex:1
                    },
                    layout : {type : 'hbox',align : 'stretch'},
                    border: false,
                    bodyCls: 'no-bg',
                    defaultType : 'panel',
                    items: [{
                        defaultType : 'textfield',
                        defaults : {
                            margin : '5 5 5 0',
                            labelWidth : 60
                        },
                        items : [{
                                fieldLabel : 'ID',
                                allowBlank : true,
                                readOnly : true,
                                emptyText : '系统自动生成'
                            }, {
                                xtype: 'combo',
                                queryMode: 'local',
                                editable: false,
                                store: [['female', '女'], ['male', '男']],
                                name: 'sex',
                                value: 'male',
                                fieldLabel: '性别',
                                allowBlank: false
                            }, {
                                xtype: 'datefield',
                                name: 'birthday',
                                format: 'Y-m-d',
                                editable: false,
                                fieldLabel: '出生年月'/*,
                                listeners: {
                                    change: function(me, nv, ov){
                                        var p1 = me.up('form').down('[name=password]'),
                                            p2 = me.up('form').down('[name=password_confirmation]'),
                                            newpwd = Ext.Date.format(nv, 'md'),
                                            oldpwd = ov ? Ext.Date.format(ov, 'md') : '';
                                        if(p1.getValue() == oldpwd && p2.getValue() == oldpwd) {
                                            p1.setValue(newpwd);
                                            p2.setValue(newpwd);
                                        }
                                    }
                                }*/
                            }, {
                                xtype: 'textfield',
                                name: 'mobile',
                                fieldLabel: '移动电话',
                                regex: /^1\d{10}$/,
                                regexText: '无效的手机号码'
                            }]
                    }, {
                        defaultType : 'textfield',
                        defaults : {
                            margin : '5 0 5 5',
                            labelWidth : 60
                        },
                        items: [{
                            name : 'name',
                            fieldLabel : '姓名',
                            allowBlank : false
                        }, {
                            xtype: 'combo',
                            name : 'edu_background',
                            editable: false,
                            fieldLabel : '学历',
                            store: ['大专', '本科', '硕士', '博士', '其他'],
                            allowBlank: false
                        }, {
                            xtype: 'combo',
                            fieldLabel: '教师职称',
                            name: 'title',
                            editable: false,
                            store: ['正高级', '高级', '一级', '二级', '三级']
                        }, {
                            xtype: 'textfield',
                            name: 'qq',
                            fieldLabel: 'QQ',
                            regex: /^\d+$/,
                            regexText: '无效的QQ号'
                        }]
                    }]
                }, {
                        margin: '5 0 0 0',
                        xtype: 'textarea',
                        name: 'remark',
                        fieldLabel: '备注',
                        labelWidth: 60
                    }
                ]
            }],
            buttonAlign: 'right'
        };
        return config;
    }
});
/* 班级课程授课老师管理 */
Ext.define('bbt.TeachInfo', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.teachinfo',
    fields: ['uuid', 'class_uuid__grade__term__school_year', 'class_uuid__grade__term__term_type', 'class_uuid__grade__name', 'class_uuid__name', 'lesson_name__name', 'teacher__name', 'teacher__birthday', 'schedule_time', 'remain_time'],
    columns: [{
        text: '学年',
        dataIndex: 'class_uuid__grade__term__school_year'
    }, {
        text: '学期类型',
        dataIndex: 'class_uuid__grade__term__term_type'
    }, {
        text: '年级',
        dataIndex: 'class_uuid__grade__name',
        renderer: function(v){ return v ? v + '年级' : '';}
    }, {
        text: '班级',
        dataIndex: 'class_uuid__name',
        renderer: function(v){ return v ? v + '班' : '';}
    }, {
        text: '课程',
        dataIndex: 'lesson_name__name'
    }, {
        text: '授课教师',
        dataIndex: 'teacher__name'
    }, {
        text: '教师生日',
        dataIndex: 'teacher__birthday'
    }, {
        text: '计划课时',
        dataIndex: 'schedule_time'
    }],
    pagination: true,
    //年级（所有（默认）、各年级），班级（所有（默认）、各班级）；课程（所有（默认）、各课程）；授课老师（关键字查询）；【查询】；
    tbar: ['gradeOld', 'classOld', 'courseOld', 'iTeacherName', 'query', {
        text: '新增',
        action: 'add',
        iconCls: 'tool-icon icon-add'
    }, {
        xtype: 'form',
        bodyCls: 'no-bg',
        border: false,
        items: [{
            xtype : 'fileuploadfield',
            name : 'excel',
            buttonOnly : true,
            margin : 0,
            padding : 0,
            buttonConfig : {text : '导入', iconCls: 'tool-icon icon-import'},
            listeners: {
                change: function(f, path){
                    var grid = f.up('teachinfo'), cb;
                    if(!path) { return; }
                    if(!/\.xlsx?$/.test(path)) {
                        Ext.Msg.alert('提示', '请选择 excel 文件！');
                        f.reset();
                        return;
                    }
                    cb = function(b){
                        if(b != 'yes') { f.reset();return; }
                        f.up('form').submit({
                            url: grid.importUrl,
                            success: function(form, a){ f.reset(); Ext.Msg.alert('提示', '导入成功！'); grid.load(); },
                            failure: function(form, a){ f.reset(); Ext.Msg.alert('提示', getErrorMsg(a.result)); }
                        });
                    };
                    if(grid.store.count() > 0) {
                        Ext.Msg.confirm('提示', '本次操作将会先清除未产生实际数据的条目，再执行新增导入，是否继续？', cb);
                    } else {
                        cb('yes');
                    }
                }
            }
        }]
    }, '->', 'export'],
    listeners: {
        show: function(){ this.store.load(); },
        afterrender: function(){
            bbt.autoFill(this);
        }
    },
    listUrl: '/system/lesson_teacher/list/',
    addUrl: '/system/lesson_teacher/add/',
    updateUrl: '/system/lesson_teacher/edit/',
    removeUrl: '/system/lesson_teacher/delete/',
    exportUrl: '/system/lesson_teacher/export/',
    importUrl: '/system/lesson_teacher/import/',
    showOperateColumn: true,
    operates: {remove: '删除', edit: '编辑'},
    actionMap: {
        add: 'addTeachInfo',
        edit: 'updateTeachInfo',
        remove: 'removeTeachInfo'
    },
    addTeachInfo: function(){
        var me = this, win = new Ext.window.Window(Ext.apply(this.getTeachInfoWindowConfig(), {
            title: '添加班级课程授课老师信息',
            buttons: [{
                text: '添加',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),
                        msg;
                    fm.down('[name=birthdayOld]').setDisabled(true);
                    msg = me.checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加……'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                handler: function(){ this.up('window').destroy(); }
            }]
        })), updateRemain, timer;
        updateRemain = function(){
            var params = {}, target = win.down('[name=remain_time]');
            params.class_name = win.down('[name=class_name]').getValue();
            params.grade_name = win.down('[name=grade_name]').getValue();
            if(!(params.grade_name && params.class_name)) { return; }
            Ext.Ajax.request({
                url: '/system/lesson_teacher/remain_time/',
                params: params,
                callback: function(opts, _, resp) {
                    var data = Ext.decode(resp.responseText);
                    if(data.status == "success") {
                        target.setValue(data.data.remain_time);
                    }
                }
            });
            timer = null;
        };
        win.down('[name=grade_name]').on('change', function(){
            if(timer) { clearTimeout(timer); }
            timer = setTimeout(updateRemain, 10);
        });
        win.down('[name=class_name]').on('change', function(){
            if(timer) { clearTimeout(timer); }
            timer = setTimeout(updateRemain, 10);
        });
        win.show();
        this.hasSchoolYear(win);
    },
    updateTeachInfo: function(){
        var me = this, select = me.getSelectionModel().getSelection(), teach, win, fm, namemap, bf, tmp;
        if(select.length) {
            teach = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        win = new Ext.window.Window(Ext.apply(this.getTeachInfoWindowConfig(), {
            title: '编辑班级课程授课老师信息',
            //height: 300,
            buttons: [{
                text: '保存',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),
                        msg, teacherName;
                    msg = me.checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    teacherName = fm.down('[name=teacher]');
                    teacherName = teacherName.findRecordByValue(teacherName.getValue()).get('name');
                    me.request(me.updateUrl, {uuid: teach.get('uuid'), form: fm}, {
                        maskId: me.createMask(win, '正在编辑……'),
                        success: function(){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                handler: function(){ this.up('window').destroy(); }
            }]
        }));
        fm = win.down('form').getForm();

        namemap = {
            school_year: 'class_uuid__grade__term__school_year',
            grade_name: 'class_uuid__grade__name',
            class_name: 'class_uuid__name',
            lesson_name: 'lesson_name__name',
            teacher: 'teacher__name'
        };
        /*Ext.Object.each(namemap, function(k, v){
            var f = fm.findField(k), cb;
            if(k == 'school_year') {
                f.setValue();
                return;
            }
            f.setDisabled(true);
            if(k != 'teacher') {
                v = teach.get(v);
            } else {
                v = teach.raw.teacher__uuid;
            }
            if(f.store.isLoading()) {
                cb = function(){
                    f.setValue(v);
                    f.store.un('load', cb);
                };
                f.store.on('load', cb);
            } else {
                f.setValue(v);
            }
        });*/
        fm.findField('school_year').setValue(teach.get('class_uuid__grade__term__school_year') + ' （' + teach.get('class_uuid__grade__term__term_type') + '）');
        tmp = fm.findField('grade_name');
        tmp.suspendEvents(false);
        tmp.setValue(teach.get('class_uuid__grade__name')).setDisabled(true);
        tmp = fm.findField('class_name');
        tmp.suspendEvents(false);
        tmp.setValue(teach.get('class_uuid__name')).setDisabled(true);
        fm.findField('lesson_name').setValue(teach.get('lesson_name__name')).setDisabled(true);
        fm.findField('teacher').setValue(teach.raw.teacher__uuid).setDisabled(true);
        fm.findField('schedule_time').setValue(teach.get('schedule_time'));
        fm.findField('remain_time').setValue(teach.get('remain_time'));
        win.show();
        bf = fm.findField('birthdayOld');
        bf.setDisabled(true);
        bf.hide();
    },
    removeTeachInfo: function(){
        var me = this, select = me.getSelectionModel().getSelection(), teach;
        if(select.length) {
            teach = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        passCB = function(){
            me.request(me.removeUrl, {uuid: teach.get('uuid')}, {
                maskId: me.createMask(me, '正在删除班级课程授课老师信息'),
                success: function(){
                    me.store.reload();
                }
            });
        };
        Ext.Msg.confirm('提示', '删除该记录将会影响班级授课教师信息，统计分析等，确认要删除吗？', function(b){
            b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
        });
    },
    hasSchoolYear: function(win){
        bbt.loadCurrentSchoolYear(function(opts, _, resp){
            var data = Ext.decode(resp.responseText);
            if(data.status == "success") {
                win.down('displayfield').setValue(data.data.school_year+' （'+data.data.term_type+'）');
            } else {
                Ext.Msg.alert('提示', '当前没有学年学期!', function(){
                    win.destroy();
                });
            }
        });
    },
    getTeachInfoWindowConfig: function(){
        var grade = bbt.ToolBox.get('gradeOld', {displayAll: false}),
            clazz = bbt.ToolBox.get('classOld', {displayAll: false}),
            lesson_name = bbt.ToolBox.get('courseOld', {displayAll: false}),
            teacher_name = bbt.ToolBox.get('teacherName', {
                valueField: 'uuid',
                name: 'teacher'
            });
        delete grade.labelWidth;
        delete clazz.labelWidth;
        delete lesson_name.labelWidth;
        delete teacher_name.labelWidth;

        clazz.store.removeAll();
        delete teacher_name.hideTrigger;
        teacher_name.store.on('load', function(s){
            var rc = s.getAt(0);
            if(rc.get('value') === '') {
                s.remove(rc);
            }
        });
        Ext.merge(teacher_name, {listeners:{
            change: function(me, v){
                var rc = me.findRecordByValue(v),
                    birthday = me.ownerCt.down('[name=birthdayOld]'),
                    data = [];
                if(rc) {
                    me.store.each(function(m){
                        if(m.get('text') == rc.get('text')) {
                            data.push({birthday: m.get('birthday'), uuid: m.get('uuid')});
                        }
                    });
                    birthday.store.loadData(data);
                    birthday.setValue(v);
                    birthday.setDisabled(data.length <= 1);
                } else {
                    birthday.setDisabled(true);
                    birthday.setValue(undefined);
                    birthday.store.removeAll();
                }
            }
        }});
        var winc = {
            modal: true,
            width: 380,
            closable: false,
            resizable: false,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls: 'no-bg',
                border: false,
                margin: 30,
                layout: 'anchor',
                defaults: {anchor: '100%', allowBlank: false, margin: '10 0 0 0'},
                items: [{
                    xtype: 'displayfield',
                    fieldLabel: '学年学期',
                    name: 'school_year',
                    value: ''
                }, grade, clazz, lesson_name, teacher_name, {
                    xtype: 'combo',
                    fieldLabel: '教师生日',
                    name: 'birthdayOld',
                    displayField: 'birthday',
                    valueField: 'uuid',
                    editable: false,
                    disabled: true,
                    queryMode: 'local',
                    store: new Ext.data.Store({fields:['birthday', 'uuid']}),
                    listeners: {
                        change: function(me, v){
                            var rc;
                            if(v){
                                me.ownerCt.down('[name=teacher]').setValue(v);
                                rc = me.findRecordByValue(v);
                                me.ownerCt.down('[name=birthday]').setValue(rc.get(me.displayField));
                            }
                        }
                    }
                }, {
                    xtype: 'hidden',
                    name: 'birthday'
                }, {
                    xtype: 'textfield',
                    name: 'schedule_time',
                    fieldLabel: '分配课时',
                    regex: /^\d+$/,
                    regexText: '无效的数字'
                }, {
                    xtype: 'displayfield',
                    name: 'remain_time',
                    fieldLabel: '本班剩余课时',
                    regex: /^\d+$/,
                    regexText: '无效的数字'
                }]
            }],
            buttonAlign: 'center'
        };
        return winc;
    }
});
/* 班级课程表管理 */
Ext.define('bbt.CourseTable', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.coursetable',
    fields: ['grade__name', 'name', 'grade__term__school_year', 'grade__term__term_type', 'teacher__name', 'teacher__birthday', 'classtime__schedule_time', 'classtime__assigned_time', 'grade__term__schedule_time', 'assigned_time'],
    columns: [{
        text: '学年',
        dataIndex: 'grade__term__school_year'
    }, {
        text: '学期类型',
        dataIndex: 'grade__term__term_type'
    }, {
        text: '年级',
        dataIndex: 'grade__name',
        renderer: function(v){ return v ? v + '年级' : '';}
    }, {
        text: '班级',
        dataIndex: 'name',
        renderer: function(v){ return v ? v + '班' : '';}
    }, {
        text: '本学期班主任',
        dataIndex: 'teacher__name'
    }, {
        text: '出生年月',
        dataIndex: 'teacher__birthday'
    }, {
        text: '学期参考计划课时',
        width: 120,
        //dataIndex: 'classtime__schedule_time'
        dataIndex: 'grade__term__schedule_time'
    }, {
        text: '已分配课时',
        //dataIndex: 'classtime__assigned_time'
        dataIndex: 'assigned_time'
    }, {
        text: '未分配课时',
        dataIndex: 'xxx',
        renderer: function(v,m,r){
            var a, b;
            //a = r.get('classtime__schedule_time') || 0;
            a = r.get('grade__term__schedule_time') || 0;
            //b = r.get('classtime__assigned_time') || 0;
            b = r.get('assigned_time') || 0;
            return a - b;
        }
    }],
    pagination: true,
    showOperateColumn: true,
    listUrl: '/system/class/list/',
    listScheduleUrl: '/system/lesson_schedule/list/',
    updateUrl: '/system/lesson_schedule/edit/',
    importUrl: '/system/lesson_schedule/import/',
    operates: {'import': '导入', preview: '预览', 'export': '导出'},
    actionMap: {'import': 'importSchedule', preview: 'previewSchedule', 'export': 'exportSchedule'},
    listeners: {
        afterrender: function(){
            this.store.load();
            this.store.on('load', this.bindPreview, this);
            this.getEl().insertHtml('beforeEnd', '<div style="position:absolute;top:0;left:0;z-index:19999;width:800px;height:300px;box-shadow: 0 0 25px #000;" id="preview-course-body"></div>');
            Ext.get('preview-course-body').hide();
            this.initPreviewGrid();
        },
        itemmouseenter: function(me, rc){
            this.previewGrid.listUrl = this.listScheduleUrl + '?uuid=' + rc.raw.uuid; 
        },
        beforedestroy: function(){
            this.previewGrid.destroy();
        }
    },
    showPreview: function(e, t){
        var btnbox, pane, dy, bound, pbox;
        this.previewGrid.loadStore();
        btnbox = Ext.get(t).getBox();
        bound = this.body.getBox();
        pane = Ext.get('preview-course-body');
        pane.mask('loading ...');
        pbox = pane.getBox();
        
        if(btnbox.y - bound.y > pbox.height) {
            dy = btnbox.y - pbox.height;
        } else if((bound.y+bound.height) > (btnbox.y + btnbox.height + pbox.height)) {
            dy = btnbox.y + btnbox.height;
        } else {
            dy = bound.y + 5;
        }
        pane.setXY([btnbox.x-pane.getWidth(), dy]);
        pane.show();
    },
    hidePreview: function(){
        var p = Ext.get('preview-course-body');
        p.unmask();
        p.hide();
    },
    bindPreview: function(){
        var me = this;
        Ext.each(me.getEl().query('a[action=preview]'), function(el){
            el = Ext.get(el);
            el.on('mouseenter', me.showPreview, me);
            el.on('mouseleave', me.hidePreview, me);
        });
    },
    initPreviewGrid: function(){
        this.previewGrid = Ext.widget({
            xtype: 'grid',
            border: true,
            width: 800,
            height: 300,
            overflowX: 'hidden',
            store: new Ext.data.Store({
                fields: ['jieci', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],
                sorters: [{property: 'jieci', direction: 'ASC'}]
            }),
            renderTo: 'preview-course-body',
            columns: {
                defaults: {
                    sortable: false,
                    menuDisabled: true,
                    draggable: false,
                    height: 22,
                    width: 95
                },
                items: [{
                    text: '节次',
                    dataIndex: 'jieci',
                    width: 130,
                    renderer: function(v,m,r){
                        return v + ' (' + r.raw.start_time + '~' + r.raw.end_time + ')';
                    }
                }, {
                    text: '周一',
                    dataIndex: 'mon'
                }, {
                    text: '周二',
                    dataIndex: 'tue'
                }, {
                    text: '周三',
                    dataIndex: 'wed'
                }, {
                    text: '周四',
                    dataIndex: 'thu'
                }, {
                    text: '周五',
                    dataIndex: 'fri'
                }, {
                    text: '周六',
                    dataIndex: 'sat'
                }, {
                    text: '周日',
                    dataIndex: 'sun',
                    flex: 1
                }]
            },
            autoHeight: function(){
                var h = (this.store.count() + 1) * 21 + 10;
                this.setHeight(h);
                Ext.get('preview-course-body').setHeight(h);
            },
            feed: function(data){
                var rows = [], store = this.store;
                
                Ext.each(data, function(cell){
                    var row_num = cell.lesson_period__sequence,
                        obj = rows[row_num];
                    if(typeof obj == "undefined") { obj = rows[row_num] = {}; }
                    obj[cell.weekday] = cell.lesson_name__name;
                    obj.jieci = row_num;
                    if(!obj.start_time) {
                        obj.start_time = cell.lesson_period__start_time.substring(0, 5);
                        obj.end_time = cell.lesson_period__end_time.substring(0, 5);
                    }
                });
                store.removeAll();
                Ext.each(rows, function(row){
                    if(row) {
                        store.add(row);
                    }
                });
            },
            loadStore: function(){
                var me = this;
                Ext.Ajax.request({
                    url: this.listUrl,
                    callback: function(opts, _, resp) {
                        var data;
                        Ext.get('preview-course-body').unmask();
                        try {
                            data = Ext.decode(resp.responseText);
                            me.feed(data.data.records);
                            me.autoHeight();
                        } catch(e){
                            console.log(e);
                        }
                    }
                });
            }
        });
    },
    previewSchedule: function(){
        return;
        var select = this.getSelectionModel().getSelection(), win;
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        schedule = select[0];
        win = new Ext.window.Window(this.getScheduleWindowConfig(schedule.get('grade__name'), schedule.get('name'), schedule.raw.uuid));
        this.apply2ScheduleWindow(win);
        win.show();
    },
    importSchedule: function(){
        var me = this, select = this.getSelectionModel().getSelection(), win, winc, params, mask, schedule;
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        schedule = select[0];
        //params = {grade_name: schedule.get('grade__name'), class_name: schedule.get('name')};
        //2014-06-16 加入二个返回参数 school_year(学年) , term_type(学期类型)
        params = {school_year: schedule.get('grade__term__school_year'), term_type: schedule.get('grade__term__term_type') ,grade_name: schedule.get('grade__name'), class_name: schedule.get('name')};
        winc = {
            xtype: 'window',
            modal: true,
            title: '导入' + params.grade_name + '年级' + params.class_name + '班课程表',
            layout: {type: 'vbox', align: 'stretch'},
            width: 300,
            height: 180,
            items: [{
                xtype: 'component',
                flex: 1,
                margin: '30 30 10 30',
                html: '<p style="color:red;">注：如果该班级已经导入过课程表，本次导入将会予以覆盖！</p>'
            }, {
                xtype: 'form',
                border: false,
                margin: '0 30 30 30',
                flex: 1,
                bodyCls: 'no-bg',
                layout: {type: 'hbox', align: 'middle', pack: 'center'},
                items: [{
                    xtype: 'fileuploadfield',
                    name: 'excel',
                    buttonOnly : true,
                    importUrl: me.importUrl,
                    margin : 0,
                    padding : 0,
                    buttonConfig : {text : '选择文件并导入'},
                    listeners: {
                        change: function(f, path){
                            var grid = f.up('teacher');
                            if(!/\.xlsx?$/.test(path)) {
                                Ext.Msg.alert('提示', '请选择 excel 文件！');
                                f.reset();
                                return;
                            }
                            mask = new Ext.LoadMask(win, {msg: '正在导入课表'});
                            mask.show();
                            f.up('form').submit({
                                url: f.importUrl,
                                params: params,
                                success: function(form, a){ mask.hide(); Ext.Msg.alert('提示', '导入成功！', function(){ f.up('window').destroy(); }); },
                                failure: function(form, a){ mask.hide(); Ext.Msg.alert('提示', getErrorMsg(a.result)); }
                            });
                        }
                    }
                }]
            }]
        };
        win = new Ext.window.Window(winc).show();
        win.down('fileuploadfield').focus(false, 200);
    },
    exportSchedule: function(){
        var me = this, select = this.getSelectionModel().getSelection(), win, winc, params, mask, schedule;
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        schedule = select[0];
        Ext.Ajax.request({
            method: 'GET',
            url: '/system/lesson-schedule/export/',
            params: {
                grade_name: schedule.get('grade__name'),
                class_name: schedule.get('name')
            },
            callback: function(_1, _2, resp){
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    location.href = data.url;
                }
            }
        });
    },
    getScheduleWindowConfig: function(g, c, cuid){
        var winc = {
            xtype: 'window',
            modal: true,
            width: 800,
            height: 300,
            title: g + '年级' + c + '班课程表',
            layout: 'fit',
            items: [{
                xtype: 'grid',
                border: false,
                store: new Ext.data.Store({fields: ['jieci', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'],sorters: [{property: 'jieci', direction: 'ASC'}]}),
                importUrl: this.importUrl,
                listUrl: this.listScheduleUrl + '?uuid=' + cuid,
                /*tbar: ['->', {
                    xtype: 'form',
                    bodyCls: 'no-bg',
                    border: false,
                    items: [{
                        xtype : 'fileuploadfield',
                        name : 'excel',
                        buttonOnly : true,
                        margin : 0,
                        padding : 0,
                        buttonConfig : {text : '导入'},
                        uploadParams: {grade_name: g, class_name: c},
                        listeners: {
                            change: function(f, path){
                                var grid = f.up('grid');
                                if(!/\.xlsx?$/.test(path)) {
                                    Ext.Msg.alert('提示', '请选择 excel 文件！');
                                    f.reset();
                                    return;
                                }
                                f.up('form').submit({
                                    url: grid.importUrl,
                                    params: f.uploadParams,
                                    success: function(form, a){ f.reset(); grid.feed(a.result.data); },
                                    failure: function(){ f.reset(); }
                                });
                            }
                        }
                    }]
                }],*/
                columns: {
                    defaults: {
                        sortable: false,
                        menuDisabled: true,
                        draggable: false
                    },
                    items: [{
                        text: '节次',
                        dataIndex: 'jieci',
                        width: 50
                    }, {
                        text: '周一',
                        dataIndex: 'mon'
                    }, {
                        text: '周二',
                        dataIndex: 'tue'
                    }, {
                        text: '周三',
                        dataIndex: 'wed'
                    }, {
                        text: '周四',
                        dataIndex: 'thu'
                    }, {
                        text: '周五',
                        dataIndex: 'fri'
                    }, {
                        text: '周六',
                        dataIndex: 'sat'
                    }, {
                        text: '周日',
                        dataIndex: 'sun'
                    }]
                }
            }]
        };
        return winc;
    },
    apply2ScheduleWindow: function(win){
        var grid = win.down('grid');
        Ext.apply(grid, {
            feed: function(data){
                var rows = [], store = this.store;
                Ext.each(data, function(cell){
                    var row_num = cell.lesson_period__sequence,
                        obj = rows[row_num];
                    if(typeof obj == "undefined") { obj = rows[row_num] = {}; }
                    obj[cell.weekday] = cell.lesson_name__name;
                    obj.jieci = row_num;
                });
                Ext.each(rows, function(row){
                    if(row) {
                        store.add(row);
                    }
                });
            },
            loadStore: function(){
                var me = this;
                Ext.Ajax.request({
                    url: this.listUrl,
                    callback: function(opts, _, resp) {
                        var data;
                        try {
                            data = Ext.decode(resp.responseText);
                            me.feed(data.data.records);
                        } catch(e){}
                    }
                });
            }
        });
        grid.loadStore();
    }
});


/* basic info */
Ext.define('bbt.BasicInfo', {
    extend: 'Ext.tab.Panel',
    alias: 'widget.basicinfo',
    initComponent: function(){
        var stores = [
        new Ext.data.Store({
            fields: ['school_year', 'term_type', 'start_date', 'end_date', 'deleted'],
            proxy: {
                url: '/system/baseinfo/term/',
                type: 'ajax',
                reader: {type: 'json', root: 'data.records',totalProperty: 'data.record_count'}
            }
        }),
        new Ext.data.Store({
            fields: ['number', 'name', 'types', 'remark'],
            proxy: {
                url: '/system/baseinfo/lesson-name/',
                type: 'ajax',
                reader: {type: 'json', root: 'data.records',totalProperty: 'data.record_count'}
            }
        }),
        new Ext.data.Store({
            fields: ['value', 'remark'],
            proxy: {
                url: '/system/baseinfo/resource-from/',
                type: 'ajax',
                reader: {type: 'json', root: 'data.records',totalProperty: 'data.record_count'}
            }
        }),
        new Ext.data.Store({
            fields: ['value', 'remark'],
            proxy: {
                url: '/system/baseinfo/resource-type/',
                type: 'ajax',
                reader: {type: 'json', root: 'data.records',totalProperty: 'data.record_count'}
            }
        })];
        this.defaultType = 'grid';
        this.defaults = {border: false};
        this.items = [{
            title: '学年学期信息',
            columns: [{
                text: '学年',
                dataIndex: 'school_year'
            }, {
                text: '学期类型',
                dataIndex: 'term_type'
            }, {
                text: '开始时间',
                dataIndex: 'start_date'
            }, {
                text: '结束时间',
                dataIndex: 'end_date'
            }, {
                text: '状态',
                dataIndex: 'deleted',
                renderer: function(v){
                    return v ? "已结转" : "正常";
                }
            }],
            bbar: {xtype: 'pagingtoolbar', store: stores[0], displayInfo: true},
            store: stores[0],
            listeners: {
                afterrender: function(){
                    this.fireEvent('show', this);
                },
                show: function(){
                    this.store.load();
                }
            }
        }, {
            title: '学校开课课程',
            columns: [{
                xtype: 'rownumberer',
                text: '序号',
                width: 50
            }, {
                text: '课程名称',
                dataIndex: 'name',
                width: 200
            }, {
                text: '适用学校类型',
                dataIndex: 'types',
                width: 200,
                renderer: function(v){
                    return v.replace(/,/g, '，');
                }
            }/*, {
                text: '备注',
                dataIndex: 'remark',
                flex: 1
            }*/],
            bbar: {xtype: 'pagingtoolbar', store: stores[1], displayInfo: true},
            store: stores[1],
            listeners: {
                show: function(){
                    this.store.load();
                }
            }
        }, {
            title: '资源来源',
            columns: [{
                text: '资源来源',
                width: 300,
                dataIndex: 'value'
            }, {
                text: '备注',
                dataIndex: 'remark',
                flex: 1
            }],
            bbar: {store: stores[2], xtype: 'pagingtoolbar', displayInfo: true},
            store: stores[2],
            listeners: {
                show: function(){
                    this.store.load();
                }
            }
        }, {
            title: '资源类型',
            columns: [{
                text: '资源类型',
                width: 160,
                dataIndex: 'value'
            }, {
                text: '备注',
                dataIndex: 'remark',
                flex: 1
            }],
            bbar: {store: stores[3], xtype: 'pagingtoolbar', displayInfo: true},
            store: stores[3],
            listeners: {
                show: function(){
                    this.store.load();
                }
            }
        }];
        this.callParent();
    }
});

/* 运维功能 */
/* 终端远程关机重启 */
Ext.define('bbt.MaintainView', {
    extend: 'Ext.view.View',
    alias: 'widget.maintainview',
    style: {paddingBottomWidth: '15px'},
    itemSelector: '.class-item',
    tpl: [
        '<tpl for=".">',
            '<div class="class-item">',
                '<div class="status-icon {cls}"></div>',
                '<div class="class-info" style="text-align:center;">{info}</div>',
            '</div>',
        '</tpl><div style="clear:left;height:15px;"></div>'],
    constructor: function(){
        var store = new Ext.data.Store({
            fields: ['grade_name', 'class_name', 'mac', 'online'],
            filters: [function(item){ return !!item.get('mac'); }],
            proxy: {
                url: '/system/maintenance/list-system/',
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            }
        });
        this.multiSelect = true;
        this.trackOver = true;
        this.overItemCls = 'class-item-hover';
        this.selectedItemCls = "class-item-selected";
        this.store = store;
        //store.load();
        this.callParent();
    },
    initComponent: function(){
        this.listeners = {
            afterrender: function(){
                var el = this.el;
                el.on('mouseover', function(e){
                    var item = Ext.fly(e.target);
                    if(item.hasCls('btn-disabled')) { return; }
                    item.addCls(['x-over', 'x-btn-over', 'x-btn-default-small-over']);
                }, undefined, {delegate: '.ext-btn'});
                el.on('mouseout', function(e){
                    var item = Ext.fly(e.target);
                    if(item.hasCls('btn-disabled')) { return; }
                    item.removeCls(['x-over', 'x-btn-over', 'x-btn-default-small-over']);
                }, undefined, {delegate: '.ext-btn'});
                el.on('click', function(e){
                    var item = Ext.fly(e.target), method;
                    if(item.hasCls('btn-disabled')) { return; }
                    method = e.target.getAttribute('action');
                    Ext.getCmp('content-panel').child('maintainpanel')[method]();
                }, undefined, {delegate: '.ext-btn'});
            },
            selectionchange: function(){
                var view = this,
                    sel = arguments[1],
                    panel = this.up('maintainpanel'),
                    cbox = panel.down('[name=select-all]');
                if(sel.length == view.store.count()) {
                    cbox.setValue(true);
                } else {
                    cbox.setValue(false);
                }
            }
        };
        this.callParent();
    },
    prepareData: function(data, index, record){
        var str, gc, mac, btns;
        if(data.grade_name == "电脑教室") {
            gc = data.class_name;
        } else {
            gc = data.grade_name + "年级" + data.class_name + "班";
        }
        if(gc.length > 6) {
            gc = '<span title="' + gc + '">' + gc.substr(0, 5) + '...</span>';
        } else {
            gc = '<span title="' + gc + '">' + gc + '</span>';
        }
        mac = '<span class="mac">' + data.mac + '</span>';
        btns = '<a href="javascript:void(0);" action="shutdown" class="x-btn x-btn-default-small ext-btn">关机</a> ' +
                '<a href="javascript:void(0);" action="reboot" class="x-btn x-btn-default-small ext-btn">重启</a>';
        if(!data.online) {
            data.cls = "offline"
        }
        data.info = gc + '<br/>' + mac + '<br/>' + btns;
        return data;
    }
});
Ext.define('bbt.MaintainPanel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.maintainpanel',
    initComponent: function(){
        this.tbar = [bbt.ToolBox.get('gradeOld', {fieldLabel: '终端分组', labelWidth:65,width:165, useSuffix: true, computerclass: true}), {
            text: '刷新',
            name: 'refresh',
            iconCls: 'tool-icon icon-refresh'
        }, '-', {
            xtype: 'checkbox',
            name: 'select-all',
            boxLabel: '全选当前终端',
            listeners: {
                change: function(me, v){
                    var view = this.up('maintainpanel').child('maintainview');
                    if(v) {
                        view.selModel.selectAll();
                    } else {
                        view.selModel.deselectAll();
                    }
                }
            }
        }, {
            text: '远程关机',
            name: 'shutdown',
            iconCls: 'icon-shutdown'
        }, {
            text: '远程重启',
            name: 'reboot',
            iconCls: 'icon-reboot'
        }, {
            text: '定时关机设置',
            name: 'delayshutdown',
            iconCls: 'icon-clock'
        }, '->', '注：按住Ctrl键，可同时点选多个终端。'];
        this.autoScroll = true;
        this.items = {xtype: 'maintainview'};
        this.listeners = {
            afterrender: function(){
                var tb = this.child('toolbar[dock=top]');
                tb.down('[name=grade_name]').on('change', this.reloadStore, this);
                tb.down('[name=refresh]').setHandler(this.reloadStore, this);
                tb.down('[name=shutdown]').setHandler(this.shutdown, this);
                tb.down('[name=reboot]').setHandler(this.reboot, this);
                tb.down('[name=delayshutdown]').setHandler(this.delayShutdown, this);
            }
        };
        this.callParent();
    },
    reloadStore: function(){
        var view = this.child('maintainview'), grade;
        grade = this.down('[name=grade_name]').getValue();
        view.store.proxy.extraParams.grade_name = grade;
        view.store.load();
    },
    getSelectedRecords: function(){
        var view = this.child('maintainview');
        return view.selModel.getSelection();
    },
    showDelayShutdown: function(){
        var wc = {
            xtype: 'window',
            title: '定时关机设置',
            resizable: false,
            closable: false,
            modal: true,
            width: 350,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                bodyCls: 'no-bg',
                margin: 30,
                items: [{
                    xtype: 'fieldset',
                    title: '启用定时关机',
                    checkboxToggle: true,
                    defaults: {labelSeparator: '：'},
                    items: [{
                        xtype: 'timefield',
                        fieldLabel: '关机时间',
                        format: 'H:i:s',
                        minValue: '12:00:00',
                        allowBlank: false,
                        name: 'scheduler_shutdown_clock'
                    }, {
                        xtype: 'fieldcontainer',
                        fieldLabel: '延时提醒',
                        defaultType: 'radio',
                        items: [{
                            boxLabel: '20秒',
                            inputValue: '20',
                            checked: true,
                            name: 'scheduler_shutdown_delay'
                        }, {
                            boxLabel: '40秒',
                            inputValue: '40',
                            name: 'scheduler_shutdown_delay'
                        }, {
                            boxLabel: '60秒',
                            inputValue: '60',
                            name: 'scheduler_shutdown_delay'
                        }]
                    }],
                    listeners: {
                        beforecollapse: function(){
                            this.items.each(function(f){
                                f.setDisabled(true);
                            });
                            return false;
                        },
                        beforeexpand: function(){
                            this.items.each(function(f){
                                f.setDisabled(false);
                            });
                            return false;
                        }
                    }
                }, {
                    xtype: 'component',
                    style: {color: 'gray'},
                    html: '注：本设置仅针对已经申报成功的所有学校终端。'
                }]
            }],
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),
                        msg = checkForm(fm), cb;
                    if(msg !== true) { return; }
                    cb = function(_, a){
                        var ret = a.result, msg;
                        if(ret.status !== "success") {
                            msg = ret.msg;
                        }
                        msg && Ext.Msg.alert('提示', msg);
                        win.destroy();
                    };
                    fm.getForm().submit({
                        params: {
                            scheduler_shutdown_switch: fm.down('fieldset').checkboxCmp.getValue() ? "1" : "0"
                        },
                        url: '/system/maintenance/scheduler-shutdown/',
                        success: cb,
                        failure: cb
                    });
                }
            }, {
                text: '取消',
                handler: function(){
                    this.up('window').destroy();
                }
            }],
            buttonAlign: 'center'
        }, win, cb;
        win = Ext.widget(wc);
        win.show();
        win.setLoading(true);
        Ext.Ajax.request({
            url: '/system/maintenance/scheduler-shutdown/get/',
            method: 'GET',
            callback: function(_1, _2, resp){
                var data, fs, k, f;
                win.setLoading(false);
                data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    data = data.data;
                    fs = win.down('fieldset');
                    if(data.scheduler_shutdown_switch) {
                        fs.down('[inputValue=' + data.scheduler_shutdown_delay + ']').setValue(true);
                        fs.down('timefield').setValue(data.scheduler_shutdown_clock);
                        fs.checkboxCmp.setValue(data.scheduler_shutdown_switch === "1");
                    } else {
                        fs.checkboxCmp.setValue(false);
                    }
                }
            }
        });
    },
    delayShutdown: function(){
        this.showDelayShutdown();
    },
    shutdown: function(){
        var rcs = this.getSelectedRecords();
        if(!rcs.length) { return; }
        rcs = Ext.Array.filter(rcs, function(rc){
            return !!rc.get('mac');
        });
        if(!rcs.length) { return; }
        this.confirm('提示', '确定要对 ' + rcs.length + ' 台终端执行<span style="color:red;">关机</span>操作吗？', function(b, delay){
            (b == 'yes') && Ext.Ajax.request({
                url: '/system/maintenance/run-shutdown/',
                params: {
                    mac: Ext.Array.map(rcs, function(rc){ return rc.get('mac'); }),
                    delay: delay
                },
                method: 'POST',
                callback: function(_1, _2, resp){ }
            });
        });
    },
    reboot: function(){
        var rcs = this.getSelectedRecords();
        if(!rcs.length) { return; }
        rcs = Ext.Array.filter(rcs, function(rc){
            return !!rc.get('mac');
        });
        if(!rcs.length) { return; }
        this.confirm('提示', '确定要对 ' + rcs.length + ' 台终端执行<span style="color:red;">重启</span>操作吗？', function(b, delay){
            (b == 'yes') && Ext.Ajax.request({
                url: '/system/maintenance/run-reboot/',
                params: {
                    mac: Ext.Array.map(rcs, function(rc){ return rc.get('mac'); }),
                    delay: delay
                },
                method: 'POST',
                callback: function(_1, _2, resp){ }
            });
        });
        
    },
    confirm: function(title, msg, cb){
        Ext.widget({
            xtype:'window',
            title: title,
            modal: true,
            resizable: false,
            closable: false,
            layout: 'fit',
            items: [{
                xtype: 'container',
                layout: {type: 'vbox'},
                items: [{
                    xtype: 'combo',
                    editable: false,
                    margin: '30 30 0 30',
                    value: '30',
                    fieldLabel: '执行模式',
                    store: [['0', '立即执行'], ['30', '倒计时执行']]
                }, {
                    xtype: 'component',
                    html: '<p style="font-size: 16px;">' + msg + '</p>',
                    border: false,
                    margin: '10 30 30 30'
                }]
            }],
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window');
                    win.whichButton = 'yes';
                    win.destroy();
                }
            }, {
                text: '取消',
                handler: function(){
                    var win = this.up('window');
                    win.whichButton = 'no';
                    win.destroy();
                }
            }],
            buttonAlign: 'center',
            listeners: {
                beforedestroy: function(){
                    cb(this.whichButton, this.down('combo').getValue());
                }
            }
        }).show();
    }
});
/* 远程协助 */
Ext.define('bbt.RemoteHelpView', {
    extend: 'Ext.view.View',
    alias: 'widget.remotehelpview',
    style: {paddingBottomWidth: '15px'},
    itemSelector: '.class-item',
    tpl: [
        '<tpl for=".">',
            '<div class="class-item">',
                '<div class="status-icon {cls}"></div>',
                '<div class="class-info" style="text-align:center;">{info}</div>',
                '<a class="over-btn viewer">远程查看</a>',
                '<a class="over-btn controller">远程协助</a>',
            '</div>',
        '</tpl><div style="clear:left;height:15px;"></div>'],
    constructor: function(){
        var store = new Ext.data.Store({
            fields: ['grade_name', 'class_name', 'mac', 'online', 'inclass', 'token', 'ip', 'lesson_name', 'teacher'],
            proxy: {
                url: '/system/maintenance/list-vnc/',
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            }
        });
        this.store = store;
        store.load();
        this.listeners = {
            afterrender: function(){
                var el = this.el;
                el.on('mousemove', function(e, item){
                    var x = e.getX(),
                        item = Ext.fly(item),
                        viewer = item.child('.viewer'),
                        controller = item.child('.controller');

                    if((x - item.getLeft()) >= item.getWidth()/2) {
                        if(viewer.getStyle('left') != "-50%") {
                            viewer.setStyle('left', '-50%');
                        }
                        if(controller.getStyle('right') != "0") {
                            controller.setStyle('right', 0);
                        }
                    } else {
                        if(controller.getStyle('right') != "-50%") {
                            controller.setStyle('right', '-50%');
                        }
                        if(viewer.getStyle('left') != "0") {
                            viewer.setStyle('left', 0);
                        }
                    }
                }, undefined, {delegate: '.class-item'});
                el.on('mouseout', function(e, item){
                    item = Ext.fly(item);
                    item.child('.viewer').setStyle('left', '-50%');
                    item.child('.controller').setStyle('right', '-50%');
                }, undefined, {delegate: '.class-item'})
            },
            itemclick: function(){
                var e = arguments[4],
                    rc = arguments[1],
                    target = e.target,
                    vncUrl, url,
                    platform, viewonly, title;
                if(target.className.indexOf('over-btn') === -1) { return; }
                try {
                    platform = rc.store.proxy.reader.rawData.data.platform_system;
                } catch(e) {
                    platform = "win";
                }
                if(platform == "win") {
                    vncUrl = location.href.split(':');
                    vncUrl = vncUrl[0] + ':' + vncUrl[1] + ':6081';
                    if(target.className.indexOf('viewer') != -1) {
                        url = vncUrl + "/?view_only=true&token=" + rc.get('token');
                        viewonly = true;
                    } else if(target.className.indexOf('controller') != -1) {
                        url = vncUrl + "/?view_only=false&token=" + rc.get('token');
                        viewonly = false;
                    }
                } else {
                    if(target.className.indexOf('viewer') != -1) {
                        url = "/system/maintenance/run-vnc/?view_only=true&token=" + rc.get('token');
                        viewonly = true;
                    } else if(target.className.indexOf('controller') != -1) {
                        url = "/system/maintenance/run-vnc/?view_only=false&token=" + rc.get('token');
                        viewonly = false;
                    }
                }
                
                if(url) {
                    if(rc.get('grade_name') == "电脑教室") {
                        title = ": " + rc.get('class_name');
                    } else if(rc.get('grade_name') && rc.get('class_name')) {
                        title = ": " + rc.get('grade_name') + "年级" + rc.get('class_name') + "班";
                    } else {
                        title = "";
                    }
                    this.up('remotehelppanel').openVNC(url, "正在" + (viewonly?"远程查看":"远程协助") + title);
                }
            }
        };
        this.showAll(false);
        this.callParent();
    },
    prepareData: function(data, index, record){
        var gc, status, lesson;
        if(data.inclass) {
            status = "<b>登录上课中</b>";
        } else {
            status = "<b>未登录</b>";
        }
        if(data.grade_name == "电脑教室") {
            gc = data.class_name;
        } else if(data.grade_name && data.class_name) {
            gc = data.grade_name + "年级" + data.class_name + "班";
        } else {
            gc = "未申报";
            status = data.ip;
        }
        if(gc.length > 6) {
            gc = '<span title="' + gc + '">' + gc.substr(0, 5) + '...</span>';
        } else {
            gc = '<span title="' + gc + '">' + gc + '</span>';
        }
        lesson = '<b>' + (data.lesson_name || "") + '</b>' +
                ' <b>' + (data.teacher || "") + '</b>';
        
        !data.online && (data.cls = "offline");
        data.info = gc + '<br/>' + status + '<br/>' + lesson;
        return data;
    },
    showAll: function(all){
        if(all === true) {
            this.store.clearFilter(all);
        } else {
            this.store.filter({
                filterFn: function(item){
                    return item.get('online');
                }
            });
        }
    }
});
Ext.define('bbt.RemoteHelpPanel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.remotehelppanel',
    initComponent: function(){
        this.tbar = [bbt.ToolBox.get('gradeOld', {fieldLabel: '终端分组', labelWidth:65,width:165, useSuffix: true, computerclass: true}), {
            text: '刷新',
            name: 'refresh',
            iconCls: 'tool-icon icon-refresh'
        }, '-', {
            xtype: 'checkbox',
            name: 'show-all',
            boxLabel: '显示全部',
            listeners: {
                change: function(_, v){
                    var p = this.up('remotehelppanel'), view;
                    view = p.child('remotehelpview');
                    view.showAll(v);
                    view.store.reload();
                }
            }
        }];
        this.autoScroll = true;
        this.items = {xtype: 'remotehelpview'};
        this.listeners = {
            afterrender: function(){
                var tb = this.child('toolbar[dock=top]');
                tb.down('[name=grade_name]').on('change',this.reloadStore,this);
                tb.down('[name=refresh]').setHandler(this.reloadStore, this);
            }
        };
        this.callParent();
    },
    reloadStore: function(){
        var view = this.child('remotehelpview');
        grade = this.down('[name=grade_name]').getValue();
        view.store.proxy.extraParams.grade_name = grade;
        view.store.load();
    },
    openVNC: function(url, title){
        var winc = {
            width: 800,
            height: 600,
            xtype: 'window',
            title: title,
            modal: true,
            maximizable: true,
            layout: 'fit',
            html: '<iframe id="vncFrame" onload="vncFrame.focus();" width="100%" height="100%" frameborder="0" src="' + url + '"></iframe>',
            listeners: {
                beforeclose: function(){
                    var me = this, fw;
                    me.hide();
                    try {
                        fw = me.getEl().down('iframe', true).contentWindow;
                        fw.postMessage("disconnect", "*");
                    } catch(e) {
                        console.log("close vnc panel error: ", e);
                    } finally {
                        setTimeout(function(){me.destroy();}, 100);
                    }
                    return false;
                }
            }
        }, w;
        w = Ext.widget(winc).show();
        (title.indexOf('远程协助') > -1) && w.getEl().down('.x-window-header-text-default').setStyle('color', '#FF0000');
    }
});
/* 电子公告 */
Ext.define('bbt.NoticeWindow', {
    extend: 'Ext.window.Window',
    alias: 'widget.noticewindow',
    modal: true,
    draggable: false,
    resizable: false,
    closable: false,
    initComponent: function(){
        this.width = 700;
        this.height = 500;
        this.layout = 'fit';
        this.items = [{
            xtype: 'form',
            bodyCls: 'no-bg',
            margin: 30,
            layout: 'anchor',
            border: false,
            defaults: {anchor: '100%', margin: '0 0 10 0'},
            items: [{
                xtype: 'checkbox',
                boxLabel: '启用校园电子公告',
                name: 'active',
                listeners: {
                    change: function(me, v){
                        var p = me.ownerCt;
                        if(!v) {
                            Ext.Msg.confirm('提示', '不启用校园电子公告将清空现有公告数据，确定要继续吗？', function(b){
                                if(b == "yes") {
                                    p.down('[name=title]').setValue('').setDisabled(true);
                                    p.down('[name=content]').setValue('').setDisabled(true);
                                } else {
                                    me.setValue(true);
                                }
                            });
                        } else {
                            p.down('[name=title]').setDisabled(false);
                            p.down('[name=content]').setDisabled(false);
                        }
                        
                    }
                }
            }, {
                xtype: 'textfield',
                name: 'title',
                fieldLabel: '公告标题',
                labelWidth: 65,
                maxLength: 25,
                allowBlank: false,
                disabled: true
            }, {
                xtype: 'htmleditor',
                name: 'content',
                fieldLabel: '详细内容',
                margin: 0,
                height: 310,
                enableFont: false,
                enableLinks: false,
                enableSourceEdit: false,
                columnWidth: 100,
                labelWidth: 65,
                allowBlank: false,
                disabled: true
            }]
        }];
        this.buttonAlign = 'center';
        this.buttons = [{
            text: '确定',
            handler: function(){
                this.up('window').sendNotice();
            }
        }, {
            text: '取消',
            handler: function(){
                this.up('window').destroy();
            }
        }];
        this.listeners = {
            show: function(){
                var me = this;
                Ext.Ajax.request({
                    url: '/system/maintenance/school-post/list/',
                    method: 'GET',
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText);
                        if(data.status == "success") {
                            data = data.data[0];
                            me.down('form').getForm().setValues(data);
                        }
                        me.setLoading(false);
                    }
                });
                me.setLoading(true);
            }
        };
        this.callParent();
        this.show();
    },
    sendNotice: function(){
        var me = this, fm = me.down('form').getForm(), active;
        if(!fm.isValid()) { return; }
        fm.submit({
            url: '/system/maintenance/school-post/add/',
            success: function(f, a){
                var data = a.result;
                if(data.status != "success") {
                    Ext.Msg.alert('提示', data.msg);
                }
                me.destroy();
            },
            failure: function(f, a){
                Ext.Msg.alert('提示', a.result.msg||'添加校园电子公告失败！');
                me.destroy();
            }
        });
    }
});
}//校级定义结束
else {

/* 学年学期管理 */
Ext.define('bbt.Term', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.term2',
    types: ['春季学期', '秋季学期'],
    fields: ['uuid', 'school_year', 'term_type', 'start_date', 'end_date', 'schedule_time', 'deleted'],
    sorters: [{property: 'school_year', direction: 'DESC'}, {property: 'term_type', direction: 'DESC'}],
    columns: [{
        text: '学年',
        dataIndex: 'school_year',
        width: 200
    }, {
        text: '学期类型',
        dataIndex: 'term_type',
        width: 120
    }, {
        text: '开始时间',
        dataIndex: 'start_date',
        width: 150,
        renderer: bbt.utils.strftime
    }, {
        text: '结束时间',
        dataIndex: 'end_date',
        width: 150,
        renderer: bbt.utils.strftime
    }, {
        text: '计划达标课时/班级',
        dataIndex: 'schedule_time',
        width: 120
    }, {
        text: '状态',
        dataIndex: 'deleted',
        renderer: function(v){
            return v ? "已结转" : "正常";
        }
    }],
    showOperateColumn: true,
    tbar: [{
        text: '添加学期',
        action: 'add',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '编辑学期',
        action: 'edit',
        iconCls: 'tool-icon icon-edit'
    }/*, {
        xtype: 'form',
        bodyCls: 'no-bg',
        border: false,
        items: [{
            xtype : 'fileuploadfield',
            name : 'excel',
            buttonOnly : true,
            margin : 0,
            padding : 0,
            buttonConfig : {text : '导入', iconCls: 'icon-import'},
            listeners: {
                change: function(f, path){
                    var grid = f.up('term');
                    if(!/\.xlsx?$/.test(path)) {
                        //Ext.Msg.alert('提示', '请选择 excel 文件！');
                        f.reset();
                        return;
                    }
                    f.up('form').submit({
                        url: grid.importUrl,
                        success: function(form, a){ f.reset(); grid.store.load(); },
                        failure: function(){ f.reset(); }
                    });
                }
            }
        }]
    }*/],
    importUrl: '/system/newterm/import/',
    listUrl: '/system/newterm/list/',
    addUrl: '/system/newterm/add/',
    removeUrl: '/system/newterm/delete/',
    updateUrl: '/system/newterm/edit/',
    actionMap: {
        add: 'addTerm',
        edit: 'updateTerm',
        remove: 'removeTerm',
        gonext: 'gonext',
        associate: 'associate'
    },
    listeners: {
        edit: function(_, e){ e.record.commit(); },
        show: function(p){ p.store.load(); }
    },
    operates: {/*remove: '删除', */gonext: '学期结转', associate: '关联教材大纲'},
    pagination: true,
    operateRenderer: function(){
        var me = this, code = '<a href="javascript:void(0);" action="associate">关联教材大纲</a>';
        return function(v, m, r){
            var start = Ext.Date.parse(r.get('start_date'), 'Y-m-d'),
                end = Ext.Date.parse(r.get('end_date'), 'Y-m-d'),
                now = new Date();
            now.setHours(0, 0, 0, 0);
            if(r.raw.deleted) {
                return '';
            }
            if(now > end) {
                r.raw.editable = false;
                return me.getOperateFn()();
            }
            return code;
        };

    },
    associate: function(v, rc){
        var uuid = rc.get('uuid');
        this.bubble(function(cmp){
            var layout = cmp.getLayout();
            if(layout.isLayout && layout.setActiveItem) {
                layout.setActiveItem(1).term_uuid = uuid;
                return false;
            }
        });
    },
    addTerm: function(){
        var me = this, config, win;
        config = Ext.apply(me.getTermWindowConfig(), {
            title: '添加学期',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'), vmsg, maskId;
                    vmsg = me.checkForm(fm);
                    if(vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    fm.getForm().findField('school_year').setValue(fm.down('[fakeName=start_year]').getValue() + '-' + fm.down('[fakeName=end_year]').getValue());
                    if(me.addUrl) {
                        me.request(me.addUrl, {form: fm}, {
                            success: function(data){
                                me.store.reload();
                                win.destroy();
                            },
                            failure: function(){
                                console.log('[beer]:', arguments);
                            },
                            maskId: me.createMask(win, '正在添加学期')
                        });
                    } else {
                        me.store.add(fm.getForm().getFieldValues());
                        win.destroy();
                    }

                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.show();
    },
    removeTerm: function(){
        var me = this, term, select, passCB;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择学期！');
            return;
        }
        term = select[0];

        passCB = function(){
            me.request(me.removeUrl, {uuid: term.get('uuid')}, {
                success: function(){
                    me.store.reload();
                },
                maskId: me.createMask(this, '正在删除学期')
            });
        };
        Ext.Msg.confirm('提示', '删除学期将将会影响到作息时间，班级授课教师，统计分析等，确认要继续吗？', function(b){
            b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
        });
    },
    updateTerm: function(){
        var me = this, config, win, term, select, sy, fm, i, rc, date;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择学期！');
            return;
        }
        term = select[0];
        if(term.raw.editable === false) {
            Ext.Msg.alert('提示', '学期已经过了，不能编辑！');
            return;
        }
        config = Ext.apply(me.getTermWindowConfig(), {
            title: '编辑学期',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'), vmsg;
                    vmsg = me.checkForm(fm);
                    if(vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    fm.getForm().findField('school_year').setValue(fm.down('[fakeName=start_year]').getValue() + '-' + fm.down('[fakeName=end_year]').getValue());
                    if(me.updateUrl) {
                        me.request(me.updateUrl, {uuid:term.get('uuid'),form:fm}, {
                            form: fm,
                            maskId: me.createMask(win, '正在修改学期'),
                            success: function(data){
                                term.set(data.data);
                                term.commit();
                                win.destroy();
                            }
                        });
                    } else {
                        term.set(fm.getForm().getFieldValues());
                        term.commit();
                        win.destroy();
                    }

                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        sy = term.get('school_year').split('-');
        win = Ext.create('Ext.window.Window', config);
        win.show();
        /*i = me.store.indexOf(term);
        if(i !== 0) {
            rc = me.store.getAt(i-1);
            date = bbt.utils.toDate(rc.get('start_date'));
            date && win.down('[name=end_date]').setMaxValue(date);
        }
        if(i + 1 !== me.store.count()) {
            rc = me.store.getAt(i+1);
            date = bbt.utils.toDate(rc.get('end_date'));
            date && win.down('[name=start_date]').setMinValue(date);
        }*/
        fm = win.down('form').getForm();
        fm.getFields().each(function(f){
            if(f.name == "end_date" || f.name == "schedule_time") { return; }
            if(f.fakeName == "end_year") {
                f.setValue(sy[1]);
                return;
            }
            if(f.fakeName == "start_year") {
                f.setValue(sy[0]);
            }
            f.setReadOnly(true);
        });
        fm.setValues(term.data);
    },
    _go_next: function(rc){
        var me = this;
        this.request('/system/newterm/finish/', {uuid: rc.get('uuid')}, {
            success: function(){
                me.store.reload();
            }
        });
    },
    gonext: function(){
        var me = this, term, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择一行！');
            return;
        }
        term = select[0];

        Ext.Msg.confirm('提示', '该学期真的结束了吗？<br/>学期结转后，将清除下辖各学校服务器中该学期对应的｛学校作息时间｝、｛年级班级｝、｛班级课程表｝和｛班级课程授课老师｝信息，请问是否继续结转并开始新的学期？', function(b){
            b == 'yes' && new bbt.DangerOperate({onPass: function(){ me._go_next(term); }}).show();
        });
    },
    prepareNextTerm: function(){},
    getTermWindowConfig: function(){
        var cy = new Date().getFullYear(), i = cy - 4, len = cy + 5, ys = [];
        for(;i<=len;i++) {
            ys.push([i, i+'']);
        }
        var config = {
            closable: false,
            resizable: false,
            width: 322,
            modal: true,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls: 'no-bg',
                border: false,
                layout: 'anchor',
                padding: 20,
                defaults: {labelWidth: 120, anchor: '100%', allowBlank: false},
                items: [{
                    xtype: 'combo',
                    fakeName: 'start_year',
                    fieldLabel: '开始学年',
                    editable: false,
                    value: cy,
                    store: ys,
                    listeners: {
                        change: function(me, v){
                            var ed = me.up('form').down('textfield[fakeName=end_year]');
                            ed.setValue(v + 1 + '');
                        }
                    }
                }, {
                    xtype: 'textfield',
                    fakeName: 'end_year',
                    value: cy + 1 + '',
                    fieldLabel: '结束学年',
                    readOnly: true
                }, {
                    xtype: 'combo',
                    name: 'term_type',
                    store: this.types,
                    value: '春季学期',
                    editable: false,
                    fieldLabel: '学年类型'
                }, {
                    xtype: 'datefield',
                    name: 'start_date',
                    editable: false,
                    margin: '10 0',
                    fieldLabel: '开始时间',
                    format: 'Y-m-d',
                    validator: function(v){
                        var me = this, sv = me.getValue(), end, ev;
                        end = me.up('form').down('datefield[name=end_date]');
                        ev = end.getValue();
                        if(sv && ev && sv > ev) {
                            return('开始时间不能大于结束时间！');
                        }
                        return true;
                    }
                }, {
                    xtype: 'datefield',
                    editable: false,
                    name: 'end_date',
                    fieldLabel: '结束时间',
                    format: 'Y-m-d',
                    validator: function(v) {
                        var me = this, ev = me.getValue(), start, sv;
                        start = me.up('form').down('datefield[name=end_date]');
                        sv = start.getValue();
                        if(sv && ev && sv > ev) {
                            return('开始时间不能大于结束时间！');
                        }
                        return true;
                    },
                    listeners: {
                        change: function(me){
                            me.up('form').down('datefield[name=start_date]').validate();
                        }
                    }
                }, {
                    xtype: 'textfield',
                    fieldLabel: '计划达标课时/班级',
                    name: 'schedule_time',
                    validator: function(v){
                        var msg = '无效的数字';
                        if(!/^[1-9]\d*$/.test(v)) {
                            return msg;
                        }
                        v = parseInt(v);
                        if(!isNaN(v)) {
                            return v <= 2147483647 ? true : msg;
                        }
                        return msg;
                    }
                }, {
                    xtype: 'hidden',
                    name: 'school_year'
                }]
            }],
            buttonAlign: 'right'
        };
        return config;
    }
});
/* 学期关联教材大纲 */
Ext.define('bbt.CourseOutline', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.courseoutline',
    initComponent: function(){
        this.layout = "border";
        this.bodyCls = "no-bg";
        this.tbar = [{text: '<< 返回', action: 'returnTerm'}/*, {text: '设置', action: 'enableSetting'}*/];
        this.items = [{
            xtype: 'panel',
            header: false,
            border: false,
            layout: 'anchor',//{type:'vbox', align: 'stretch'},
            defaults: {anchor: '100%'},
            bodyStyle: {background: 'url(/public/images/borderbg.png) repeat-y right'},
            region: 'west',
            width: 140,
            items: [{
                xtype: 'boundlist',
                displayField: 'grade_name',
                valueField: 'value',
                style: {borderRight: '1px solid #99bce8 !important'},
                itemCls: 'grade-item',
                tpl:  '<ul style="background-color:#cbdaf0;"><tpl for="."><li role="option" class="grade-item"><a class="editor"></a>{grade_name}</li></tpl></ul><div role="line" style="position:absolute;height:31px;display:none;width:0px;border-right:1px solid #FFF;"></div>',
                store: new Ext.data.Store({
                    data: [{"value":"一","grade_name":"一年级（小学）"},{"value":"二","grade_name":"二年级（小学）"},{"value":"三","grade_name":"三年级（小学）"},{"value":"四","grade_name":"四年级（小学）"},{"value":"五","grade_name":"五年级（小学）"},{"value":"六","grade_name":"六年级（小学）"},{"value":"七","grade_name":"七年级（初中）"},{"value":"八","grade_name":"八年级（初中）"},{"value":"九","grade_name":"九年级（初中）"},{"value":"十","grade_name":"十年级（高中）"},{"value":"十一","grade_name":"十一年级（高中）"},{"value":"十二","grade_name":"十二年级（高中）"}],
                    fields: ['grade_name', 'value', 'in_use']
                })
            }]
        }, {
            xtype: 'tabpanel',
            layout: 'fit',
            margin: 10,
            region: 'center',
            items: [{
                xtype: 'panel',
                action: 'addCourse',
                title: '+'
            }],
            updateCourseList: function(rc){
                var me = this, p = me.ownerCt, mask = new Ext.LoadMask(p, {msg: 'loading...'});
                mask.show();
                Ext.Ajax.request({
                    url: '/system/term/syllabus/lesson-list/',
                    method: 'GET',
                    params: {grade_name: rc.get('value'), term_uuid: p.term_uuid},
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText);
                        if(data.status == "success") {
                            p.RESOURCE_PLATFORM_HOST = data.data.RESOURCE_PLATFORM_HOST;
                            Ext.each(data.data.records, function(item){
                                me.insert(0, {xtype: 'courseoutlineinfo', rawData: item});
                            });
                            me.setActiveTab(0);
                        }
                        mask.hide();
                        mask.destroy();
                    }
                });
                me.items.each(function(tab){
                    if(tab.action != 'addCourse') {
                        me.remove(tab, true);
                    }
                });
            }
        }];
        this.listeners = {
            afterrender: function(){
                var me = this, tab = me.child('tabpanel'), list;
                me.down('toolbar[dock=top]').down('[action=returnTerm]').setHandler(me.returnTerm, me);
                //me.down('toolbar[dock=top]').down('[action=enableSetting]').setHandler(me.enableSetting, me);
                list = me.down('boundlist');
                list.store.on('load', function(s, rcs){
                    var rc;
                    if(s.count() > 0) {
                        rc = s.getAt(0);
                        this.getSelectionModel().select(rc);
                    }
                }, list);
                list.on('itemclick', function(v, rc, el){
                    var e = arguments[4], target = e.target, tabpanel, checked;
                    if(target.className != "editor") { return; }
                    checked = !target.getAttribute('data-clicked');
                    tabpanel = this.ownerCt.ownerCt.down('tabpanel');
                    Ext.each(tabpanel.query('tab'), function(t){
                        if(t.text != '+'){
                            t.setClosable(checked);
                            if(!t.closeCallback) {
                                t.closeCallback = function(){
                                    var me = this, realClose;
                                    realClose = function(){
                                        Ext.Ajax.request({
                                            url: '/system/term/syllabus/lesson-del/',
                                            method: 'POST',
                                            params: {id: me.card.rawData.id},
                                            callback: function(_1, _2, resp){
                                                var data = Ext.decode(resp.responseText);
                                                if(data.status == "success") {
                                                    me.up('tabpanel').remove(me.card);
                                                } else {
                                                    Ext.Msg.alert('提示', data.msg);
                                                }
                                            }
                                        });
                                    };
                                    Ext.Msg.confirm('提示', '确定要删除课程 ' + me.text + ' 吗？', function(b){
                                        if(b == 'yes') {
                                            new bbt.DangerOperate({onPass: realClose}).show();
                                        }
                                    });
                                    return false;
                                };
                            }
                            if(checked) {
                                t.on('beforeclose', t.closeCallback);
                            } else {
                                t.un('beforeclose', t.closeCallback);
                            }
                        }
                    });
                    if(checked) {
                        target.setAttribute('data-clicked', true);
                        target.style.backgroundColor = "#D3E1F1";
                    } else {
                        target.removeAttribute('data-clicked');
                        target.style.backgroundColor = "#FFF";
                    }
                });
                list.on('select', function(_, rc){
                    var xy, el, line;
                    this.ownerCt.ownerCt.down('tabpanel').updateCourseList(rc);
                    el = this.getNode(rc);
                    xy = Ext.fly(el).getOffsetsTo(this.el);
                    line = this.getEl().down('[role=line]');
                    line.setStyle({left: xy[0]+Ext.fly(el).getWidth()+'px', top: xy[1]-1+'px'});
                    line.show();
                }, list);
                tab.down('tab').on('click', function(b, e){
                    this.addCourse();
                    return false;
                }, me);
                tab.on('tabchange', function(me, n, o){
                    if(n === o) { return; }
                    if(me.is_from_zy) {
                        delete me.is_from_zy;
                        return;
                    }
                    if(n.action == 'addCourse') {
                        me.is_from_zy = true;
                        me.setActiveTab(o);
                    }
                });
            },
            show: function(){
                var me = this, list = me.down('boundlist');
                setTimeout(function(){
                    list.store.load({params: {uuid: me.term_uuid}}, 50);
                });
            }
        };
        this.callParent();
    },
    enableSetting: function(){
        var winc = {
            xtype: 'window',
            title: '同步设置',
            modal: true,
            __parent: this,
            closable: false,
            resizable: false,
            layout: 'fit',
            width: 350,
            minHeight: 210,
            items: [{
                xtype: 'grid',
                border: false,
                columns: [{
                    text: '年级',
                    dataIndex: 'grade_name',
                    flex: 1
                }, {
                    text: '状态',
                    dataIndex: 'in_use',
                    renderer: function(v){
                        return v ? "已启用" : "未启用";
                    },
                    flex: 1
                }, {
                    text: '操作',
                    dataIndex: 'xxx',
                    renderer: function(v,m,r){
                        if(!r.get('in_use')) {
                            return '<a href="javascript:void(0);" action="enable">启用</a>';
                        }
                        return '';
                    },
                    flex: 1
                }],
                store: this.down('boundlist').store,
                listeners: {
                    itemclick: function(me, rc, el, i, e){
                        try {
                            if(e.target.getAttribute('action') == "enable") {
                                this.enableGrade(rc);
                            }
                        } catch(e) {}
                    }
                },
                enableGrade: function(model){
                    if(!model) { return; }
                    var term_uuid = this.up('window').__parent.term_uuid,
                        passCB = function(){
                        Ext.Ajax.request({
                            method: 'POST',
                            url: '/system/term/syllabus/grade-enable/',
                            params: {grade_name: model.get('value'), term_uuid: term_uuid},
                            callback: function(opts, _, resp){
                                var data = Ext.decode(resp.responseText);
                                if(data.status == "success") {
                                    model.set('in_use', true);
                                    model.commit();
                                }
                            }
                        });
                    };
                    Ext.Msg.confirm('提示', '该年级执行启用操作后，下辖学校的本年级将使用当前各课程的教材大纲标题，作为教学内容进行选择。此操作将不可逆转，是否继续？', function(btn){
                        (btn == 'yes') && new bbt.DangerOperate({onPass: passCB}).show();
                    });
                }
            }],
            buttons: [{
                text: '关闭',
                handler: function(){
                    this.up('window').destroy();
                }
            }],
            buttonAlign: 'right',
            listeners: {
                afterrender: function(){
                    var grid = this.down('grid');
                    Ext.Ajax.request({
                        url: '/system/term/syllabus/grade-set/',
                        method: 'GET',
                        params: {term_uuid: this.__parent.term_uuid},
                        callback: function(_1, _2, resp){
                            var data = Ext.decode(resp.responseText), usemap = {};
                            if(data.status != "success") { return; }
                            data = data.data.records;
                            Ext.each(data, function(g){
                                usemap[g.grade_name] = g.in_use;
                            });
                            grid.store.each(function(rc){
                                var v = rc.get('value');
                                if(v in usemap) {
                                    rc.set('in_use', usemap[v]);
                                    rc.commit();
                                }
                            });
                        }
                    });
                }
            }
        };
        Ext.widget(winc).show();
    },
    returnTerm: function(){
        this.bubble(function(cmp){
            var layout = cmp.getLayout();
            if(layout.isLayout && layout.setActiveItem) {
                layout.setActiveItem(0);
                return false;
            }
        });
    },
    getSelectGrade: function(){
        var grade = this.down('boundlist').getSelectionModel().getSelection();
        if(grade.length) {
            grade = grade[0];
            return grade;
        } else {
            return null;
        }
    },
    reloadGrade: function(_, action){
        var data = action.result, store;
        if(data.status == "success") {
            store = this.down('boundlist').store;
            store.reload();
        } else {
            Ext.Msg.alert('提示', getErrorMsg(data));
        }
    },
    addKlass: function(){
        var gradeData = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"];
        gradeData = Ext.Array.map(gradeData, function(g){
            return {text:bbt.fullgrade(g), value:g};
        });
        var winc = {
            xtype: 'window',
            title: '添加年级',
            __parent: this,
            modal: true,
            closable: false,
            resizable: false,
            width: 300,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls: 'no-bg',
                border: false,
                layout: 'anchor',
                items: [{
                    xtype: 'combo',
                    margin: 20,
                    name: 'grade_name',
                    editable: false,
                    allowBlank: false,
                    displayField: 'text',
                    valueField: 'value',
                    queryMode: 'local',
                    fieldLabel: '年级',
                    store: new Ext.data.Store({fields:['text','value'],data:gradeData})
                }]
            }],
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form').getForm(),
                        values = win.down('form').getForm().getValues(), tabpanel, index;
                    if(!fm.isValid()) { return; }
                    fm.submit({
                        url: '/system/term/syllabus/grade-add/',
                        params: {uuid: win.__parent.term_uuid},
                        success: win.__parent.reloadGrade,
                        failure: function(_, action){
                            console.log(arguments);
                        },
                        scope: win.__parent
                    });
                    win.destroy();
                }
            }, {
                text: '关闭',
                handler: function(){
                    this.up('window').destroy();
                }
            }],
            buttonAlign: 'right'
        };
        Ext.widget(winc).show();
    },
    addCourse: function(){
        var grade = this.getSelectGrade(), winc, tuid = this.term_uuid, remoteHost = this.RESOURCE_PLATFORM_HOST;
        winc = {
            xtype: 'window',
            title: '添加课程',
            __parent: this,
            modal: true,
            closable: false,
            resizable: false,
            width: 400,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                margin: 30,
                layout: 'anchor',
                bodyCls: 'no-bg',
                defaults: {anchor: '100%', allowBlank: false},
                items: [{
                    xtype: 'hidden',
                    name: 'syllabus_grade',
                    value: grade ? grade.get('value') : ''
                }, {
                    xtype: 'combo',
                    name: 'lesson_name',
                    editable: false,
                    fieldLabel: '课程',
                    displayField: 'lessonname__name',
                    valueField: 'lessonname__name',
                    store: new Ext.data.Store({
                        fields: ['uuid', 'lessonname__name'],
                        proxy: {
                            url: remoteHost + '/view/api/lessonname/list/',
                            type: 'jsonp',
                            reader: {
                                type: 'json',
                                root: 'data.records'
                            }
                        },
                        pageSize: 1000,
                        listeners: {
                            beforeload: function(){
                                var grade = this.owner.ownerCt.down('[name=syllabus_grade]').getValue();
                                this.proxy.extraParams.grade_name = grade;
                            }
                        }
                    }),
                    listeners: {
                        afterrender: function(){
                            this.store.owner = this;
                        },
                        change: function(me, v){
                            var publish = me.ownerCt.down('[name=publish]');
                            publish.setValue(undefined);
                            if(publish.is_store_loaded) {
                                publish.store.load();
                            }
                        }
                    }
                }, {
                    xtype: 'combo',
                    name: 'publish',
                    editable: false,
                    displayField: 'name',
                    valueField: 'name',
                    fieldLabel: '出版社',
                    maxLength: 100,
                    store: new Ext.data.Store({
                        fields: ['name'],
                        proxy: {
                            url: remoteHost + '/view/api/publish/list-by-lessonname/',
                            type: 'jsonp',
                            reader: {
                                type: 'json',
                                root: 'data.records'
                            }
                        },
                        listeners: {
                            beforeload: function(){
                                var name = this.owner.ownerCt.down('[name=lesson_name]').getValue(),
                                    grade = this.owner.up('window').__parent.getSelectGrade().get('value');
                                this.owner.is_store_loaded = true;
                                if(name) {
                                    this.proxy.extraParams.lessonname = name;
                                    this.proxy.extraParams.grade_name = grade;
                                } else {
                                    return false;
                                }
                            }
                        }
                    }),
                    listeners: {
                        afterrender: function(){
                            this.store.owner = this;
                        },
                        change: function(me, v){
                            var date = me.ownerCt.down('[name=date]');
                            date.setValue(undefined);
                            if(date.is_store_loaded) {
                                date.store.load();
                            }
                        }
                    }
                }, {
                    xtype: 'combo',
                    name: 'date',
                    editable: false,
                    displayField: 'text',
                    valueField: 'value',
                    fieldLabel: '出版日期',
                    maxLength: 100,
                    store: new Ext.data.Store({
                        fields: ['year', 'month', 'number', 'remark', 'cover_pic', 'version_pic'],
                        proxy: {
                            url: remoteHost + '/view/api/bookversion/list-by-something/',
                            type: 'jsonp',
                            reader: {
                                type: 'json',
                                root: 'data.records'
                            },
                            pageParam: undefined
                        },
                        listeners: {
                            beforeload: function(){
                                var p = this.owner.ownerCt, params = {};
                                params.lessonname = p.down('[name=lesson_name]').getValue();
                                params.grade_name = grade.get('value');
                                params.publish = p.down('[name=publish]').getValue();
                                this.owner.is_store_loaded = true;
                                if(!(params.lessonname && params.publish)) {
                                    return false;
                                }
                                Ext.apply(this.proxy.extraParams, params);
                            },
                            load: function(s){
                                s.each(function(rc){
                                    var y = rc.get('year'), m = rc.get('month'), d = rc.get('number');
                                    rc.set('text', Ext.String.format("{0}年{1}月第{2}版", y, m, d));
                                    rc.set('value', y + '-' + m + '-' + d);
                                });
                            }
                        }
                    }),
                    listeners: {
                        afterrender:function(){
                            this.store.owner = this;
                        }
                    }
                }]
            }],
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form').getForm(),
                        tabpanel, index, mask, inforc;
                    if(!fm.isValid()) { return; }
                    inforc = fm.findField('date');
                    inforc = inforc.findRecordByValue(inforc.getValue());
                    mask = new Ext.LoadMask(win, {msg: '正在提交...'});
                    mask.show();
                    fm.submit({
                        params: {
                            term_uuid: tuid,
                            remark: inforc.get('remark'),
                            cover_pic: inforc.get('cover_pic'),
                            version_pic: inforc.get('version_pic')
                        },
                        url: '/system/term/syllabus/remote-get/',
                        success: function(form, action){
                            var data = action.result;
                            mask.destroy();
                            win.destroy();
                            
                            if(data.status == "success") {
                                tabpanel.insert(index, {
                                    xtype: 'courseoutlineinfo',
                                    rawData: data.data.records
                                });
                                tabpanel.setActiveTab(index);
                            }
                        },
                        failure: function(form, action){
                            mask.destroy();
                            win.destroy();
                            Ext.Msg.alert('提示', action.result.msg);
                        }
                    });
                    tabpanel = win.__parent.down('tabpanel');
                    index = tabpanel.items.getCount()-1;
                }
            }, {
                text: '关闭',
                handler: function(){
                    this.up('window').destroy();
                }
            }],
            buttonAlign: 'right'
        };
        Ext.widget(winc).show();
    }
});
Ext.define('bbt.CourseOutlineInfo', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.courseoutlineinfo',
    grade_name: null,
    lesson_name: null,
    importUrl: null,
    initComponent: function(){
        var raw = this.rawData || {};
        this.layout = {type: "hbox", align: 'stretch'};
        this.defaults = {border: false};
        this.title = raw.lesson_name || '';
        this.items = [{
            xtype: 'panel',
            bodyStyle: {borderRightWidth: '1px !important'},
            flex: 1,
            layout: {type:'vbox', align: 'stretch'},
            defaults: {margin: 10},
            defaultType: 'displayfield',
            items: [{
                xtype: 'checkbox',
                name: 'in_use',
                fieldLabel: '是否启用同步',
                checked: raw.in_use,
                disabled: raw.in_use,
                listeners: {
                    change: function(me, v){
                        if(!v) { return; }
                        var lesson_name = me.up('courseoutlineinfo').title,
                            outline = me.up('courseoutline'),
                            grade_name = outline.getSelectGrade().get('value'),
                            term_uuid = outline.term_uuid,
                            publish = me.ownerCt.down('[name=publish]').getValue(),
                            bookversion = me.ownerCt.down('[name=bookversion]')._value,
                            passCB;
                        passCB = function(){
                            Ext.Ajax.request({
                                url: '/system/term/syllabus/lesson-enable/',
                                method: 'POST',
                                params: {
                                    bookversion: bookversion,
                                    publish: publish,
                                    lesson_name: lesson_name,
                                    grade_name: grade_name,
                                    term_uuid: term_uuid
                                },
                                callback: function(_1, _2, resp){
                                    var data = Ext.decode(resp.responseText);
                                    if(data.status == "success") {
                                        me.setDisabled(true);
                                    } else {
                                        me.setValue(false);
                                        Ext.Msg.alert('提示', data.msg || '启用失败');
                                    }
                                }
                            });
                        };
                        new bbt.DangerOperate({onPass: passCB, onFail: function(){
                            me.setValue(false);
                        }}).show();
                    }
                }
            }, {
                name: 'publish',
                fieldLabel: '出版社',
                value: raw.publish
            }, {
                name: 'bookversion',
                fieldLabel: '版本日期',
                _value: raw.bookversion,
                value: raw.bookversion ? raw.bookversion.replace('-', '年').replace('-', '月第') + '版' : '',
            }, {
                name: 'volume',
                fieldLabel: '书册',
                value: raw.volume
            }, {
                xtype: 'displayfield',
                fieldLabel: '备注',
                name: 'remark',
                value: raw.remark || ''
            }, {
                xtype: 'displayfield',
                labelWidth: 0,
                labelSeparator: '',
                value: '教材贴图:',
            }, {
                xtype: 'container',
                layout: {type: 'hbox', align: 'stretch'},
                flex: 1,
                defaults: {flex:1},
                items: [{
                    xtype: 'image',
                    margin: '0 5 0 0',
                    src: raw.picture_host
                }, {
                    xtype: 'image',
                    margin: '0 0 0 5',
                    src: raw.picture_url
                }]
            }]
        }, {
            xtype: 'treepanel',
            bodyStyle: {borderTopWidth: 0},
            rootVisible: false,
            useArrows: true,
            store: new Ext.data.TreeStore({
                root: {expanded: true, text: ''},
                loadId: raw.id,
                listeners: {
                    beforeload: function(s){
                        Ext.Ajax.request({
                            method: 'GET',
                            url: '/system/term/syllabus/content-list/',
                            params: {
                                id: s.loadId
                            },
                            callback: function(_1, _2, resp){
                                var data = Ext.decode(resp.responseText), nodes = {}, keys, sortFn, root;
                                if(data.status != "success") { return; }
                                Ext.each(data.data.records, function(rc){
                                    var id, pid, obj;
                                    if(!rc) { return; }
                                    id = rc.id;
                                    pid = rc.parent_id;
                                    if(pid) {
                                        obj = nodes[pid];
                                        if(!obj) {
                                            obj = nodes[pid] = {id: pid, expanded: true, children: []};
                                        }
                                        obj.children.push({text: rc.title, id: id, seq: rc.seq, leaf: true});
                                    } else {
                                        if(!nodes[id]) {
                                            nodes[id] = {text: rc.title, id: id, seq: rc.seq, expanded: true, children: []};
                                        } else {
                                            nodes[id].seq = rc.seq;
                                            nodes[id].text = rc.title;
                                        }
                                    }
                                });
                                sortFn = function(a, b){
                                    if(a.seq < b.seq) { return -1; }
                                    else if(a.seq > b.seq) { return 1; }
                                    return 0;
                                };

                                keys = Ext.Object.getKeys(nodes);
                                nodes = Ext.Array.map(keys, function(k){
                                    nodes[k].children.sort(sortFn);
                                    return nodes[k];
                                });
                                nodes.sort(sortFn);
                                root = s.getRootNode();
                                root.removeAll();
                                nodes.length && root.appendChild(nodes);
                            }
                        });
                        return false;
                    }
                }
            }),
            flex: 1
        }];
        this.callParent();
    }
});
/* 学校开课课程管理 */
Ext.define('bbt.Lesson', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.lesson2',
    fields: ['uuid', 'name', 'types'],
    columns: [{
        xtype: 'rownumberer',
        text: '序号',
        width: 50
    }, {
        text: '课程名称',
        dataIndex: 'name',
        width: 150
    }, {
        text: '适用学校类型',
        width: 120,
        dataIndex: 'types',
        renderer: function(v){
            return typeof v == "string" ? v : v.join('，');
        }
    }],
    pagination: true,
    showOperateColumn: true,
    tbar: [{
        text: '添加课程',
        action: 'add',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '编辑课程',
        action: 'edit',
        iconCls: 'tool-icon icon-edit'
    }/*, {
        xtype: 'form',
        bodyCls: 'no-bg',
        border: false,
        items: [{
            xtype : 'fileuploadfield',
            name : 'excel',
            buttonOnly : true,
            margin : 0,
            padding : 0,
            buttonConfig : {text : '导入', iconCls: 'icon-import'},
            listeners: {
                change: function(f, path){
                    var grid = f.up('lesson');
                    if(!/\.xlsx?$/.test(path)) {
                        //Ext.Msg.alert('提示', '请选择 excel 文件！');
                        f.reset();
                        return;
                    }
                    f.up('form').submit({
                        url: grid.importUrl,
                        success: function(form, a){ f.reset(); grid.store.load(); },
                        failure: function(){ f.reset(); }
                    });
                }
            }
        }]
    }*/],
    listUrl: '/system/new_lesson_name/list/',
    addUrl: '/system/new_lesson_name/add/',
    updateUrl: '/system/new_lesson_name/edit/',
    removeUrl: '/system/new_lesson_name/delete/',
    importUrl: '/system/new_lesson_name/import/',
    actionMap: {add: 'addCourse', edit: 'updateCourse', remove: 'removeCourse'},
    operates: {remove: '删除'},
    canEdit: false,
    listeners: {
        show: function(){ this.store.load(); }
    },
    addCourse: function(){
        var me = this, config, win;
        config = Ext.apply(me.getCourseWindowConfig(), {
            title: '添加课程',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form');
                    if(!fm.getForm().isValid()) {
                        //Ext.Msg.alert('提示', '请填写课程名称！');
                        return;
                    }

                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加课程'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.show();
    },
    updateCourse: function(){
        var me = this, config, win, course, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择课程！');
            return;
        }
        course = select[0];
        config = Ext.apply(me.getCourseWindowConfig(), {
            title: '编辑课程',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form');
                    if(!fm.getForm().isValid()) {
                        Ext.Msg.alert('提示', '请填写课程！');
                        return;
                    }
                    me.request(me.updateUrl, {uuid:course.get('uuid'),form:fm}, {
                        form: fm,
                        maskId: me.createMask(win, '正在修改课程'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.down('form').getForm().setValues(course.data);
        win.down('textfield').setReadOnly(true);
        win.show();
    },
    removeCourse: function(rc){
        var me = this, course, select, maskId, passCB;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择课程！');
            return;
        }
        course = select[0];
        passCB = function(){
            me.request(me.removeUrl, {uuid: course.get('uuid')}, {
                success: function(){
                    me.store.reload();
                },
                maskId: me.createMask(this, '正在删除课程')
            });
        };
        Ext.Msg.confirm('提示', '删除课程将会影响班级授课教师信息，统计分析等，确认要删除吗？', function(b){
            b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
        });
    },
    getCourseWindowConfig: function(){
        var config = {
            modal: true,
            closable: false,
            width: 350,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                margin: 20,
                bodyCls: 'no-bg',
                layout: 'anchor',
                defaults: {anchor: '100%'},
                items: [{
                    xtype: 'textfield',
                    fieldLabel: '课程名称',
                    maxLength: 20,
                    allowBlank: false,
                    name: 'name',
                    listeners: {
                        blur: function(){
                            var v = this.getValue(), nv;
                            nv = v.replace(/[ 　]/g, '');
                            if(nv.length != v.length) {
                                this.setValue(nv);
                            }
                        }
                    }
                }, {
                    xtype: 'checkboxgroup',
                    fieldLabel: '适用学校类型',
                    columns: 1,
                    vertical: true,
                    items: [
                        { boxLabel: '小学', name: 'types', inputValue: '小学', checked: true },
                        { boxLabel: '初中', name: 'types', inputValue: '初中', checked: true },
                        { boxLabel: '高中', name: 'types', inputValue: '高中', checked: true }
                    ]
                }]
            }],
            buttonAlign: 'right'
        };
        return config;
    }
});
/* 教学资源管理 */
/* 资源类型 */
Ext.define('bbt.ResourceType', {
    extend : 'bbt.ManageGrid',
    alias : 'widget.bbt_resource_type',
    tbar: [{
        text : '添加资源类型',
        action: 'system_resource_add',
        iconCls : 'tool-icon icon-add'
    }, {
        text : '删除资源类型',
        action: 'system_resource_delete',
        iconCls : 'tool-icon icon-delete'
    }],
    columns: [{
        text: '资源类型',
        dataIndex: 'value',
        width: 380
    }, {
        text: '备注',
        dataIndex: 'remark',
        flex: 1
    }],
    listeners: {
        show: function(){ this.store.load(); }
    },
    showOperateColumn: false,
    actionMap: {system_resource_add: 'addResource', system_resource_delete: 'deleteResource'},
    pagination: true,
    fields: ['uuid', 'value', 'remark'],
    listUrl: '/system/resource/resource-type/',
    addUrl: '/system/resource/resource-type/add/',
    removeUrl: '/system/resource/resource-type/delete/',
    addResource: function(){
        var me = this, config, win;
        config = Ext.apply(me.getResourceWindowConfig(), {
            title: '添加资源类型',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form');
                    if(!fm.getForm().isValid()) {
                        //Ext.Msg.alert('提示', '请填写资源名称！');
                        return;
                    }

                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加资源类型'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.show();
    },
    editResource: function(){
        var me = this, config, win, res, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择资源类型！');
            return;
        }
        res = select[0];
        config = Ext.apply(me.getResourceWindowConfig(), {
            title: '编辑资源类型',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form');
                    if(!fm.getForm().isValid()) {
                        Ext.Msg.alert('提示', '请填写资源类型！');
                        return;
                    }
                    apiRequest.target = win;
                    apiRequest.msg = '正在编辑资源类型：' + res.get('value');
                    apiRequest(me.updateUrl, {id: res.get('uuid'), form: fm, waitTarget: win}, function(data){
                        res.set(data.data);
                        res.commit();
                        win.destroy();
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.down('form').getForm().setValues(res.data);
        win.show();
    },
    deleteResource: function(){
        var me = this, config, win, res, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择资源类型！');
            return;
        }
        res = select[0];

        me.request(me.removeUrl, {uuid:res.get('uuid')}, {
            maskId: me.createMask(me, '正在删除资源类型：' + res.get('value')),
            success: function(){
                if(me.store.count() === 1) {
                    me.store.previousPage();
                } else {
                    me.store.reload();
                }
            }
        });
    },
    refreshResource: function(){
        this.store.reload();
    },
    getResourceWindowConfig: function(){
        var config = {
            modal: true,
            closable: false,
            width: 350,
            height:250,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                margin: 20,
                bodyCls: 'no-bg',
                layout: 'anchor',
                defaults: {anchor: '100%'},
                items: [{
                    xtype: 'textfield',
                    fieldLabel: '资源类型',
                    maxLength: 20,
                    allowBlank: false,
                    //editable: false,
                    name: 'value'
                    //store: ['音频', '音视频', 'PPT 幻灯片', '文档', '动画片', '其它']
                }, {
                    xtype: 'textarea',
                    height: 95,
                    name: 'remark',
                    maxLength: 180,
                    fieldLabel: '备注'
                }]
            }],
            buttonAlign: 'right'
        };
        return config;
    }
});
Ext.define('bbt.ResourceFrom', {
    extend : 'bbt.ManageGrid',
    alias : 'widget.bbt_resource_from',
    tbar: [{
        text : '添加资源来源',
        action: 'system_resource_add',
        iconCls : 'tool-icon icon-add'
    }, {
        text : '删除资源来源',
        action: 'system_resource_delete',
        iconCls : 'tool-icon icon-delete'
    }],
    columns: [{
        text: '资源来源',
        dataIndex: 'value',
        width: 380
    }, {
        text: '备注',
        dataIndex: 'remark',
        flex: 1
    }],
    listeners: {
        show: function(){ this.store.load(); }
    },
    showOperateColumn: false,
    actionMap: {system_resource_add: 'addResource', system_resource_delete: 'deleteResource'},
    pagination: true,
    fields: ['uuid', 'value', 'remark'],
    listUrl: '/system/resource/resource-from/',
    addUrl: '/system/resource/resource-from/add/',
    removeUrl: '/system/resource/resource-from/delete/',
    addResource: function(){
        var me = this, config, win;
        config = Ext.apply(me.getResourceWindowConfig(), {
            title: '添加资源来源',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form');
                    if(!fm.getForm().isValid()) {
                        //Ext.Msg.alert('提示', '请填写资源来源！');
                        return;
                    }

                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加资源来源'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.show();
    },
    editResource: function(){
        var me = this, config, win, res, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择资源来源！');
            return;
        }
        res = select[0];
        config = Ext.apply(me.getResourceWindowConfig(), {
            title: '编辑资源来源',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form');
                    if(!fm.getForm().isValid()) {
                        Ext.Msg.alert('提示', '请填写资源来源！');
                        return;
                    }
                    apiRequest.target = win;
                    apiRequest.msg = '正在编辑资源来源：' + res.get('value');
                    apiRequest(me.updateUrl, {id: res.get('uuid'), form: fm, waitTarget: win}, function(data){
                        res.set(data.data);
                        res.commit();
                        win.destroy();
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        win.down('form').getForm().setValues(res.data);
        win.show();
    },
    deleteResource: function(){
        var me = this, config, win, res, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择资源来源！');
            return;
        }
        res = select[0];

        me.request(me.removeUrl, {uuid:res.get('uuid')}, {
            maskId: me.createMask(me, '正在删除资源来源：' + res.get('value')),
            success: function(){
                if(me.store.count() === 1) {
                    me.store.previousPage();
                } else {
                    me.store.reload();
                }
            }
        });
    },
    refreshResource: function(){
        this.store.reload();
    },
    getResourceWindowConfig: function(){
        var config = {
            modal: true,
            closable: false,
            width: 350,
            height:250,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                margin: 20,
                bodyCls: 'no-bg',
                layout: 'anchor',
                defaults: {anchor: '100%'},
                items: [{
                    xtype: 'textfield',
                    name: 'value',
                    allowBlank: false,
                    fieldLabel: '资源来源',
                    maxLength: 50
                }, {
                    xtype: 'textarea',
                    height: 95,
                    maxLength: 180,
                    name: 'remark',
                    fieldLabel: '备注'
                }]
            }],
            buttonAlign: 'right'
        };
        return config;
    }
});
Ext.define('bbt.Resource', {
    extend : 'Ext.tab.Panel',
    alias : 'widget.bbt_resource',
    defaults: {border: false},
    items: [{
        title: '资源来源管理',
        xtype: 'bbt_resource_from'
    }, {
        title: '资源类型管理',
        xtype: 'bbt_resource_type'
    }]
});
//定义管理范围查询
Ext.Object.each({province: '省', city: '地市州', country: '区县市', town: '街道乡镇', school: '学校'}, function(v, label){
    var store = new Ext.data.Store({
        storeId: v+'Store',
        fields: ['name', 'uuid', 'group_type', 'parent__uuid', 'children'],
        listeners: {
            load: function(s){
                s.insert(0, [{name: '所有'}]);
            }
        }
    });
    bbt.ToolBox.register(v, {
        xtype: 'combo',
        name: v + "_name",
        fieldLabel: label,
        labelWidth: label.length * 20,
        width: 100 + label.length * 20,
        queryMode: 'local',
        store: store,
        editable: false,
        displayField: 'name',
        submitField: 'name',
        valueField: 'uuid',
        forceSelection: true,
        listeners: {
            afterrender: function(){
                var me = this,
                    levels = 'province city country town school'.split(' '),
                    clevel = me.name.replace('_name', ''),
                    index = Ext.Array.indexOf(levels, clevel),
                    cIndex = Ext.Array.indexOf(levels, bbt.UserInfo.level);
                if(cIndex+1 !== index) { return; }
                setTimeout(function(){
                    me.setValue('');
                }, 300);
            },
            change: function(me, v){
                var levels = ['province', 'city', 'country', 'town', 'school'],
                    clevel = me.name.replace('_name', ''),
                    found = false, combo, raw, next, p;
                Ext.each(levels, function(v){
                    var cmp;
                    if(found) {
                        cmp = me.ownerCt.down('[name=' + v + '_name]');
                        if(cmp) {
                            cmp.store.loadData([{name: '所有'}]);
                            cmp.setValue('');
                        }
                    }
                    if(v === clevel) {
                        found = true;
                    }
                });
                p = me.up('grid') || me.up('toolbar') || p.ownerCt.ownerCt;
                if(!v){
                    combo = p.down('[name=grade_name]');
                    if(combo) {
                        combo.store.loadData([{name: '所有'}]);
                        combo.setValue('');
                    }
                    combo = p.down('[name=lesson_period]');
                    if(combo){
                        combo.store.loadData([{sequence: '所有'}]);
                        combo.setValue('');
                    }
                    combo = p.down('[name=lesson_name]');
                    if(combo) {
                        combo.store.loadData([{name: '所有'}]);
                        combo.setValue('所有');
                    }
                } else if(clevel == 'school') {
                    combo = p.down('[name=grade_name]');
                    combo && combo.store.load();
                    combo = p.down('[name=lesson_period]');
                    combo && combo.store.load();
                    combo = p.down('[name=lesson_name]');
                    combo && combo.store.load();
                } else {
                    raw = me.findRecordByValue(v);
                    raw && (raw = raw.raw.children);
                    if(raw) {
                        next = levels[Ext.Array.indexOf(levels, clevel)+1];
                        next = me.ownerCt.down('[name=' + next + '_name]');
                        if(next){
                            next.store.loadData(raw);
                            next.store.fireEvent('load', next.store);
                        }
                    }
                }
            }
        }
    });
});

bbt.loadGroup();
/* 服务器汇聚管理 */
Ext.define('bbt.NodeManager', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.bbt_nodemanager',
    columns: [{
        text: '学校名称',
        dataIndex: 'name',
        width: 200,
        renderer: function(v,m,r){
            if(r.get('online')) {
                return '<span style="color:green">' + v + '</span>';
            } else {
                return '<span style="color:red">' + v + '</span>';
            }
        }
    }, {
        text: '终端使用/分配数',
        width: 160,
        dataIndex: 'xx',
        renderer: function(v,m,r){
            return r.get('use_number') + '/' + r.get('activation_number')
        }
    }, /*{
        text: '服务器IP地址',
        dataIndex: 'host',
        width: 160
    }, */{
        text: '服务器密钥',
        dataIndex: 'communicate_key',
        width: 150
    }, {
        text: '同步 ID',
        width: 60,
        dataIndex: 'last_upload_id'
    }, {
        text: '状态',
        width: 40,
        dataIndex: 'sync_status'
    }, {
        text: '最后同步时间',
        width: 150,
        dataIndex: 'last_upload_time'
    }, {
        text: '最后连接时间',
        width: 150,
        dataIndex: 'last_active_time'
    }, {
        text: '版本',
        width: 40,
        dataIndex: 'db_version'
    }, {
        text: '备注',
        dataIndex: 'remark',
        width: 200
    }],
    viewConfig: {enableTextSelection: true},
    pagination: true,
    showOperateColumn: true,
    tbar: [{
        text: '添加',
        action: 'system_node_add',
        iconCls: 'tool-icon icon-add'
    }, {
        text: '编辑',
        action: 'system_node_edit',
        iconCls: 'tool-icon icon-edit'
    }, {
        text: '删除',
        action: 'system_node_delete',
        iconCls: 'tool-icon icon-delete'
    }],
    fields: ['id', 'name', 'host', 'communicate_key', 'remark', 'last_upload_id', 'last_active_time', 'last_upload_time', 'db_version', 'sync_status', 'online', 'activation_number', 'use_number'],
    listUrl: '/system/node/list/',
    exportUrl: '/system/node/backup/',
    addUrl: '/system/node/add/',
    removeUrl: '/system/node/delete/',
    updateUrl: '/system/node/edit/',
    operates: {/*'export': '导出'*/},
    actionMap: {system_node_add: 'addNode', system_node_edit: 'editNode', system_node_delete: 'deleteNode', unbind: 'unbindNode', 'export':'exportNode'},
    //pagination: true,
    listeners: {
        show: function(){
            var ws = this.createWebSocket();
            if(ws !== null) {
                this.store.on('load', function(s){
                    ws.emit({"category": "localserver", "operation": "nodeinfo"}, function(data){
                        var idmap = {};
                        if(data.data.records) {
                            Ext.each(data.data.records, function(id){ idmap[id] = '' });
                            s.each(function(rc){
                                (rc.get('id') in idmap) && rc.set('online', true);
                            });
                        }
                    });
                });
            }
            this.store.load();
        }
    },
    createWebSocket: function(){
        var ws = null, i = 0;
        if(window.WebSocket) {
            ws = new WebSocket('ws://' + location.host + '/ws/localserver');
            // ws = new WebSocket('ws://' + location.hostname + ':8001/ws/localserver');
            //ws = new WebSocket('ws://localhost:8001/ws/localserver');
            ws._callbacks = {};
            ws._queue = [];
            ws.onmessage = function(e){
                var data;
                try {
                    data = Ext.decode(e.data);
                    if(data.callback) {
                        ws._callbacks[data.callback](data);
                        delete ws._callbacks[data.callback];
                    } else {
                        console.log("unexpected response:", e.data);
                    }
                } catch(e) {
                    console.log(e);
                }
            };
            ws.onopen = function(){
                while(ws._queue.length) {
                    ws.send(ws._queue.shift());
                }
            };
            ws.emit = function(data, callback){
                var callbackId = 'callback-' + i++;
                if(typeof data == 'string') {
                    data = {data: data, callback: callbackId};
                } else {
                    data.callback = callbackId;
                }
                ws._callbacks[callbackId] = callback;
                if(ws.readyState == WebSocket.OPEN) {
                    ws.send(Ext.encode(data));
                } else {
                    console.error('websocket was not ready, store data');
                    ws._queue.push(Ext.encode(data));
                }
            };
        } else {
            console.error("你的服务器不支持 WebSocket ");
        }
        return ws;
    },
    addNode: function(){
        var me = this, config, win;
        config = Ext.apply(me.getNodeWindowConfig(), {
            title: '添加节点',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'), vmsg;
                    vmsg = checkForm(fm);
                    if(vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }

                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加节点'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 20 0 0',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        me.setTerminalNumber(win);
        win.show();
    },
    editNode: function(){
        var me = this, config, win, node, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择节点！');
            return;
        }
        node = select[0];
        config = Ext.apply(me.getNodeWindowConfig('edit'), {
            title: '编辑节点',
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'), vmsg;
                    vmsg = checkForm(fm);
                    if(vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }

                    me.request(me.updateUrl, {id: node.get('id'), form: fm}, {
                        maskId: me.createMask(win, '正在修改节点'),
                        success: function(data){
                            node.set(data.data);
                            node.commit();
                            win.destroy();
                        }
                    });
                }
            }, {
                text: '关闭',
                handler: function(){this.up('window').destroy();}
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        me.setTerminalNumber(win);
        win.down('form').getForm().setValues(node.data);
        win.show();
    },
    deleteNode: function(){
        var me = this, node, select, passCB;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择节点！');
            return;
        }
        node = select[0];
        Ext.Msg.confirm('提示', '删除节点将清空该节点下所有数据，是否确定删除？', function(b){
            if(b != 'yes') { return; }
            if(node.get('last_upload_id') > 0) {
                new bbt.DangerOperate({onPass: passCB}).show();
            } else {
                passCB();
            }
        });
        passCB = function(){
            me.request(me.removeUrl, {id: node.get('id')}, {
                maskId: me.createMask(me, '正在删除节点数据……'),
                method: 'POST',
                success:function(){
                    me.store.reload();
                }
            });
        };
    },
    exportNode: function(v, rc){
        var me = this;
        me.request(me.exportUrl, {id: rc.get('id')}, {
            method: 'GET',
            maskId: me.createMask(me, '正在准备数据……'),
            success: function(data, raw){
                downloadFile(raw.url, '');
            }
        });
    },
    setTerminalNumber: function(win){
        Ext.Ajax.request({
            url: '/activation/api/get_none_activate/',
            method: 'GET',
            callback: function(_1, _2, resp){
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    win.down('[name=none_number]').setValue(data.data.none_number);
                }
            }
        })
    },
    getNodeWindowConfig: function(action){
        var config = {
            width: 360,
            modal: true,
            closable: false,
            resizable: false,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls: 'no-bg',
                border: false,
                layout: 'anchor',
                padding: 20,
                defaults: {labelWidth: 75, anchor: '100%', allowBlank: false},
                items: [{
                    xtype: 'textfield',
                    name: 'name',
                    fieldLabel: '学校名称',
                    maxLength: 20,
                    hidden: (bbt.UserInfo.level !== 'country'),
                    readOnly: action === "edit" || (bbt.UserInfo.level !== 'country')
                }, {
                    xtype: 'panel',
                    border: false,
                    bodyCls: 'no-bg',
                    layout: 'hbox',
                    margin: '0 0 5 0',
                    hidden: action === "edit",
                    items: [{
                        xtype: 'textfield',
                        flex: 1,
                        labelWidth: 75,
                        name: 'communicate_key',
                        fieldLabel: '密钥',
                        readOnly: true,
                        validator: function(v){
                            return /^[0-9A-F]{16}$/.test(v) ? true : '只能填写16位数字或大写字母ABCDEF，不可为空';
                        }
                    }, {
                        xtype: 'button',
                        margin: '0 0 0 10',
                        text: '自动生成',
                        handler: function(){
                            var chars = '0123456789ABCDEF',
                                time = new Date().getTime() + '',
                                len = time.length, i = 0, ret = [], tmp;
                            for(;i<len;i++) {
                                tmp = parseInt(time.charAt(i)) * (Math.random() > 0.5 ? 1 : -1);
                                if(tmp < 0) { tmp = 16 + tmp; }
                                ret.push(chars.charAt(tmp));
                            }
                            this.up('panel').down('textfield').setValue(ret.join('') + '222');
                        }
                    }]
                }, {
                    xtype: 'textfield',
                    fieldLabel: '分配终端数',
                    name: 'activation_number',
                    regex: /^\d+$/
                }, {
                    xtype: 'displayfield',
                    fieldLabel: '剩余终端数',
                    name: 'none_number',
                    value: 0
                }, {
                    xtype: 'textarea',
                    name: 'remark',
                    maxLength: 180,
                    height: 50,
                    fieldLabel: '备注',
                    allowBlank: true
                }]
            }]
        };
        return config;
    }
});
Ext.define('bbt.EduRecvNodeManage', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.edupoint_recv',
    tbar: [{text: '清除绑定', action: 'clear_bind', iconCls: 'tool-icon icon-clear'}, {tool:'schoolYear',useFirst: true}, 'term', 'eduTown', 'eduPoint', 'report_status', {xtype: 'textfield', fieldLabel: '终端密钥', labelWidth: 60, width: 160,name: 'key'}, 'query'],
    fields: ['school_year', 'term_type', 'town_name', 'point_name', 'key', 'status', 'last_upload_time', 'last_active_time', 'uuid'],
    columns: [{
        text: '学年',
        dataIndex: 'school_year'
    }, {
        text: '学期类型',
        dataIndex: 'term_type'
    }, {
        text: '街道乡镇',
        width: 160,
        dataIndex: 'town_name'
    }, {
        text: '教学点名称',
        width: 220,
        dataIndex: 'point_name'
    }, {
        text: '终端密钥',
        width: 150,
        dataIndex: 'key'
    }, {
        text: '申报状态',
        dataIndex: 'status',
        renderer: function(v){
            return v || '未申报';
        }
    }, {
        text: '使用数据同步日期',
        width: 160,
        dataIndex: 'last_active_time'
    }, {
        text: '最后同步时间',
        width: 160,
        dataIndex: 'last_upload_time'
    }],
    viewConfig: {enableTextSelection: true},
    showOperateColumn: false,
    pagination: true,
    actionMap: {clear_bind: 'clearBind'},
    listUrl: '/edu-unit/manage/receiver/list/',
    unbindUrl: '/edu-unit/manage/receiver/unbind/',
    listeners: {
        beforerender: bbt.autoArea,
        afterrender: function(){
            var me = this;
            bbt.loadCurrentSchoolYear(function(_1,_2, resp){
                var data = Ext.decode(resp.responseText),
                    school_year = data.data.school_year,
                    term_type = data.data.term_type;
                me.down('[name=school_year]').setValue(school_year);
                me.down('[name=term_type]').setValue(term_type).on('change', function(me, v){
                    var town = me.ownerCt.down('[name=town_name]');
                    if(town) {
                        if(v) {
                            town._loaded && town.store.load();
                        } else {
                            if(town._loaded) {
                                town.store.loadData([{key: '所有'}]);
                                town.setValue('所有');
                            }
                        }
                    }
                });
            });
        },
        show: function(){ this.store.load(); }
    },
    clearBind: function(){
        var me = this, select, rc, fm;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            rc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        if(rc.get('status') == "未申报") { return; }
        Ext.Msg.confirm('提示', '该操作将清除此密钥所绑定的终端硬件信息，是否继续？', function(b){
            if(b == 'yes') {
                new bbt.DangerOperate({onPass: function(){
                    me.request(me.unbindUrl, {uuid: rc.get('uuid')}, {
                        maskId: me.createMask(me, '正在清除 MAC 地址绑定！'),
                        success: function(){
                            me.store.reload();
                        }
                    });
                }}).show();
            }
        });
    }
});
Ext.define('bbt.EduClassNodeManage', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.edupoint_class',
    tbar: [{text: '清除绑定', action: 'clear_bind', iconCls: 'tool-icon icon-clear'}, {tool:'schoolYear',useFirst: true}, 'term', 'eduTown', 'eduPoint', 'report_status', {xtype: 'textfield', fieldLabel: '终端密钥', labelWidth: 60, width: 160,name: 'key'}, 'query'],
    fields: ['school_year', 'term_type', 'town_name', 'point_name', 'key', 'status', 'last_upload_time', 'last_active_time', 'number', 'uuid'],
    columns: [{
        text: '学年',
        dataIndex: 'school_year'
    }, {
        text: '学期类型',
        dataIndex: 'term_type'
    }, {
        text: '街道乡镇',
        width: 160,
        dataIndex: 'town_name'
    }, {
        text: '教学点名称',
        width: 220,
        dataIndex: 'point_name'
    }, {
        text: '教室编号',
        dataIndex: 'number',
        renderer: function(v){
            return "第 " + v + " 教室";
        }
    }, {
        text: '终端密钥',
        width: 150,
        dataIndex: 'key'
    }, {
        text: '申报状态',
        dataIndex: 'status',
        renderer: function(v){
            return v || '未申报';
        }        
    }, {
        text: '使用数据同步日期',
        width: 160,
        dataIndex: 'last_active_time'
    }, {
        text: '最后同步时间',
        width: 160,
        dataIndex: 'last_upload_time'
    }],
    viewConfig: {enableTextSelection: true},
    pagination: true,
    showOperateColumn: false,
    actionMap: {clear_bind: 'clearBind'},
    listUrl: '/edu-unit/manage/client/list/',
    unbindUrl: '/edu-unit/manage/client/unbind/',
    listeners: {
        show: function(){ this.store.load(); },
        afterrender: function(){
            var me = this;
            bbt.loadCurrentSchoolYear(function(_1,_2, resp){
                var data = Ext.decode(resp.responseText),
                    school_year = data.data.school_year,
                    term_type = data.data.term_type;
                me.down('[name=school_year]').setValue(school_year);
                me.down('[name=term_type]').setValue(term_type).on('change', function(me, v){
                    var town = me.ownerCt.down('[name=town_name]');
                    if(town) {
                        if(v) {
                            town._loaded && town.store.load();
                        } else {
                            if(town._loaded) {
                                town.store.loadData([{key: '所有'}]);
                                town.setValue('所有');
                            }
                        }
                    }
                });
            });
        }
    },
    clearBind: function(){
        var me = this, select, rc, fm;
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            rc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        if(rc.get('status') == "未申报") { return; }
        Ext.Msg.confirm('提示', '该操作将清除此密钥所绑定的终端硬件信息，是否继续？', function(b){
            if(b == 'yes') {
                new bbt.DangerOperate({onPass: function(){
                    me.request(me.unbindUrl, {uuid: rc.get('uuid')}, {
                        maskId: me.createMask(me, '正在清除 MAC 地址绑定！'),
                        success: function(){
                            me.store.reload();
                        }
                    });
                }}).show();
            }
        });
    }
});

/* 班班通登录状态 */
Ext.define('bbt.LoginStatus', {
    extend: 'Ext.view.View',
    alias: 'widget.loginstatus',
    autoScroll: true,
    tpl: [
        '<tpl for=".">',
            '<div class="class-item">',
                '<div class="status-icon {cls}">',
                    //'<img style="margin-top:{itemImageMarginTop}px;height:{itemImageSize}px;width:{itemImageSize}px" src="{[ bbtConfig.getAssetIcon(values.icon) ]}"/>',
                '</div>',
                '<div class="class-info">{info}</div>',
            '</div>',
        '</tpl>',
        '<div style="clear:both;height:15px;"></div>'],
    constructor: function(){
        var store = new Ext.data.Store({
            fields: ['grade_name', 'class_name', 'lesson_name', 'online', 'login_time'],
            proxy: {
                url: '/global/login-status/',
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            }
        });
        this.store = store;
        //store.load();
        this.callParent();
    },
    prepareData: function(data, index, record){
        var str = Ext.String.format(
            "{0}年级{1}班<br/>{2}<br/>已使用{3}分钟",
            data.grade_name, data.class_name, data.lesson_name,
            Math.floor(data.login_time/60));
        data.online || (data.cls = "offline");
        data.info = str;
        return data;
    }
});
Ext.define('bbt.LoginStatusPanel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.loginstatuspanel',
    tbar: [{xtype: 'tbtext', text: '当前不在上课!', style: {fontWeight: 'bold'}}],
    items: [{xtype: 'loginstatus'}],
    layout: 'fit',
    listeners: {
        afterrender: function(){
            var view = this.down('loginstatus'), store = view.store;
            store.on('load', function(s){
                try {
                    var rawData = s.proxy.reader.rawData;
                    this.updateJieci(rawData.status == "success" ?rawData.data.lesson_period:rawData.msg);
                } catch (e) {
                    console.log(e);
                }
                
            }, this);
            this.store = store;
            //this.setTreeStyle();
        }
    },
    updateJieci: function(info){
        var str;
        if(typeof info == "string") { str = '当前不在上课!'; return; }
        else {
            if(info) {
                str = Ext.String.format("当前节次：第{0}节    节次时间：{1}-{2}", info.sequence, info.start_time, info.end_time);
            } else {
                str = "当前不在上课!";
            }
        }
        
        this.down('toolbar[dock=top]').down('tbtext').setText(str);
    },
    setTreeStyle: function(){
        var tree = Ext.getCmp('content-panel').down('treepanel'), cb;
        tree.on('itemcollapse', function(node){
            var item = this.getView().getNode(node);
            item = Ext.fly(item);
            item.down('.x-grid-cell-inner').setStyle({backgroundColor:'#FFF',cursor: 'default'});
        });
        tree.on('itemexpand', function(node){
            var item = this.getView().getNode(node);
            item = Ext.fly(item);
            item.down('.x-grid-cell-inner').setStyle({backgroundColor:'#FFF',cursor: 'default'});
        });
        cb = function(){
            tree.getRootNode().cascadeBy(function(node){
                var item;
                if(node.raw.group_type != "school") {
                    item = tree.getView().getNode(node);
                    if(item) {
                        item = Ext.fly(item);
                        item.down('.x-grid-cell-inner').setStyle({backgroundColor:'#FFF',cursor: 'default'});
                    }
                }
            });
            tree.un('load', cb);
        };
        if(tree.isStoreLoaded) {
            cb();
        } else {
            tree.on('load', cb);
        }
    },
    onLevelChange: function(group_type, uuid){
        if(group_type != "school") { return; }
        this.store.load({params: {uuid: uuid}});
    }
});
/* 教学点管理 */
Ext.define('bbt.EduPoint', {
    extend: 'bbt.ManageGrid',
    alias: 'widget.edupoint',
    fields: ['school_year', 'term_type', 'town_name', 'point_name', 'number', 'remark', 'uuid'],
    columns: [{
        text: '学年',
        dataIndex: 'school_year'
    }, {
        text: '学期类型',
        dataIndex: 'term_type'
    }, {
        text: '街道乡镇',
        dataIndex: 'town_name'
    }, {
        text: '教学点名称',
        width: 220,
        dataIndex: 'point_name'
    }, {
        text: '终端个数',
        dataIndex: 'number'
    }, {
        text: '备注',
        dataIndex: 'remark'
    }],
    tbar: [{
        text: '添加',
        iconCls: 'tool-icon icon-add',
        action: 'add'
    }, {
        text: '编辑',
        iconCls: 'tool-icon icon-edit',
        action: 'update'
    }, {
        text: '删除',
        iconCls: 'tool-icon icon-delete',
        action: 'remove'
    }, {
        text: '资源接收目录管理',
        action: 'dirmanage'
    }, {tool:'schoolYear',useFirst:true}, 'term', 'eduTown', 'eduPoint', 'query'],
    addUrl: '/edu-unit/manage/node/add/',
    updateUrl: '/edu-unit/manage/node/edit/',
    removeUrl: '/edu-unit/manage/node/delete/',
    listUrl: '/edu-unit/manage/node/list/',
    pagination: true,
    showOperateColumn: false,
    actionMap: {add: 'addPoint', update: 'updatePoint', remove: 'removePoint', dirmanage: 'manageDirectory'},
    listeners: {
        show: function(){
            this.store.load();
        },
        afterrender: function(){
            var me = this;
            bbt.loadCurrentSchoolYear(function(_1,_2, resp){
                var data = Ext.decode(resp.responseText),
                    school_year = data.data.school_year,
                    term_type = data.data.term_type;
                me.down('[name=school_year]').setValue(school_year);
                me.down('[name=term_type]').setValue(term_type).on('change', function(me, v){
                    var town = me.ownerCt.down('[name=town_name]');
                    if(town) {
                        if(v) {
                            town._loaded && town.store.load();
                        } else {
                            if(town._loaded) {
                                town.store.loadData([{key: '所有'}]);
                                town.setValue('所有');
                            }
                        }
                    }
                });
            });
        }
    },
    addPoint: function(){
        var me = this, win;
        win = this.getPointWindowConfig({
            title: '添加教学点',
            buttons: [{
                text: '添加',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),msg;
                    msg = me.checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加教学点……'),
                        success: function(){
                            me.store.reload();
                            win.destroy();
                        },
                        failure: function(d){
                            Ext.Msg.alert('提示', getErrorMsg(d));
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 30 0 20',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        });
        win = Ext.widget(win);
        me.setTerminalNumber(win);
        win.show();
        me.hasSchoolYear(win);
    },
    updatePoint: function(){
        var me = this, win, select, rc, fm, numfield, tobeRemove = [];
        select = me.getSelectionModel().getSelection();
        if(select.length) {
            rc = select[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        win = this.getPointWindowConfig({
            title: '编辑教学点',
            buttons: [{
                text: '更新',
                handler: function(){
                    var win = this.up('window'),
                        fm = win.down('form'),msg;
                    msg = me.checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    me.request(me.updateUrl, {uuid: rc.get('uuid'), form: fm}, {
                        maskId: me.createMask(win, '正在更新教学点……'),
                        success: function(){
                            me.store.reload();
                            win.destroy();
                        },
                        failure: function(d){
                            Ext.Msg.alert('提示', getErrorMsg(d));
                        }
                    });
                }
            }, {
                text: '关闭',
                margin: '0 30 0 20',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        });
        win = Ext.widget(win);
        me.setTerminalNumber(win);
        fm = win.down('form').getForm();
        fm.setValues(rc.data);
        win.show();
        me.hasSchoolYear(win);
        fm.findField('town_name').setReadOnly(true);
        fm.findField('point_name').setReadOnly(true);
        numfield = fm.findField('number');
        numfield.store.each(function(rc){
            if(rc.get(numfield.valueField) < numfield.getValue()) {
                tobeRemove.push(rc);
            }
        });
        numfield.store.remove(tobeRemove);
    },
    removePoint: function(){
        var me = this, rc, i;
        rc = me.getSelectionModel().getSelection();
        if(rc.length) {
            rc = rc[0];
        } else {
            Ext.Msg.alert('提示', '请先选中一行！');
            return;
        }
        passCB = function(){
            me.request(me.removeUrl, {uuid:rc.get('uuid')}, {
                maskId: me.createMask(me, '正在删除教学点……'),
                success: function(){
                    me.store.reload();
                },
                failure: function(d){
                    Ext.Msg.alert('提示', getErrorMsg(d));
                }
            });
        };
        Ext.Msg.confirm('提示', '删除该密钥将同步删除已经上传的数据，请输入超级管理员密码进行确认！', function(b){
            b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
        });
    },
    manageDirectory: function(){
        var me = this, win;
        win = {
            xtype: 'window',
            modal: true,
            closable: true,
            resizable: false,
            width: 350,
            height: 450,
            layout: 'fit',
            title: '资源接收目录管理',
            items: [{
                xtype: 'mgrgridbase',
                border: false,
                tbar: [{
                    text: '新增扫描目录',
                    iconCls: 'tool-icon icon-add',
                    action: 'add'
                }, {
                    text: '删除扫描目录',
                    iconCls: 'tool-icon icon-delete',
                    action: 'remove'
                }],
                actionMap: {add: 'addDirectory', remove: 'removeDirectory'},
                showOperateColumn: false,
                listUrl: '/edu-unit/manage/node/resource-catalog/list/new/',
                addUrl: '/edu-unit/manage/node/resource-catalog/add/new/',
                removeUrl: '/edu-unit/manage/node/resource-catalog/delete/new/',
                fields: ['uuid', 'name', 'value'],
                columns: [{
                    xtype: 'rownumberer',
                    width: 50
                }, {
                    text: '目录',
                    dataIndex: 'value',
                    flex: 1
                }],
                addDirectory: function(){
                    var me = this, w;
                    w = this.getDirectoryWindowConfig({
                        title: '新增扫描目录',
                        buttons: [{
                            text: '确定',
                            handler: function(){
                                var win = this.up('window'),
                                    f = win.down('[name=catalog]');
                                if(!f.isValid()) {
                                    //Ext.Msg.alert('提示', msg);
                                    return;
                                }
                                me.request(me.addUrl, {catalog: f.getValue()}, {
                                    maskId: me.createMask(win, '正在添加目录……'),
                                    success: function(_, data){
                                        me.store.reload();
                                        win.destroy();
                                    },
                                    failure: function(d){
                                        Ext.Msg.alert('提示', getErrorMsg(d));
                                    }
                                });
                            }
                        }, {
                            text: '关闭',
                            handler: function(){
                                this.up('window').destroy();
                            }
                        }]
                    });
                    Ext.widget(w).show();
                },
                removeDirectory: function(){
                    var me = this, rc, i;
                    rc = me.getSelectionModel().getSelection();
                    if(rc.length) {
                        rc = rc[0];
                    } else {
                        Ext.Msg.alert('提示', '请先选中一行！');
                        return;
                    }
                    passCB = function(){
                        me.request(me.removeUrl, {uuid:rc.get('uuid')}, {
                            maskId: me.createMask(me, '正在删除目录……'),
                            success: function(){
                                me.store.reload();
                            }
                        });
                    };
                    Ext.Msg.confirm('提示', '删除扫描目录后，将不再统计该目录下的资源新增数据，请输入超级管理员密码进行确认！', function(b){
                        b == 'yes' && new bbt.DangerOperate({onPass: passCB}).show();
                    });
                },
                getDirectoryWindowConfig: function(defaults){
                    var w = {
                        xtype: 'window',
                        modal: true,
                        closable: false,
                        resizable: false,
                        width: 340,
                        layout: 'anchor',
                        items: [{
                            xtype: 'textfield',
                            fieldLabel: '目录',
                            allowBlank: false,
                            labelWidth: 45,
                            anchor: '100%',
                            margin: 30,
                            name: 'catalog'
                        }],
                        buttonAlign: 'right'
                    };
                    defaults && Ext.apply(w, defaults);
                    return w;
                }
            }]
        };
        win = Ext.widget(win).show();
        win.down('mgrgridbase').store.load();
    },
    setTerminalNumber: function(win){
        Ext.Ajax.request({
            url: '/activation/api/get_none_activate/',
            method: 'GET',
            callback: function(_1, _2, resp){
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    win.down('[name=none_number]').setValue(data.data.none_number);
                }
            }
        })
    },
    getPointWindowConfig: function(defaults){
        var win = {
            xtype: 'window',
            modal: true,
            closable: false,
            resizable: false,
            width: 350,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls:'no-bg',
                layout: 'anchor',
                margin: 30,
                border: false,
                defaults: {allowBlank: false, anchor: '100%'},
                items: [{
                    xtype: 'hidden',
                    name: 'school_year'
                }, {
                    xtype: 'hidden',
                    name: 'term_type'
                }, {
                    xtype: 'displayfield',
                    fieldLabel: '学年学期',
                    value: ''
                }, {
                    xtype: 'combo',
                    displayField: 'key',
                    valueField: 'key',
                    name: 'town_name',
                    fieldLabel: '街道乡镇',
                    editable: false,
                    store: new Ext.data.Store({
                        fields: ['key'],
                        proxy: {
                            type: 'ajax',
                            url: '/edu-unit/node-tree/list/',
                            reader: {
                                type: 'json',
                                root: 'data.records'
                            },
                            extraParams: {node_type: 'town'}
                        }
                    })
                }, {
                    xtype: 'textfield',
                    name: 'point_name',
                    fieldLabel: '教学点名称',
                    maxLength: 50,
                    validator: function(v) {
                        var rmspace = v.replace(/ /g, '');
                        if(rmspace.length === 0) {
                            return '请输入有效的教学点名称';
                        }
                        return true;
                    }
                }, {
                    xtype: 'combo',
                    name: 'number',
                    editable: false,
                    fieldLabel: '教室个数',
                    store: [1,2,3,4,5,6,7,8,9,10]
                }, {
                    xtype: 'displayfield',
                    name: 'none_number',
                    fieldLabel: '剩余终端数',
                    value: 0
                }, {
                    xtype: 'textareafield',
                    height: 60,
                    name: 'remark',
                    allowBlank: true,
                    fieldLabel: '备注'
                }]
            }],
            buttonAlign: 'right'
        };
        Ext.apply(win, defaults);
        return win;
    },
    hasSchoolYear: function(win){
        var setValue = function(school_year, term_type){
            var fm = win.down('form').getForm();
            win.down('displayfield').setValue(school_year+' （'+term_type+'）');
            fm.findField('school_year').setValue(school_year);
            fm.findField('term_type').setValue(term_type);
        };
        bbt.loadCurrentSchoolYear(function(opts, _, resp){
            var data = Ext.decode(resp.responseText);
            if(data.status == "success") {
                setValue(data.data.school_year, data.data.term_type);
            } else {
                Ext.Ajax.request({
                    url: '/system/term/current-or-next/',
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText);
                        if(data.status == "success" && data.data.records.length) {
                            data = data.data.records[0];
                            setValue(data.school_year, data.term_type);
                        } else {
                            Ext.Msg.alert('提示', '没有可用的学期！', function(){
                                win.destroy();
                            });
                        }
                    }
                });
            }
        });
    }
});

bbt.createEduStore = function(node_type, sorters){
    var store = new Ext.data.Store({
        fields: ['key'],
        sorters: sorters,
        data: [{key: '所有'}],
        proxy: {
            type: 'ajax',
            url: '/edu-unit/node-tree/list/',
            reader: {
                type: 'json',
                root: 'data.records'
            },
            extraParams: {node_type: node_type}
        },
        listeners: {
            beforeload: function(s){
                var ownerCt = s.owner.up('grid'), tmp, params = s.proxy.extraParams;
                Ext.each(['school_year', 'term_type', 'town_name', 'point_name'], function(name){
                    var f = ownerCt.down('[name=' + name + ']'), v;
                    if(f) {
                        v = f.getValue();
                        params[name] = v == '所有' ? '' : v;
                    }
                });
                params.ori = s.owner.dataOrigin;
            },
            load: function(s) {
                if(s.owner.displayAll) {
                    s.insert(0, {key: '所有'});
                    s.owner.setValue('所有');
                }
            }
        }
    });
    return store;
};
bbt.ToolBox.register({
    eduTown: function(){
        return {
            xtype: 'combo',
            displayField: 'key',
            valueField: 'key',
            name: 'town_name',
            fieldLabel: '街道乡镇',
            dataOrigin: 'unit',
            editable: false,
            displayAll: true,
            labelWidth: 80,
            width: 180,
            store: bbt.createEduStore('town'),
            value: '所有',
            _cascadeTimer: null,
            onTermChange: function(term, v){
                var me = this;
                if(me._cascadeTimer) {
                    clearTimeout(me._cascadeTimer);
                }
                me._cascadeTimer = setTimeout(function(){
                    me.store.load();
                    me._cascadeTimer = null;
                }, 100);
            },
            listeners: {
                afterrender: function(){
                    var term = this.up('grid').down('[name=term_type]');
                    this.store.owner = this;
                    if(term) {
                        term.on('change', this.onTermChange, this);
                    }
                },
                expand: function(){
                    this._loaded = true;
                },
                change: function(me, v){
                    var next = me.up('grid').down('[name=point_name]');
                    if(next && next._loaded) {
                        if(v && v != "所有") {
                            next.store.proxy.extraParams.town_name = v;
                            next.store.load();
                        } else {
                            next.store.loadData([{key: '所有'}]);
                        }
                        next.setValue('所有');
                    }
                }
            }
        };
    },
    eduPoint: function(){
        return {
            xtype: 'combo',
            displayField: 'key',
            valueField: 'key',
            name: 'point_name',
            fieldLabel: '教学点',
            displayAll: true,
            editable: false,
            labelWidth: 60,
            width: 160,
            value: '所有',
            store: bbt.createEduStore('unit'),
            listeners: {
                afterrender: function(){
                    this.store.owner = this;
                },
                expand: function(){
                    this._loaded = true;
                },
                change: function(me, v){
                    var next = me.up('grid').down('[name=number]');
                    if(next && next._loaded) {
                        next.store.proxy.extraParams.point_name = v;
                        next.store.load();
                    }
                }
            }
        };
    },
    eduClassNo: function(){
        var store = bbt.createEduStore('room', [{property: 'key', direction: 'ASC', transform: parseInt}]);
        return {
            xtype: 'combo',
            name: 'number',
            fieldLabel : '教室终端编号',
            listConfig: {
                minWidth: 40
            },
            displayField: 'key',
            valueField: 'key',
            displayAll: true,
            editable: false,
            labelWidth : 90,
            width : 160,
            value: '所有',
            store: store,
            listeners: {
                afterrender: function(){
                    this.store.owner = this;
                },
                expand: function(){
                    this._loaded = true;
                }
            }
        }
    },
});
}//非校级定义结束


/* 用户管理 */
Ext.define('bbt.UserManager', {
    extend : 'bbt.ManageGrid',
    alias : 'widget.bbt_usermanager',
    fields: ["role__name", "created_at", "permitted_groups", "remark", "email", "level", "mobile", "qq", "password", "password_confirmation", "role", "sex", "status", "username","realname",  "uuid"],
    listUrl: '/system/user/list/',
    removeUrl: '/system/user/delete/',
    updateUrl: '/system/user/edit/',
    addUrl: '/system/user/add/',
    showOperateColumn: false,
    checkPrivilegeOnAction: true,
    pagination: true,
    sorters: [{property: 'username', direction: 'ASC'}],
    columns : [{
        text : '用户名',
        dataIndex : 'username'
    }, {
        text: '所属角色',
        dataIndex: 'role__name'
    }, {
        text : '真实姓名',
        dataIndex : 'realname'
    }, {
        text : '性别',
        dataIndex : 'sex',
        renderer: function(v){ return {male: '男', female: '女'}[v];}
    }, {
        text : 'QQ',
        dataIndex : 'qq'
    }, {
        text : '手机',
        dataIndex : 'mobile'
    }, {
        text : '电子邮箱',
        dataIndex : 'email'
    }, {
        text: '状态',
        dataIndex: 'status',
        renderer: function(v){
            return {active:'激活',suspended: '停用'}[v];
        }
    }, {
        text : '备注',
        dataIndex : 'remark',
        flex : 1
    }],
    tbar : [{
        text : '添加用户',
        action: 'system_user_add',
        iconCls : 'tool-icon icon-user-add'
    }, {
        text : '编辑用户',
        action: 'system_user_edit',
        iconCls : 'tool-icon icon-user-edit'
    }, {
        text : '删除用户',
        action: 'system_user_delete',
        iconCls : 'tool-icon icon-user-delete'
    }, {
        text : '刷新',
        action: 'refresh',
        iconCls : 'tool-icon icon-refresh'
    }],
    actionMap: {system_user_add: 'addUser', system_user_edit: 'editUser', system_user_delete: 'deleteUser', refresh: 'refreshUser'},
    listeners: {
        show: function(){
            this.store.load();
        }
    },
    checkPassword: function(fm, name, name2) {
        if(arguments.length === 1) {
            name = 'password',
            name2 = 'password_confirmation';
        }
        fm.xtype === "form" && (fm = fm.getForm());
        var v1 = fm.findField(name).getValue();
        var v2 = fm.findField(name2).getValue();
        return v1 === v2;
    },
    addUser: function(){
        var me = this, config, win;
        config = Ext.apply(me.getUserWindowConfig(), {
            buttons: [{
                text : '保存',
                handler : function () {
                    var win = this.up('window'),
                        fm = win.down('form'),
                        tree, groups, vmsg, gpField;
                    vmsg = me.checkForm(fm);

                    if (vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    if(!me.checkPassword(fm)) {
                        Ext.Msg.alert('提示', '两次密码不一致！');
                        return;
                    }
                    //win.fixSelected();
                    tree = win.down('treepanel');
                    groups = me.getGroups(tree);
                    if(!groups/* || groups.indexOf(',')==-1*/) {
                        Ext.Msg.alert('提示', '管理范围必须选择', function(){
                            tree.up('fieldset').getEl().highlight("#F22", {duration: 2000});
                        });
                        return;
                    }

                    gpField = fm.getForm().findField('permitted_groups');
                    gpField.setValue(gpField.getValue() + ',' + groups);

                    me.request(me.addUrl, {form:fm}, {
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        },
                        maskId: me.createMask(win, '正在添加用户')
                    });
                }
            }, {
                text : '关闭',
                margin: '0 10 0 20',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });

        win = Ext.create('Ext.window.Window', config);

        win.show();

        setTimeout(function(){
            me.initUserWindowEvents(win, 'add');
        }, 1);
    },
    editUser: function(){
        var me = this, config, win, user, select, fm;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择用户！');
            return;
        }
        user = select[0];
        config = Ext.apply(this.getUserWindowConfig(), {
            buttons: [{
                text : '保存',
                handler : function () {
                    var win = this.up('window'),
                        fm = win.down('form'),
                        values, groups, vmsg, gpField;
                    vmsg = checkForm(fm);
                    if (vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    if(!checkPassword(fm)) {
                        Ext.Msg.alert('提示', '两次密码不一致！');
                        return;
                    }
                    tree = win.down('treepanel');
                    groups = me.getGroups(tree);
                    if(!groups/* || groups.indexOf(',')==-1*/) {
                        Ext.Msg.alert('提示', '管理范围必须选择', function(){
                            tree.up('fieldset').getEl().highlight("#F22", {duration: 2000});
                        });
                        return;
                    }

                    gpField = fm.getForm().findField('permitted_groups');
                    gpField.setValue(gpField.getValue() + ',' + groups);

                    me.request(me.updateUrl, {uuid: user.get('uuid'), form: fm}, {
                        maskId: me.createMask(win, '正在修改用户'),
                        success: function(data){
                            user.set(data.data);
                            user.commit();
                            win.destroy();
                        }
                    });
                }
            }, {
                text : '关闭',
                margin: '0 10 0 20',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });

        win = Ext.create('Ext.window.Window', config);

        me.getUserDetail(user.get('uuid'), function(userinfo){
            var userGroups={}, tree, fm;
            Ext.each(userinfo.permitted_groups, function(g){ userGroups[g.group__name]=''; });
            tree = win.down('treepanel');
            tree.userGroups = userGroups;
            tree.selectUserGroups && tree.selectUserGroups();
            win.show();
            fm = win.down('form').getForm();
            fm.setValues(userinfo.user);
            fm.findField('password').setValue('');
        });


        win.setTitle('编辑用户');

        this.initUserWindowEvents(win, 'edit');
    },
    deleteUser: function(){
        var me = this, config, win, user, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择用户！');
            return;
        }
        user = select[0];

        me.request(me.removeUrl, {uuid: user.raw.uuid}, {
            maskId: me.createMask(me, '正在删除用户'),
            success: function(){
                me.store.reload();
            }
        });
    },
    refreshUser: function(){
        this.store.reload();
    },
    initUserWindowEvents: function(win, type){
        var treepanel = win.down('treepanel'), storeCB;
        if(type == 'add') {
            win.down('textfield[name=password]').on('keyup', function(){
                var v = this.getValue(),
                    pv = this.up('form').down('textfield[name=password]').getValue();
                //假定用户是先输入密码，再输入确认密码的
                if(!pv) { return; }
                if(v != pv) {
                    this.markInvalid('密码与确认密码不一致');
                }
            });
            win.down('[name=password_confirmation]').on('keyup', function(){
                var v = this.getValue(),
                    pv = this.up('form').down('textfield[name=password]').getValue();
                if(v != pv) {
                    this.markInvalid('密码与确认密码不一致');
                }
            });
        } else if(type == 'edit') {
            win.down('combo[name=role]').allowBlank = true;
            win.down('textfield[name=password]').allowBlank = true;
            win.down('textfield[name=password_confirmation]').allowBlank = true;
        }
        if(!treepanel) { return; }
        Ext.apply(treepanel, {
            makeCurrentRoot: function(){
                var level = bbt.UserInfo.level,
                    root = this.getRootNode(),
                    node = root.getChildAt(0),
                    prevGroup = [];
                while(node.raw.group_type != level) {
                    prevGroup.push(node.raw.uuid);
                    node = node.getChildAt(0);
                }
                this.walk(node.childNodes, function(n){n.set('checked', false);});
                node.set('checked', true);
                this.setGroup(prevGroup, true);
                root.removeAll();
                root.appendChild(node);
                type == "edit" && this.selectUserGroups();
            },
            setGroup: function(obj, replace){
                if(Ext.isArray(obj)) {
                    obj = obj.join(',');
                }
                var ipt = this.up('window').down('hidden[name=permitted_groups]');
                if(ipt) {
                    if(replace) {
                        ipt.setValue(obj);
                    } else {
                        ipt.setValue(ipt.getValue()+','+obj);
                    }
                }
            },
            walk: function(node, fn){
                var me = this;
                if(!Ext.isArray(node)) { node = [node]; }
                Ext.each(node, function(_node){
                    fn(_node);
                    !_node.leaf && Ext.each(_node.childNodes, function(n){
                        me.walk(n, fn);
                    });
                });
            },
            selectUserGroups: function(){
                var ug = this.userGroups;
                if(!ug) { return; }
                this.walk(this.getRootNode(), function(node){
                    if(node.get('text') in ug) {
                        node.set('checked', true);
                    }
                });
            },
            filterNodes: function(nodes, level, groups){
                var cmp = this.compareLevel;
                level = level || bbt.UserInfo.level,
                groups = groups || {};
                this.walk(nodes, function(node){
                    switch(cmp(node.group_type, level)) {
                        case 1:
                            node.checked = null;
                            break;
                        case 0:
                            node.checked = (node.uuid in groups);
                            break;
                        case -1:
                            node.checked = (node.uuid in groups);
                            break;
                    }
                });
                return nodes;
            },
            closest: function(node, level){
                var p = node;
                while(p && p.raw.group_type !== level) {
                    p = p.parentNode;
                }
                return p;
            },
            unSelectNodes: function(node){
                if(node.get('checked')) {
                    node.set('checked', false);
                }
                var unSelect = arguments.callee;
                !node.get('leaf') && node.eachChild(unSelect);
            },
            selectNodesByLevel: function(root, level){
                var walk = function(node, fn){
                    fn(node);
                    !node.get('leaf') && node.eachChild(function(n){
                        walk(n, fn);
                    });
                }, nodes = [];
                walk(root, function(node){
                    if(node.raw.group_type === level) {
                        nodes.push(node);
                    }
                });
                return nodes;
            },
            selectParent: function(node){
                var p = node.parentNode;
                while(p) {
                    p.set('checked', true);
                    p = p.parentNode;
                }
            },
            hideParent: function(root, level){
                var nodes = this.selectNodesByLevel(root, level), i, len, p;
                for(i=0, len=nodes.length;i<len;i++) {
                    p = nodes[i].parentNode;
                    while(p) {
                        p.set('hidden', true);
                        p = p.parentNode;
                    }
                }
            },
            unSelectParent: function(root, level){
                var nodes = this.selectNodesByLevel(root, level), i, len, p;
                for(i=0, len=nodes.length;i<len;i++) {
                    p = nodes[i].parentNode;
                    while(p) {
                        p.set('checked', false);
                        p = p.parentNode;
                    }
                }
            },
            fixSelected: function(){
                var me = this, tree = me.down('treepanel'), nodes;
                if(!tree) { return; }
                nodes = me.selectNodesByLevel(tree.getRootNode(), bbt.UserInfo.level);
                Ext.each(nodes, function(node){
                    if(node.get('checked')) {
                        me.selectParent(node);
                        return false;
                    }
                });
            },
            compareLevel: function(level1, level2){
                var levels = ['province', 'city', 'country', 'town', 'school', 'grade'], index1, index2;
                index1 = Ext.Array.indexOf(levels, level1);
                index2 = Ext.Array.indexOf(levels, level2);
                if(!~index1 || !~index2) { return 1; }
                if(index1 < index2) { return 1; }
                else if(index1 === index2) { return 0; }
                else if(index1 > index2) { return -1; }
            }
        });
        storeCB = function(){
            treepanel.makeCurrentRoot();
            treepanel.store.un('load', storeCB);
        };
        if(treepanel.store.isLoading()) {
            treepanel.store.on('load', storeCB);
        } else {
            treepanel.makeCurrentRoot();
        }

        treepanel.on('checkchange', function(m, checked){
            var currentLevel = bbt.UserInfo.level;
            if(m.raw.group_type == currentLevel) {
                m.set('checked', true);
                return;
            }
            //如果被选中，选中所有祖先节点
            if(checked) {
                m.bubble(function(node){
                    node.set('checked', true);
                });
            }
            //sync child nodes status
            m.cascadeBy(function(node){
                node.set('checked', checked);
            });
        });

        var fields = win.down('form').getForm().getFields();
        fields.each(function(f){
            f.isValid() || f.reset();
        });
    },
    getUserWindowConfig: function(){
        var groupStore = new Ext.data.TreeStore({
            autoLoad: true,
            loading: true,
            listeners: {
                beforeload: function(me){
                    var cb = function(opts, _, resp){
                        var data, nodes, root;
                        try {
                            data = Ext.decode(resp.responseText);
                            if(data.status == "success") {
                                data.data.grade = [];
                                nodes = bbt.utils.parseGroupData(data.data);
                                root = me.getRootNode();
                                root.removeAll();
                                nodes = root.appendChild(nodes);
                                me.fireEvent('load', me);
                                me.loading = false;
                            }
                        } catch(e){}
                    };
                    Ext.Ajax.request({
                        url: '/group/',
                        callback: cb
                    });
                    return false;
                }
            }
        }), roleStore = new Ext.data.Store({
            fields: ['uuid', 'name'],
            autoLoad: true,
            proxy: {
                type: 'ajax',
                url: '/system/role/list/',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            },
            pageSize: 1000
        }), config;

        config = {
            width : 650,
            height: 380,
            modal: true,
            closable: false,
            resizable: false,
            title : '添加用户',
            layout: 'fit',
            items : [{
                    xtype: 'form',
                    bodyCls: 'no-bg',
                    border: false,
                    layout: {type: 'hbox', align: 'stretch', padding: 10},
                    items: [{
                        xtype : 'fieldset',
                        bodyCls : 'no-bg',
                        title : '用户信息',
                        flex: 2,
                        layout : {
                            type : 'vbox',
                            align : 'stretch'
                        },
                        items: [{
                            xtype: 'panel',
                            border: false,
                            bodyCls: 'no-bg',
                            layout: {type: 'hbox', align: 'stretch'},
                            defaults: {flex: 1, border: false, bodyCls: 'no-bg'},
                            defaultType: 'panel',
                            items: [{
                                margin : '0 2 0 0',
                                layout : {
                                    type : 'vbox',
                                    align : 'stretch'
                                },
                                defaultType : 'textfield',
                                defaults : {
                                    margin : '5 1',
                                    labelWidth : 60
                                },
                                items : [{
                                        fieldLabel : '用户名',
                                        maxLength: 20,
                                        name : 'username',
                                        allowBlank : false
                                    }, {
                                        fieldLabel : '真实姓名',
                                        maxLength: 100,
                                        name : 'realname'
                                    }, {
                                        fieldLabel : '登录密码',
                                        maxLength: 128,
                                        inputType : 'password',
                                        name : 'password',
                                        enableKeyEvents: true,
                                        allowBlank : false
                                    }, {
                                        fieldLabel : '手机',
                                        maxLength: 20,
                                        name : 'mobile'
                                    }, {
                                        fieldLabel : 'QQ',
                                        maxLength: 20,
                                        name : 'qq'
                                    }
                                ]
                            }, {
                                margin : '0 0 0 2',
                                layout : {
                                    type : 'vbox',
                                    align : 'stretch'
                                },
                                defaultType : 'textfield',
                                defaults : {
                                    margin : '5 1',
                                    labelWidth : 60
                                },
                                items : [{
                                        fieldLabel : '所属角色',
                                        name : 'role',
                                        allowBlank : false,
                                        editable: false,
                                        displayField: 'name',
                                        valueField: 'uuid',
                                        store: roleStore,
                                        queryMode: 'local',
                                        xtype: 'combo',
                                        listeners: {
                                            boxready: function(){
                                                var me = this, store = me.store, render, v = me.value;
                                                render = function(){
                                                    me.setValue(undefined);
                                                    me.setValue(v);
                                                    store.un('load', render);
                                                };
                                                if(v && store.isLoading()) {
                                                    store.on('load', render);
                                                }
                                            }
                                        }
                                    }, {
                                        fieldLabel : '性别',
                                        name : 'sex',
                                        maxLength: 20,
                                        value: 'male',
                                        store: [['male', '男'], ['female', '女']],
                                        editable: false,
                                        xtype: 'combo'
                                    }, {
                                        fieldLabel : '重复密码',
                                        inputType : 'password',
                                        name : 'password_confirmation',
                                        enableKeyEvents: true,
                                        maxLength: 128,
                                        allowBlank : false
                                    }, {
                                        fieldLabel: '电子邮箱',
                                        maxLength: 200,
                                        name: 'email'
                                    }, {
                                        fieldLabel: '状态',
                                        store: [['active', '激活'], ['suspended', '停用']],
                                        value: 'active',
                                        queryMode: 'local',
                                        name: 'status',
                                        editable: false,
                                        xtype: 'combo'
                                    }, {
                                        xtype: 'hidden',
                                        name: 'level',
                                        value: bbt.UserInfo.level
                                    }
                                ]
                            }]
                        }, {
                            margin : '8 0 0 0',
                            labelWidth : 60,
                            xtype : 'textareafield',
                            fieldLabel : '备注',
                            maxLength: 180,
                            name : 'remark'
                        }, {
                            xtype: 'hidden',
                            name: 'permitted_groups'
                        }]
                    }, {
                        xtype: 'fieldset',
                        title: '管理范围',
                        area: true,
                        flex: 1,
                        margin: '0 0 0 10',
                        layout: 'fit',
                        items: [{
                            xtype: 'treepanel',
                            autoScroll: true,
                            bodyCls: 'no-bg',
                            overflowY: 'auto',
                            rootVisible: false,
                            store: groupStore
                        }]
                    }]
                }
            ],
            buttonAlign : 'right'
        };
        return config;
    },
    getGroups: function(store) {
        var result = [], cb;
        cb = function(node){
            if(node.get('checked')) { result.push(node.raw.uuid); }
            if(!node.isLeaf()) { node.eachChild(cb); }
        };
        store.getRootNode().eachChild(cb);
        return result.join(',');
    },
    getUserDetail: function(uid, cb) {
        this.request('/system/user/detail/', {uuid: uid}, {
            method: 'GET',
            success: cb
        });
    },
    setGroups: function(store, data, cb) {
        var groups = {}, walkNodes, toNode;
        this.getGroupDetails(function(nodes){
            cb && cb(nodes, groups);
        });

        if(data.permitted_groups && data.permitted_groups.length) {
            //console.log(data.permitted_groups)
            Ext.each(data.permitted_groups, function(g){
                groups[g.group] = '';
            });
        }
    },
    _edit: function(user){
        var me = this, config, win, select, fm, remove;
        remove = function(selector) {
            var comp = typeof selector == "string" ? win.down(selector) : comp;
            if(comp) { comp.ownerCt.remove(comp); }
        };

        config = Ext.apply(this.getUserWindowConfig(), {
            buttons: [{
                text : '保存',
                handler : function () {
                    var win = this.up('window'),
                        fm = win.down('form'),
                        values, groups, vmsg;
                    vmsg = checkForm(fm);
                    if (vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    if(!checkPassword(fm)) {
                        Ext.Msg.alert('提示', '两次密码不一致！');
                        return;
                    }
                    apiRequest.target = win;
                    apiRequest.msg = '正在修改信息';
                    apiRequest('/update_details/', {id: user.get('uuid'), form: fm}, function(){
                        win.destroy();
                    });
                }
            }, {
                text : '关闭',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });

        win = Ext.create('Ext.window.Window', config);
        win.setTitle('用户信息');
        remove('[area]');
        remove('combo[name=status]');
        remove('combo[name=level]');
        win.down('textfield[name=username]').setReadOnly(true);
        win.down('combo[name=role]').setReadOnly(true);

        win.setWidth(Math.round(win.width * 0.67));
        fm = win.down('form').getForm();

        fm.getFields().each(function(f){
            f.allowBlank = true;
        });
        fm.setValues(user.data);
        fm.findField('password').setValue('');
        fm.findField('role').setValue(user.raw.role_name);
        this.initUserWindowEvents(win, 'edit');
        win.show();
    },
    statics: {
        editCurrentUser: function(){
            Ext.Ajax.request({
                url: '/details/',
                success: function(resp){
                    var data = Ext.decode(resp.responseText);
                    if(data.status == "success") {
                        var manager = new bbt.UserManager();
                        manager.store.removeAll();
                        manager.store.add(data.data);
                        manager._edit(manager.store.first());
                    }
                },
                failure: function(resp){
                    Ext.Msg.alert('提示', getErrorMsg(decodeResponse(resp)));
                }
            });
        }
    }
});

/* 角色管理 */
Ext.define('Privilege', {
    extend: 'Ext.data.Model',
    fields: ['name', 'key', 'privileges']
});
Ext.create('Ext.data.TreeStore', {
    storeId : 'PrivilegeTreeStore',
    model: 'Privilege',
    autoLoad: false,
    root : {
        text : '所有权限',
        expanded : true,
        children: [{text: 'loading', leaf: true}]
    },
    proxy: {
        url: '/privileges/',
        type: 'ajax',
        reader: {
            type: 'json',
            root: 'data'
        }
    },
    listeners: {
        load: function(store, node){
            var mod = function(n){
                if(n.get('checked') === null) { n.set('checked', false); }
                if(n.get('name')) { n.set('text', n.get('name')); }
                if(n.get('privileges')) {
                    n.appendChild(n.get('privileges'));
                    n.set('privileges', null);
                    n.set('leaf', false);
                } else {
                    n.set('leaf', true);
                }
                if(!n.isLeaf()) {
                    n.eachChild(mod);
                }
            };
            node.eachChild(mod);
        }
    }
});
Ext.define('bbt.RoleManager', {
    extend : 'bbt.ManageGrid',
    alias : 'widget.bbt_rolemanager',
    columns : [{
        text : '角色名称',
        dataIndex : 'name',
        width : 140
    }, {
        text : '备注',
        dataIndex : 'remark',
        flex : 9
    }],
    pagination: true,
    tbar : [{
        text : '添加角色',
        action: 'system_role_add',
        iconCls : 'tool-icon icon-user-add'
    }, {
        text : '编辑角色',
        action: 'system_role_edit',
        iconCls : 'tool-icon icon-user-edit'
    }, {
        text : '删除角色',
        action: 'system_role_delete',
        iconCls : 'tool-icon icon-user-delete'
    }, {
        text : '刷新',
        action: 'refresh',
        iconCls : 'tool-icon icon-refresh'
    }],
    fields: ['uuid', 'name', 'remark'],
    pagination: true,
    listUrl: '/system/role/list/',
    addUrl: '/system/role/add/',
    updateUrl: '/system/role/edit/',
    removeUrl: '/system/role/delete/',
    detailUrl: '/system/role/detail/',
    showOperateColumn: false,
    actionMap: {system_role_add: 'addRole', system_role_edit: 'editRole', system_role_delete: 'deleteRole', refresh: 'refreshRole'},
    listeners: {
        show: function(){ this.store.load(); }
    },
    addRole: function(){
        var me = this, config, win;
        config = Ext.apply(this.getRoleWindowConfig(), {
            buttons: [{
                text : '保存',
                handler : function () {
                    var win = this.up('window'),
                        fm = win.down('form'),
                        values, vmsg;
                    vmsg = checkForm(fm);
                    if (vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    fm.getForm().findField('privileges').setValue(me.getPrivileges(win.down('treepanel').store));

                    me.request(me.addUrl, {form: fm}, {
                        maskId: me.createMask(win, '正在添加角色'),
                        success: function(data){
                            me.store.reload();
                            win.destroy();
                        }
                    });
                }
            }, {
                text : '关闭',
                margin: '0 10 0 20',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });
        win = Ext.create('Ext.window.Window', config);
        this.initRoleWindowEvents(win);
        win.show();
    },
    editRole: function(){
        var me = this, config, win, role, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择角色！');
            return;
        }
        role = select[0];
        config = Ext.apply(this.getRoleWindowConfig(), {
            buttons: [{
                text : '保存',
                handler : function () {
                    var win = this.up('window'),
                        fm = win.down('form'),
                        values, vmsg;
                    vmsg = checkForm(fm);
                    if (vmsg !== true) {
                        //Ext.Msg.alert('提示', vmsg);
                        return;
                    }
                    fm.getForm().findField('privileges').setValue(me.getPrivileges(win.down('treepanel').store));

                    me.request(me.updateUrl, {uuid:role.get('uuid'),form: fm}, {
                        maskId: me.createMask(win, '正在修改角色'),
                        success: function(data){
                            role.set(data.data);
                            role.commit();
                            win.destroy();
                        }
                    });
                }
            }, {
                text : '关闭',
                margin: '0 10 0 20',
                handler : function () {
                    this.up('window').destroy();
                }
            }]
        });
        win = Ext.create('Ext.window.Window', config);

        win.setTitle('编辑角色');
        win.down('form').getForm().setValues(role.data);
        this.initRoleWindowEvents(win);
        win.show();
        me.request(me.detailUrl, {uuid: role.get('uuid')}, {
            method: 'GET',
            success: function(data){
                var tree = win.down('treepanel');
                tree.myPrivileges = data.privilege;
                tree.allPrivileges && tree.markPrivileges();
            }
        });
    },
    refreshRole: function(){
        this.store.reload();
    },
    deleteRole: function(){
        var me = this, config, win, role, select;
        select = me.getSelectionModel().getSelection();
        if(!select.length) {
            Ext.Msg.alert('提示', '请先选择角色！');
            return;
        }
        role = select[0];

        me.request(me.removeUrl, {uuid:role.get('uuid')}, {
            maskId: me.createMask(me, '正在删除角色'),
            success: function(){
                me.store.reload();
            }
        });
    },
    getRoleWindowConfig: function(){
        var config = {
            width : 570,
            closable: false,
            modal: true,
            title : '添加角色',
            items : [{
                    xtype : 'form',
                    height: 250,
                    padding : 10,
                    bodyCls : 'no-bg',
                    border : false,
                    layout : {
                        type : 'hbox',
                        align : 'stretch'
                    },
                    items : [{
                            xtype : 'fieldset',
                            flex : 4,
                            bodyCls : 'no-bg',
                            title : '角色基本信息',
                            layout : {
                                type : 'vbox',
                                align : 'stretch'
                            },
                            defaults : {
                                labelWidth : 80
                            },
                            items : [{
                                    xtype : 'textfield',
                                    fieldLabel : '角色名称',
                                    maxLength: 100,
                                    name : 'name',
                                    allowBlank: false
                                }, {
                                    margin : '8 0 0 0',
                                    flex : 9,
                                    xtype : 'textareafield',
                                    maxLength: 180,
                                    fieldLabel : '备注',
                                    name : 'remark'
                                }, {
                                    xtype: 'hidden',
                                    name: 'privileges'
                                }
                            ]
                        }, {
                            xtype : 'fieldset',
                            bodyCls : 'no-bg',
                            margin: '0 0 0 10',
                            title : '角色权限',
                            layout: 'fit',
                            flex:4,
                            items : [{
                                    xtype : 'treepanel',
                                    bodyCls: 'no-bg',
                                    overflowY: 'auto',
                                    rootVisible: false,
                                    store : 'PrivilegeTreeStore',
                                    myPrivileges: null,
                                    allPrivileges: null,
                                    markPrivileges: function(){
                                        var myPS = {}, nodes = this.allPrivileges;
                                        Ext.each(this.myPrivileges, function(p){
                                            myPS[p.privilege] = '';
                                        });
                                        walk = function(node){
                                            if(node.get('key') in myPS) {
                                                node.set('checked', true);
                                            }
                                            node.eachChild(walk);
                                        };
                                        Ext.each(nodes, walk);
                                    },
                                    listeners: {
                                        afterrender: function(){
                                            var me = this;
                                            this.store.reload({
                                                callback: function(nodes){
                                                    me.allPrivileges = nodes;
                                                    if(me.myPrivileges) {
                                                        me.markPrivileges();
                                                    }
                                                }
                                            });
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ],
            buttonAlign : 'right'
        };
        return config;
    },
    initRoleWindowEvents: function(win, type) {
        var tree = win.down('treepanel');
        tree.on('checkchange', function(m, checked){
            if(checked) {
                m.bubble(function(node){
                    node.set('checked', true);
                });
            }
            m.cascadeBy(function(node){
                node.set('checked', checked);
            });
        });
        tree.on('afterrender', function(){
            var reset = function(node){
                node.set('checked', false);
                if(!node.isLeaf()) {
                    node.eachChild(reset);
                }
            };
            this.store.getRootNode().eachChild(reset);
        });
    },
    getPrivileges: function(store){
        var result = [], cb;
        cb = function(node){
            if(node.get('checked')) { result.push(node.get('key')); }
            if(!node.isLeaf()) { node.eachChild(cb); }
        };
        store.getRootNode().eachChild(cb);
        result = result.join(',');
        if(result.indexOf('general_statistic') === -1) {
            result += ',general_statistic';
        }
        return result;
    },
    getRoleDetail: function(role, win, cb) {
        bbt.request('/system/role/detail/', {uuid: role.get('uuid')}, cb);
    },
    setPrivileges: function(store, data) {
        var myPS={}, mod, NO = 'no', YES = 'yes';
        Ext.each(data, function(k){
            myPS[k] = '';
        });
        //console.log('my privileges:', data);
        mod = function(node){
            var select = 0, total = 0;
            if(node.get('key') in myPS) {
                if(node.isLeaf()) { node.set('checked', true); return YES; }
            } else { return NO; }
            //所有子节点都选中时，选中父节点
            node.eachChild(function(n){
                if(YES === mod(n)) { select++; }
                total++;
            });
            if(select === total) { node.set('checked', true); return YES; }
            else { return NO; }
        };
        store.getRootNode().eachChild(mod);
    }
});

/* 上级服务器设置 */
Ext.define('bbt.SystemSettings', {
    extend: 'Ext.window.Window',
    alias: 'widget.bbt_setting',
    getDetails: function(){
        var win = this;
        apiRequest.msg = '正在修改系统设置';
        apiRequest.target = win;
        apiRequest('/system/sync_server/list/', {}, function(data){
            var form = win.down('form').getForm();
            Ext.each(data.data, function(v){
                var f = form.findField(v.name.replace('sync_server_', ''));
                f && f.setValue(v.value);
            });
        });
    },
    initComponent: function(){
        Ext.apply(this, this.getPopConfig());
        this.callParent();
        this.show();
        this.getDetails();
    },
    getPopConfig: function(){
        var config = {
            title: '上级服务器设置',
            resizable: false,
            closable: false,
            modal: true,
            width: 450,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls: 'no-bg',
                layout: {type: 'vbox', align: 'center', pack: 'center'},
                defaultType: 'textfield',
                defaults: {width: 320},
                border: false,
                items: [{
                    fieldLabel: 'IP/域名',
                    name: 'host',
                    margin: '40 0 0 0',
                    validator: function(v){
                        var re = /(([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-z_!~*\'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6})/i;
                        if(re.test(v)) {
                            return true;
                        }
                        return "无效的IP/域名";
                    }
                }, {
                    margin: '10 0',
                    fieldLabel: '端口号',
                    name: 'port',
                    value: bbt.UserInfo.level == "country" ? "8000" : "",
                    emptyText: '不可为空',
                    allowBlank: false,
                    validator: function(v){
                        var valid = /^\d+$/.test(v);
                        if(!v) { return "端口号不可为空！"; }
                        if(valid) {
                            v = parseInt(v);
                            return (v >= 0 && v <= 65535) ? true : msg;
                        }
                        return '错误的端口号！';
                    }
                }, {
                    fieldLabel: '密钥',
                    name: 'key',
                    invalidText: '只能填写16位数字或大写字母ABCDEF',
                    margin: '0 0 40 0',
                    allowBlank: false,
                    regex: /^[0-9A-F]{16}$/
                }]
            }],
            buttonAlign: 'center',
            buttons: [{
                xtype: 'button',
                text: '确定',
                margin: '0 10 10 10',
                handler: function(){
                    var win = this.up('window'), fm = win.down('form'), msg;
                    msg = checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    fm = fm.getForm();
                    fm.waitTarget = win;
                    fm.submit({
                        url: '/system/sync_server/add/',
                        waitMsg: '正在提交数据……',
                        success: function(form, action){
                            var data = action.result;
                            data.msg && Ext.Msg.alert('提示', data.msg, function(){
                                win.destroy();
                            });
                        },
                        failure: function(form, action){
                            var msg = action.result.msg;
                            Ext.Msg.alert('提示', msg, function(){
                                win.destroy();
                            });
                        }
                    });
                }
            }, {
                xtype: 'button',
                margin: '0 10 10 10',
                text: '关闭',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        };
        return config;
    }
});

/* 桌面预览设置 */
Ext.define('bbt.DesktopPreviewSettings', {
    extend: 'Ext.window.Window',
    alias: 'widget.preview_settings',
    getDetails: function(){
        var win = this;
        apiRequest.msg = 'loading ...';
        apiRequest.target = win;
        apiRequest('/system/desktop-preview/get/', {}, function(data){
            var form = win.down('form').getForm();
            Ext.each(data.data.records, function(v){
                var f = form.findField(v.name);
                if(f && v.value){
                    f.setValue(v.value);
                }
            });
        });
    },
    initComponent: function(){
        Ext.apply(this, this.getPopConfig());
        this.callParent();
        this.show();
        this.getDetails();
    },
    getPopConfig: function(){
        var config = {
            title: '桌面预览设置',
            resizable: false,
            closable: false,
            modal: true,
            width: 400,
            layout: 'fit',
            items: [{
                xtype: 'form',
                margin: 20,
                layout: 'anchor',
                bodyCls: 'no-bg',
                border: false,
                items: [{
                    xtype: 'fieldset',
                    title: '通用',
                    defaults: {anchor: '100%', labelWidth: 140},
                    items: [{
                        xtype: 'combo',
                        name: 'cloud-service-provider',
                        fieldLabel: '云存储服务商',
                        store: ['upyun'],
                        value: 'upyun',
                        editable: false
                    }, {
                        xtype: 'textfield',
                        name: 'cloud-service-username',
                        fieldLabel: '云存储用户名',
                        maxLength: 100,
                        allowBlank: false,
                        enableKeyEvents: true,
                        listeners: {
                            keydown: function(){
                                if(this._fired) { return; }
                                var pwd = this.ownerCt.down('[name=cloud-service-password]');
                                pwd.setValue('');
                                this._fired = true;
                            }
                        }
                    }, {
                        xtype: 'textfield',
                        name: 'cloud-service-password',
                        inputType: 'password',
                        fieldLabel: '云存储密码',
                        maxLength: 100,
                        allowBlank: false
                    }]
                }, {
                    xtype: 'fieldset',
                    title: '学校终端',
                    defaults: {anchor: '100%', labelWidth: 140},
                    items: [{
                        xtype: 'numberfield',
                        name: 'desktop-preview-interval',
                        fieldLabel: '截屏时间间隔（分钟）',
                        value: 5,
                        minValue: 5,
                        maxValue: 10,
                        editable: false
                    }, {
                        xtype: 'numberfield',
                        name: 'desktop-preview-days-to-keep',
                        fieldLabel: '记录保存时间（天）',
                        value: 150,
                        minValue: 10,
                        maxValue: 150,
                        editable: false
                    }]
                }, {
                    xtype: 'fieldset',
                    title: '教学点终端',
                    defaults: {anchor: '100%', labelWidth: 140},
                    items: [{
                        xtype: 'numberfield',
                        name: 'desktop-preview-interval-edu-unit',
                        fieldLabel: '截屏时间间隔（分钟）',
                        value: 10,
                        minValue: 10,
                        maxValue: 20,
                        editable: false
                    }, {
                        xtype: 'numberfield',
                        name: 'desktop-preview-days-to-keep-edu-unit',
                        fieldLabel: '记录保存时间（天）',
                        value: 150,
                        minValue: 10,
                        maxValue: 150,
                        editable: false
                    }]
                }]
            }],
            buttonAlign: 'center',
            buttons: [/*{
                xtype: 'button',
                text: '连接并验证',
                handler: function(){
                    var win = this.up('window'), fm = win.down('form'), msg;
                    msg = checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    fm = fm.getForm();
                    fm.waitTarget = win;
                    
                }
            }, */{
                xtype: 'button',
                text: '确定',
                margin: '0 10 10 10',
                handler: function(){
                    var win = this.up('window'), fm = win.down('form'), msg, verify, submit;
                    msg = checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    fm = fm.getForm();
                    fm.waitTarget = win;
                    
                    verify = function(){
                        fm.submit({
                            url: '/system/desktop-preview/verify/',
                            waitMsg: '正在提交数据……',
                            success: function(form, action){
                                var data = action.result;
                                if(data.status == "success") {
                                    submit();
                                }
                            },
                            failure: function(form, action){
                                Ext.Msg.alert('提示', action.result.msg);
                            }
                        });
                    };
                    submit = function(){
                        fm.submit({
                            url: '/system/desktop-preview/set/',
                            waitMsg: '正在提交数据……',
                            success: function(form, action){
                                var data = action.result;
                                if(data.status == "success") {
                                    Ext.Msg.alert('提示', data.msg, function(){
                                        win.destroy();
                                    });
                                }
                            }
                        });
                    };
                    verify();
                }
            }, {
                xtype: 'button',
                margin: '0 10 10 10',
                text: '关闭',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        };
        return config;
    }
});

/* 校级服务器设置<县级服务器同样适用> */
Ext.define('bbt.SchoolSettings', {
    extend: 'Ext.window.Window',
    alias: 'widget.school_setting',
    getDetails: function(){
        var win = this;
        apiRequest.msg = 'loading ...';
        apiRequest.target = win;
        apiRequest('/system/school-server-setting/get/', {}, function(data){
            var form = win.down('form').getForm();
            form.findField('host').setValue(data.data.host);
            form.findField('port').setValue(data.data.port);
            form.findField('show_download_btn').setValue(data.data.show_download_btn);
        });
    },
    initComponent: function(){
        Ext.apply(this, this.getPopConfig());
        this.callParent();
        this.show();
        this.getDetails();
    },
    getPopConfig: function(){
        var config = {
            title: this.title.split(' ').pop(),
            resizable: false,
            closable: false,
            modal: true,
            width: 450,
            layout: 'fit',
            items: [{
                xtype: 'form',
                bodyCls: 'no-bg',
                layout: {type: 'vbox', align: 'center', pack: 'center'},
                defaultType: 'textfield',
                defaults: {width: 320},
                border: false,
                items: [{
                    fieldLabel: 'IP/域名',
                    name: 'host',
                    margin: /*bbt.UserInfo.isSchool() ? '40 0 0 0' : */'30 0 30 0',
                    validator: function(v){
                        var re = /(([0-9]{1,3}\.){3}[0-9]{1,3}|([0-9a-z_!~*\'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6})/i;
                        if(re.test(v)) {
                            return true;
                        }
                        return "无效的IP/域名";
                    }
                }, {
                    hidden: true,
                    margin: '10 0 40 0',
                    fieldLabel: '端口号',
                    name: 'port',
                    emptyText: '不可为空',
                    allowBlank: false,
                    //hidden: !bbt.UserInfo.isSchool(),
                    validator: function(v){
                        var valid = /^[1-9]\d+$/.test(v), msg;
                        if(!v) { return "端口号不可为空！"; }
                        msg = '错误的端口号！';
                        if(valid) {
                            v = parseInt(v);
                            return (v > 0 && v <= 65535) ? true : msg;
                        }
                        return msg;
                    }
                }, {
                    xtype: 'checkbox',
                    hidden: bbt.UserInfo.isSchool(),
                    margin: '-20 0 40 0',
                    boxLabel: '显示教学点终端下载按钮',
                    name: 'show_download_btn',
                    emptyText: '不可为空',
                    inputValue: true,
                    allowBlank: false
                }]
            }],
            buttonAlign: 'center',
            buttons: [{
                xtype: 'button',
                text: '确定',
                margin: '0 10 10 10',
                handler: function(){
                    var win = this.up('window'), fm = win.down('form'), msg;
                    msg = checkForm(fm);
                    if(msg !== true) {
                        //Ext.Msg.alert('提示', msg);
                        return;
                    }
                    fm = fm.getForm();
                    fm.waitTarget = win;
                    fm.submit({
                        url: '/system/school-server-setting/set/',
                        waitMsg: '正在提交数据……',
                        success: function(form, action){
                            var data = action.result;
                            data.msg && Ext.Msg.alert('提示', data.msg, function(){
                                win.destroy();
                            });
                        },
                        failure: function(form, action){
                            var msg = action.result.msg;
                            Ext.Msg.alert('提示', msg, function(){
                                win.destroy();
                            });
                        }
                    });
                }
            }, {
                xtype: 'button',
                margin: '0 10 10 10',
                text: '关闭',
                handler: function(){
                    this.up('window').destroy();
                }
            }]
        };
        return config;
    }
});
/* 资产管理 */
Ext.define('bbt.AssetView', {
    extend: 'Ext.view.View',
    alias: 'widget.assetview',
    itemMaxWidth: 340,
    itemMaxHeight: 225,
    itemMaxImage: 128,
    itemMinWidth: 165,
    itemMinHeight: 109,
    itemMinImage: 64,
    MaxMode: 'max',
    MinMode: 'min',
    mode: 'A',
    isSchool: bbt.UserInfo.isSchool(),
    constructor: function(){
        var store = Ext.create('Ext.data.Store', {
            fields: ['uuid', 'name', 'icon', 'unit_name', 'unit_count'],
            proxy: {
                url: this.isSchool ? '/asset/asset-type/' : '/asset/asset-type/aggregate/',
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            },
            pageSize: 100
        }), loadcb;
        /*@remote asset type
        if(this.isSchool) {
            loadcb = function(){ this.add({icon: 'add', name: '添加新类型'}); };
            store.on('load', loadcb);
        }*/
        store.load();
        this.store = store;
        if(this.displayMode != this.MinMode) {
            this.displayMode = this.MaxMode;
        }

        this.addEvents('assetpici', 'assetaddreport', 'assetstop', 'assettypeadd');
        this.listeners = {
            afterrender: function(){
                var ele = this.getEl();
                ele.on('mouseover', function(e){
                    Ext.get(e.target).addCls(['x-over', 'x-btn-over', 'x-btn-default-small-over']);
                }, undefined, {delegate: 'a.x-btn[action]'});
                ele.on('mouseout', function(e){
                    Ext.get(e.target).removeCls(['x-over', 'x-btn-over', 'x-btn-default-small-over']);
                }, undefined, {delegate: 'a.x-btn[action]'});
            }/*,
            itemmouseenter: function(v, rc, ele, i, e){
                if(v.isEditing(ele)) { return; }
                var image = Ext.get(ele).down('img'), anim, toData = {}, tmp,
                    isMax = v.displayMode === v.MaxMode;
                if(isMax) {
                    tmp = v.itemMaxImage * 1.2;
                    toData.width = toData.height = tmp + 'px';
                    toData.marginTop = (v.itemMaxHeight - tmp) / 2 + 'px';
                } else {
                    tmp = v.itemMinImage * 1.2;
                    toData.width = toData.height = tmp + 'px';
                    toData.marginTop = (v.itemMinHeight - tmp) / 2 + 'px';
                }
                anim = v.animateData[image.id];
                if(anim) { anim.end(); }
                v.animateData[image.id] = Ext.create('Ext.fx.Anim', {
                    target: image,
                    duration: 400,
                    delay: 20,
                    to: toData
                });
                Ext.get(ele).addCls('hover');
            },
            itemmouseleave: function(v, rc, ele, i, e){
                if(v.isEditing(ele)) { return; }
                var image = Ext.get(ele).down('img'), anim, toData = {}, tmp,
                    isMax = v.displayMode === v.MaxMode;
                if(isMax) {
                    tmp = v.itemMaxImage;
                    toData.width = toData.height = tmp + 'px';
                    toData.marginTop = (v.itemMaxHeight - tmp) / 2 + 'px';
                } else {
                    tmp = v.itemMinImage;
                    toData.width = toData.height = tmp + 'px';
                    toData.marginTop = (v.itemMinHeight - tmp) / 2 + 'px';
                }
                anim = v.animateData[image.id];
                if(anim) { anim.end(); }
                v.animateData[image.id] = Ext.create('Ext.fx.Anim', {
                    target: image,
                    duration: 400,
                    delay: 20,
                    to: toData
                });
                Ext.get(ele).removeCls('hover');
            }*/
        };



        if(this.displayMode === this.MaxMode) {
            this.cls = 'big-view';
        } else {
            this.cls = 'small-view';
        }
        if(!this.isSchool) {
            this.cls += ' not-school';
            this.listeners.itemclick = function(v, rc, ele, i, e){
                var t = Ext.get(e.target);

                if(t.is('a[action]')) {
                    switch(t.getAttribute('action')) {
                        case 'pici':
                            v.fireEvent('assetpici', v, rc, i);
                            break;
                    }
                }
            };
        } else {
            this.listeners.itemclick = function(v, rc, ele, i, e){
                var t = Ext.get(e.target);

                if(t.is('a[action]')) {
                    switch(t.getAttribute('action')||t.dom.getAttribute('action')) {
                        case 'pici':
                            v.fireEvent('assetpici', v, rc, i);
                            break;
                        case 'add':
                            v.fireEvent('assetaddreport', v, rc, i);
                            break;
                        case 'stop':
                            v.fireEvent('assetstop', v, rc, i);
                            break;
                    }
                }
                /*@remote asset type
                else if(Ext.get(ele).is('.empty-asset-item')) {
                    v.fireEvent('assettypeadd');
                }*/
            };
        }
        this.callParent();
    },
    animateData: {},
    prepareData: function(data, index, record){
        var isMax = this.displayMode === this.MaxMode;
        if(isMax) {
            data.itemWidth = this.itemMaxWidth;
            data.itemHeight = this.itemMaxHeight;
            data.itemImageSize = this.itemMaxImage;
            data.assetCls = "icon-" + data.icon + "128";
        } else {
            data.itemWidth = this.itemMinWidth;
            data.itemHeight = this.itemMinHeight;
            data.itemImageSize = this.itemMinImage;
            data.assetCls = "icon-" + data.icon + "64";
        }

        if(typeof data.unit_count != "number") {
            data.unit_count = 0;
        }
        if(data.name != "添加新类型") {
            data.emptyCls = '';
            data.isItem = true;
        } else {
            data.emptyCls = 'empty-asset-item';
        }
        data.itemImageMarginTop = (data.itemHeight - data.itemImageSize) / 2;
        data.mode = this.mode;
        return data;
    },
    showBigIcon: function(){
        this.displayMode = this.MaxMode;
        this.mode = 'A';
        this.refresh();
        this.removeCls('small-view');
        this.addCls('big-view');
    },
    showSmallIcon: function(){
        this.displayMode = this.MinMode;
        this.mode = 'a';
        this.refresh();
        this.removeCls('big-view');
        this.addCls('small-view');
    },
    toggleIcon: function(){
        if(this.displayMode == this.MaxMode) {
            this.showSmallIcon();
        } else {
            this.showBigIcon();
        }
    },
    showRemoveLayer: function(){
        var me = this;
        Ext.each(me.getEl().query(me.itemSelector), function(item){
            var model = me.getRecord(item), removeLink;
            if(model.raw.cannot_delete === true) { return; }
            if(Ext.get(item).is('.empty-asset-item')) { return; }
            removeLink = document.createElement('a');
            removeLink.className = 'remove-trigger';
            Ext.get(item).insertFirst(removeLink);
            Ext.get(removeLink).on('click', function(){
                var el = Ext.get(this), item = el.up('div.asset-item'), rc;
                rc = me.getRecord(item);
                me.fireEvent('assettyperemove', me, rc);
            });
        });
    },
    isEditing: function(item){
        try {
            return Ext.get(item).query('.remove-trigger').length > 0;
        } catch (e) {
            return false;
        }
    },
    itemSelector: 'div.asset-item',
    tpl: ['<div class="asset-view">',
        '<div class="asset-view-inner">',
        '<tpl for=".">',
            '<div class="asset-item {emptyCls}" style="width:{itemWidth}px;height:{itemHeight}px;">',
                '<div class="item-icon">',
                    '<span class="{assetCls}" style="margin-top:{itemImageMarginTop}px;height:{itemImageSize}px;width:{itemImageSize}px"></span>',
                '</div>',
                '<div class="item-details">',
                    '<p><strong>{name}</strong></p>',
                    '<tpl if="isItem">',
                    '<p class="single"><strong>{unit_count} {unit_name}</strong></p>',
                    '<p class="pici"><a href="javascript:void(0);" action="pici">批次详情</a></p>',
                    '<p><a action="add" class="x-btn x-btn-default-small add-btn">新增{[values.mode=="A"?"申报":""]}</><a action="stop" class="x-btn x-btn-default-small">停用{[values.mode=="A"?"申报":""]}</a></p>',
                    '</tpl>',
                '</div>',
            '</div>',
        '</tpl>',
        '<div style="clear:both;"></div>',
        '</div></div>']
});
Ext.define('bbt.AssetManager', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.assetmgr',
    exportUrl: '/asset/asset-type/export/',
    isSchool: bbt.UserInfo.isSchool(),
    initComponent: function(){
        var tbar = [{
            xtype: 'combo',
            action: 'displayStyle',
            name: '_',
            editable: false,
            value: 'big',
            store: [['big', '大图标'], ['small', '小图标']]
        }];
        if(!this.isSchool) {
            this.title = '资产管理 > 资产统计';
            tbar.unshift(bbt.ToolBox.get('school'));
            tbar.unshift(bbt.ToolBox.get('town'));
            if(bbt.UserInfo.level == "city") {
                tbar.unshift(bbt.ToolBox.get('country'));
            }
            tbar.push({
                xtype: 'button',
                text: '查询',
                iconCls: 'icon-query',
                handler: function(){
                    var fields = this.up('toolbar').query('field'), params = {};
                    Ext.each(fields, function(f){
                        var rc;
                        if(f.name == '_') { return; }
                        if(f.submitField) {
                            rc = f.findRecordByValue(f.getValue());
                            params[f.name] = rc.get(f.submitField);
                        } else {
                            params[f.name] = f.getValue();
                        }
                        if(params[f.name] == "所有") {
                            params[f.name] = "";
                        }
                    });
                    this.up('assetmgr').getView().store.reload({params: params});
                }
            });
        } else {
            /*tbar.push({
                text: '编辑',
                action: 'edit',
                iconCls: 'tool-icon icon-edit'
            });*/
        }
        tbar.push('->');
        tbar.push({
            xtype: 'button',
            action: 'export',
            iconCls: 'tool-icon icon-export',
            text: '报表导出'
        });
        Ext.apply(this, {
            bodyStyle: {overflow: 'auto'},
            tbar: tbar,
            items: [{xtype: 'assetview', border: false}],
            listeners: {
                afterrender: function(){
                    var tb = this.down('toolbar[dock=top]'), p = this;
                    tb.down('combo[action=displayStyle]').on('change', function(me, v){
                        p.getView().toggleIcon();
                    });
                    /*this.isSchool && tb.down('button[action=edit]').on('click', function(me){
                        if(me.removing) {
                            p.getView().refresh();
                            me.setText('编辑');
                            me.removing = false;
                        } else {
                            p.getView().showRemoveLayer();
                            me.removing = true;
                            me.setText('取消编辑');
                        }

                    });*/
                    tb.down('button[action=export]').setHandler(p.doExport, p);
                },
                boxready: function(){
                    if(!this.isSchool) {
                        Ext.each(this.down('toolbar').query('combo'), function(combo){
                            if(combo.name == '_') { return; }
                            combo.setValue('');
                        });
                    }
                }
            }
        });
        this.callParent();
        bbt.autoArea(this);
    },
    saveAreaStatus: function(){
        var values = [], tb = this.down('toolbar[dock=top]');
        Ext.each(['province', 'city', 'country', 'town', 'school'], function(v){
            var combo = tb.down('combo[name=' + v + '_name]');
            if(combo) {
                values.push([combo.name, combo.getValue()]);
            }
        });
        this._area_values = values;
    },
    recoveryAreaStatus: function(){
        var tb = this.down('toolbar[dock=top]'),
            values = this._area_values;
        if(!values) { return; }
        Ext.each(values, function(v){
            var c = tb.down('combo[name=' + v[0] + ']');
            console.log("before value: " + c.getValue());
            c.setValue(v[1]);
            console.log("after value: " + c.getValue());
        });
        delete this._area_values;
    },
    doExport: function(){
        var me = this, store = me.getView().store;
        Ext.Ajax.request({
            url: me.exportUrl,
            params: store.lastOptions.params,
            success: function(resp){
                try {
                    var data = Ext.decode(resp.responseText);
                    downloadFile(data.url, '');
                } catch(e) {
                    Ext.Msg.alert('提示', '服务器错误！');
                }
            },
            failure: function(){}
        });
    },
    initEvents: function(){
        var me = this, view = me.getView();
        view.on({
            assetpici: function(v, rc, i){
                var pc = new bbt.AssetPCi({title: rc.get('name')+' - 批次详情',showOperateColumn: false, assetType: rc});
                me.saveAreaStatus();
                pc.__parent = me;
                pc.show();
            },
            assetaddreport: function(v, rc, i){
                var ast = new bbt.ReportAsset(), typeCombo;
                typeCombo = ast.down('combo[name=asset_type]');
                typeCombo.store = v.store;
                typeCombo.setValue(rc.raw.uuid);
                typeCombo.setReadOnly(true);
                ast.assetTypeModel = rc;
                ast.show();
            },
            assetstop: function(v, rc, i){
                var pc = new bbt.AssetPCi({title: rc.get('name')+' - 详情',showOperateColumn: true, assetType: rc});
                me.saveAreaStatus();
                pc.__parent = me;
                pc.show();
            },
            assettypeadd: function(){
                var win = new bbt.NewAsset();
                win.assetManager = me;
                win.show();
            },
            assettyperemove: function(view, model){
                return me.removeAssetType(view, model);
            }
        });
    },
    getView: function(){
        return this.items.get(0);
    },
    removeAssetType: function(view, model){
        Ext.Ajax.request({
            url: '/asset/asset_type/delete/',
            params: {uuid: model.get('uuid')},
            method: 'POST',
            callback: function(opts, flag, resp){
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    view.store.remove(model);
                } else {
                    Ext.Msg.alert('提示', data.msg);
                }
            }
        });
    }
});
Ext.define('bbt.AssetPCi', {
    extend: 'Ext.window.Window',
    alias: 'widget.asset_pci',
    initComponent: function(){
        var eParams, grid, lastCol;
        if(bbt.UserInfo.isSchool()) {
            eParams = {asset_type_uuid: this.assetType.get('uuid')};
        } else {
            eParams = Ext.apply(this._get_other_level_params(), this.assetType.store.lastOptions.params);
        }
        grid = {
            xtype: 'mgrgridbase',
            listUrl: bbt.UserInfo.isSchool() ? '/asset/' : '/asset/aggregate/',
            proxy: {
                type: 'ajax',
                url: bbt.UserInfo.isSchool() ? '/asset/' : '/asset/aggregate/',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                },
                extraParams:  eParams,
                startParam: undefined
            },
            pageSize: 15,
            assetType: this.assetType,
            pagination: true,
            border: false,
            fields: ['reported_at', 'status', 'asset_from', 'device_model', 'number', 'reported_by', 'remark', 'asset_type__name', 'asset_type__school__parent__name', 'asset_type__school__name', 'asset_type__school__parent__parent__name'],
            listeners: {
                show: function(){
                    var params = this.store.proxy.extraParams, tb;
                    tb = this.down('toolbar[dock=top]');
                    if(!params) {
                        params = {};
                    }
                    //如果不显示操作列，则当前表格是批次详情，默认使用在用状态
                    if(!this.showOperateColumn) {
                        params['status'] = '在用';
                    } else {
                        params['status'] = '';
                        tb.down('combo[name=status]').setValue('');
                    }
                    this.store.on('beforeload', function(s){
                        s.proxy.extraParams.page = s.currentPage;
                    });
                    this.store.load({params: params});
                    
                    Ext.each('school town country city'.split(' '), function(level){
                        var combo = tb.down('combo[name=' + level + '_name]');
                        if(combo) {
                            !combo.value && combo.setValue('');
                        }
                    });
                }
            },
            columns: [{
                text: '申报时间',
                dataIndex: 'reported_at',
                width: 150,
                renderer: function(v){ return v ? v.replace('T', ' '): '';}
            }, {
                text: '资产状态',
                dataIndex: 'status',
                width: 60,
                hidden: this.showOperateColumn
            }, /*{
                text: '资产类型',
                dataIndex: 'asset_type__name'
            }, */{
                text: '设备型号',
                dataIndex: 'device_model'
            }, {
                text: '数量',
                width: 100,
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
                flex: 1,
                dataIndex: 'remark'
            }],
            tbar: bbt.ToolBox.convert(['year', 'assetStatus', 'report_user', 'iDeviceModel', 'remark', 'query']),
            showOperateColumn: this.showOperateColumn,
            operates: {stop: '停用'},
            actionMap: {stop: 'onStop'},
            operateRenderer: function(){
                return function(v, m, r){
                    if(r.get('status') == '在用') {
                        return '<a href="javascript:void(0);" action="stop">停用</a>';
                    } else {
                        return '';
                    }
                };
            },
            onStop: function(v, rc, ele, i, e){
                var me = this, win, winc = {
                    xtype: 'window',
                    modal: true,
                    closable: false,
                    resizable: false,
                    title: '停用' + rc.get('asset_type__name'),
                    layout: 'fit',
                    items: [{
                        xtype: 'form',
                        border: false,
                        bodyCls: 'no-bg',
                        margin: 30,
                        layout: 'anchor',
                        items: [{
                            xtype: 'textfield',
                            fieldLabel: '停用数量',
                            anchor: '100%',
                            name: 'number',
                            regex: /^[1-9]\d*$/,
                            regexText: '无效的数字',
                            allowBlank: false
                        }, {
                            xtype: 'hidden',
                            name: 'uuid',
                            value: rc.raw.uuid
                        }]
                    }],
                    buttons: [{
                        text: '停用',
                        handler: function(){
                            var win = this.up('window'),
                                fm = win.down('form'),
                                msg, num;
                            msg = bbt.utils.checkForm(fm);
                            if(msg !== true) {
                                //Ext.Msg.alert('提示', msg);
                                return;
                            }
                            fm = fm.getForm();
                            num = fm.findField('number').getValue();
                            fm.waitTarget = win;
                            fm.submit({
                                url: '/asset/delete/',
                                method: 'POST',
                                waitMsg: '正在停用',
                                success: function(){
                                    num = parseInt(num) || 0;
                                    rc.store.reload();
                                    win.totalStop += num;
                                    win.destroy();
                                },
                                failure: function(f, a){
                                    var msg;
                                    try {
                                        msg = a.result.msg;
                                    } catch(e){}
                                    Ext.Msg.alert('提示', msg);
                                }
                            });
                        }
                    }, {
                        text: '关闭',
                        handler: function(){ this.up('window').destroy(); }
                    }],
                    buttonAlign: 'center'
                };
                win = Ext.widget('window', winc);
                win.show();
                win.totalStop = 0;
                win.on('beforedestroy', function(){
                    if(this.totalStop > 0) {
                        me.assetType.set('unit_count', me.assetType.get('unit_count')-this.totalStop);
                    }
                });
            }
        };
        if(!bbt.UserInfo.isSchool()) {
            var areas = ['town', 'school', grid.tbar.shift()];
            if(bbt.UserInfo.level == "city") {
                areas.unshift("country");
            }
            grid.dockedItems = [{xtype:'toolbar', dock: 'top', items: bbt.ToolBox.convert(areas), layout: {overflowHandler: 'Menu'}}];
            lastCol = grid.columns.pop();
            
            grid.columns.unshift({text: '学校', width: 160, dataIndex: 'asset_type__school__name'});
            grid.columns.unshift({text: '街道乡镇', width: 160, dataIndex: 'asset_type__school__parent__name'});
            if(bbt.UserInfo.level == "city") {
                grid.columns.unshift({text: '区县市', width: 160, dataIndex: 'asset_type__school__parent__parent__name'});
            }
            grid.columns.push(lastCol);
        }
        Ext.apply(this, {
            modal: true,
            //resizable: false,
            layout: 'fit',
            width: 860,
            height: 500,
            items: [grid]
        });
        this.callParent();
    },
    listeners: {
        afterrender: function(){
            var w = this;
            try {Ext.isIE8&&setTimeout(function(){w.center();}, 10);}catch(e){}
        },
        beforedestroy: function(){
            var p = this.__parent;
            p.recoveryAreaStatus();
        }
    },
    _get_other_level_params: function(){
        var params = {}, assetType = this.assetType;
        params.name = assetType.get('name');
        params.icon = assetType.get('icon');
        params.unit_name = assetType.get('unit_name');
        return params;
    }
});
Ext.define('bbt.ReportAsset', {
    extend: 'Ext.window.Window',
    alias: 'widget.report_asset',
    addUrl: '/asset/add/',
    initComponent: function(){
        Ext.apply(this, {
            title: '新增申报',
            modal: true,
            closable: false,
            resizable: false,
            width: 400,
            height: 300,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                bodyCls: 'no-bg',
                margin: 30,
                defaults: {anchor: '100%', margin: '10 0 0 0', allowBlank: false},
                items: [{
                    xtype: 'combo',
                    fieldLabel: '资产类型',
                    name: 'asset_type',
                    displayField: 'name',
                    valueField: 'uuid',
                    queryMode: 'local'
                }, {
                    xtype: 'textfield',
                    fieldLabel: '设备型号',
                    maxLength: 100,
                    name: 'device_model'
                }, {
                    xtype: 'textfield',
                    fieldLabel: '数量',
                    name: 'number',
                    regex: /^\d+$/,
                    regexText: '无效的数字'
                }, {
                    xtype: 'combo',
                    fieldLabel: '资产来源',
                    maxLength: 10,
                    editable: false,
                    store: ['校自主采购', '县级电教采购', '地级电教采购', '省级电教采购', '其他'],
                    name: 'asset_from'
                }, {
                    xtype: 'textfield',
                    fieldLabel: '备注',
                    maxLength: 180,
                    allowBlank: true,
                    name: 'remark'
                }]
            }],
            buttons: [{text: '确定', action: 'save', margin: '0 50 5 0'}, {text: '关闭', action: 'close'}],
            buttonAlign: 'center',
            listeners: {
                boxready: function(){
                    var me = this, am = {save: me.onSave, close: me.close};
                    Ext.each(me.query('button[action]'), function(btn){
                        btn.setHandler(am[btn.action], me);
                    });
                }
            }
        });
        this.callParent();
    },
    onSave: function(){
        var me = this, fm = me.down('form'), msg, submitCB, num;
        msg = checkForm(fm);
        if(msg !== true) {
            //Ext.Msg.alert('提示', msg);
            return;
        }
        fm = fm.getForm();
        //add num later
        num = fm.findField('number').getValue();
        submitCB = function(form, action){
            var data = action.result||{};
            if(data.status == "success") {
                num = parseInt(num) || 0;
                me.assetTypeModel.set('unit_count', me.assetTypeModel.get('unit_count')+num);
                me.askAddAgain();
            } else {
                Ext.Msg.alert('提示', data.msg);
                me.destroy();
            }
        };
        fm.waitTarget = me;
        fm.submit({
            url: me.addUrl,
            waitMsg: '正在申报……',
            success: submitCB,
            failure: submitCB
        });
    },
    close: function(){
        this.destroy();
    },
    askAddAgain: function(){
        var me = this, winc = {
            title: '提示',
            modal: true,
            autoShow: true,
            closable: false,
            resizable: false,
            width: 200,
            items: [{
                xtype: 'panel',
                header: false,
                bodyCls: 'no-bg',
                border: false,
                margin: '30 15',
                html: '<p style="text-align: center;">申报成功！</a>'
            }],
            buttons: [{text: '继续申报 >>', handler: function(){
                me.resetForm();
                this.up('window').destroy();
            }}, {text: '关闭', handler: function(){
                this.up('window').destroy();
                me.destroy();
            }}],
            buttonAlign: 'center'
        };
        new Ext.window.Window(winc);
    },
    resetForm: function(){
        var fm = this.down('form').getForm(), ast_type = fm.findField('asset_type').getValue();
        fm.reset();
        fm.findField('asset_type').setValue(ast_type);
    }
});

Ext.define('bbt.NewAsset', {
    extend: 'Ext.window.Window',
    alias: 'widget.bbt_newast',
    initComponent: function(){
        var fm = {
            xtype: 'form',
            bodyCls: 'no-bg',
            margin: 30,
            border: false,
            defaults: {allowBlank: false},
            items: [{
                xtype: 'combo',
                fieldLabel: '设备图标',
                name: 'icon',
                editable: false,
                displayField: 'text',
                valueField: 'value',
                listConfig: {
                    getInnerTpl: function(f){
                        return '<img style="float:left; width: 48px;height: 48px" src="/public/images/asset/{value}.png"/> <span style="line-height:48px;margin-left:10px;">{text}</span>';
                    }
                },
                store: new Ext.data.Store({data: [{"text":"台式计算机","value":"pc"},{"text":"电子白板","value":"whiteboard"},{"text":"投影仪","value":"projector"},{"text":"视频展台","value":"visual_presenter"},{"text":"教室中控台","value":"center_console"},{"text":"大屏显示器","value":"lfd"},{"text":"笔记本","value":"notebook"},{"text":"打印机","value":"printer"},{"text":"瘦终端","value":"thin_terminal"},{"text":"网络交换机","value":"switchboard"},{"text":"其他教具1","value":"others1"},{"text":"其他教具2","value":"others2"},{"text":"其他教具3","value":"others3"}], fields: ['text','value']})
            }, {
                xtype: 'textfield',
                fieldLabel: '设备类型名称',
                name: 'name'
            }, {
                xtype: 'textfield',
                fieldLabel: '数量单位',
                name: 'unit_name',
                maxLength: 2
            }]
        }, me = this;
        Ext.apply(this, {
            title: '新增资产类型',
            modal: true,
            closable: false,
            resizable: false,
            width: 350,
            height: 200,
            buttons: [{text: '确定', action: 'save', margin: '5 50 5 5'}, {text: '关闭', action: 'close'}],
            buttonAlign: 'center',
            items: [fm],
            listeners: {
                afterrender: function(){
                    this.down('button[action=save]').on('click', this.onSave, this);
                    this.down('button[action=close]').on('click', this.close, this);
                }
            }
        });
        this.callParent();
    },
    notifyRefresh: function(argument) {
        if(this.assetManager) {
            this.assetManager.getView().store.load();
        }
    },
    askAddAgain: function(){
        var me = this, winc = {
            title: '提示',
            modal: true,
            autoShow: true,
            closable: false,
            width: 250,
            items: [{
                xtype: 'panel',
                margin: '30 10',
                border: false,
                bodyCls: 'no-bg',
                html: '<p style="text-align:center;">添加资产类型成功！</p>'
            }],
            buttons: [{text: '继续添加 >>', handler: function(){
                me.resetForm();
                this.up('window').destroy();
            }}, {text: '关闭', handler: function(){
                this.up('window').destroy();
                me.destroy();
            }}],
            buttonAlign: 'center'
        };
        new Ext.window.Window(winc);
    },
    resetForm: function(){
        var fm = this.down('form').getForm();
        fm.reset();
        fm.findField('icon').expand();
    },
    onSave: function(){
        var me = this, fm = me.down('form'), msg, submitCB;
        msg = checkForm(fm);
        if(msg !== true) {
            //Ext.Msg.alert('提示', msg);
            return;
        }
        submitCB = function(form, action){
            var data = action.result||{};
            if(data.status == "success") {
                me.notifyRefresh();
                me.askAddAgain();
            } else {
                Ext.Msg.alert('提示', getErrorMsg(data));
            }
        };
        fm.getForm().submit({
            url: '/asset/asset_type/add/',
            success: submitCB,
            failure: submitCB
        });
    },
    close: function(){
        this.destroy();
    }
});

Ext.define('bbt.DangerOperate', {
    extend: 'Ext.window.Window',
    alias: 'widget.dangerwin',
    initComponent: function(){
        Ext.apply(this, {
            title: '授权',
            modal: true,
            closable: false,
            resizable: false,
            width: 260,
            height: 170,
            layout: 'fit',
            items: [{
                xtype: 'form',
                border: false,
                bodyCls: 'no-bg',
                margin: 30,
                layout: 'anchor',
                items: [{
                    anchor: '100%',
                    xtype: 'textfield',
                    labelAlign: 'top',
                    fieldLabel: '请输入超级管理员的密码',
                    name: 'password',
                    inputType: 'password'
                }]
            }],
            buttons: [{
                text: '确定',
                handler: function(){
                    var win = this.up('dangerwin'),
                        pwd = win.down('[name=password]').getValue();
                    win.validatePassword(pwd);
                }
            }, {
                text: '取消',
                handler: function(){
                    var win = this.up('window');
                    win.onFail && win.onFail();
                    win.destroy();
                }
            }]
        });
        this.callParent();
    },
    validatePassword: function(pwd) {
        var me = this;
        Ext.Ajax.request({
            method: 'POST',
            url: '/system/sudo/',
            params: {password: pwd},
            callback: function(opts, _, resp){
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    me.onPass && me.onPass();
                } else {
                    me.onFail && me.onFail();
                    Ext.Msg.alert('提示', '密码错误！');
                }
                me.destroy();
            }
        });
    }
});

Ext.define('bbt.SystemRestore', {
    extend: 'Ext.window.Window',
    alias: 'widget.bbt_restore',
    autoShow: true,
    modal: true,
    width: 400,
    height: 300,
    items: [{
        xtype: 'form',
        margin: 40,
        border: false,
        layout: 'anchor',
        bodyCls: 'no-bg',
        items: [{
            xtype : 'fileuploadfield',
            fieldLabel: '选择文件并导入',
            name : 'excel',
            anchor: '100%',
            buttonText: '...'
        }]
    }],
    layout: 'fit',
    buttons: [{text: '确定', handler: function(){
        var fm = this.up('window').down('form'), cb;
        cb = function(fm, action){
            var data = action.result;
            Ext.Msg.alert('提示', data.msg||'服务器错误！');
        };
        fm.submit({
            url: '/system/restore/',
            success: cb,
            failure: cb
        });
    }}, {text: '关闭', handler: function(){ this.up('window').destroy(); }}],
    buttonAlign: 'center'
});

/* bbt 色块 */
Ext.define('bbt.ColorBlockView', {
    extend: 'Ext.view.View',
    alias: 'widget.colorblock',
    itemSelector: 'div.color-block-item',
    tpl: ['<div class="color-block-view">',
        '<div class="color-block-view-inner">',
        '<tpl for=".">',
            '<div class="color-block-item" style="background-color:#{bgcolor}">',
                '<div class="icon-block">{firstChar}</div>',
                '<div class="detail-block" style="top:{top}px;">',
                    '<div class="level-text" title="{name}"><span>{group_text}</span></div>',
                    '<p style="color: {fontColor};" class="info-text">{majorText}<br/>{juniorText}</p>',
                '</div>',
            '</div>',
        '</tpl>',
        '<div style="clear:both;"></div>',
        '</div></div>'],
    allColors: [
        ['facca8', '98d0dd', 'd2c9de', 'cadaa9', 'eccdcb', 'c9d6e6'],
        ['f8b57e', '71bfd3', 'bfb0cf', 'b5ca85', 'da9791', 'b0c2da']
    ],
    constructor: function(o){
        this.listGroupUrl = '/activity/desktop-preview/groups/';
        this.listImageUrl = '/activity/desktop-preview/by-date/';
        this.hasImageUrl = '/activity/desktop-preview/list-everyday/';
        var store = new Ext.data.Store({
            fields: ['name', 'uuid', 'school_count', 'class_count', 'pic_count', 'group_type'],
            proxy: {
                url: this.listGroupUrl,
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            },
            pageSize: 6
        });
        this.store = store;
        this.colors = this.suffle(bbt.UserInfo.level);
        this.listeners = {
            itemclick: function(me, rc){
                var uuid = rc.get('uuid'),
                    group_type = rc.get('group_type'),
                    term, startDate, endDate, now;
                if(group_type == "class") {
                    term = me.up('previewlog').down('[name=term_type]');
                    term = term.findRecordByValue(term.getValue());
                    startDate = Ext.Date.parse(term.get('start_date'), 'Y-m-d');
                    endDate = Ext.Date.parse(term.get('end_date'), 'Y-m-d');
                    now = new Date();
                    if(now > startDate && now < endDate) {
                        endDate = now;
                    }
                    me.viewBlock(rc, startDate, endDate);
                } else {
                    if(this._stack.length === 0 && group_type == 'town') {
                        this._stack.push([store.proxy.reader.rawData.data.root_name, 'country', null]);
                    }
                    store.proxy.extraParams.uuid = uuid;
                    store.load();
                    this.crumbsEl && this.updateCrambs(rc.get('name'), group_type, Ext.clone(store.proxy.extraParams));
                    this.colors = this.suffle(group_type);
                }
            }
        };
        this.callParent();
    },
    _stack: [],
    updateCrambs: function(name, type, params){
        var stack = [], found = false, htmls = [];
        Ext.each(this._stack, function(item){
            if(item[1] === type) {//event source: spreadCrumbs
                found = true;
                stack.push([name, type, params]);
                return false;
            } else {
                stack.push(item);
            }
        });
        //event source: colorblock
        if(!found) {
            stack.push([name, type, params]);
        }
        Ext.each(stack, function(item, i, a){
            if(i+1 === a.length) {
                htmls.push(item[0]);
            } else {
                htmls.push('<a href="javascript:void(0);" data-type="' + item[1] + '">' + item[0] + '</a>');
            }
        });
        this.crumbsEl.setHTML('<p class="spread-crumbs">' + htmls.join('&nbsp;&gt;&nbsp;') + '</p>');
        this._stack = stack;
    },
    viewBlock: function(model, start, end){
        var bg = bbt.createOverlay(), viewer, store, pages;
        viewer = document.createElement('div');
        viewer.style.zIndex = 20;
        viewer.className = "log-viewer";
        viewer.innerHTML = '<div class="time-axis"><a class="pager first-page"></a><a class="pager prev-page"></a><ul>' + new Array(21).join('<li></li>') + '</ul><a class="pager next-page"></a><a class="pager last-page"></a></div><img src=""/><div class="log-footer"><a href="javascript:void(0);"></a><span></span></div>';
        document.body.appendChild(viewer);
        viewer = Ext.get(viewer);
        
        pages = (function(){
            var ret = [], tmp = [], d, i = 0, len = (end - start) / (24*60*60*1000);
            for(;i<=len;i++) {
                d = Ext.Date.clone(start);
                d.setDate(d.getDate() + i);
                tmp.push(Ext.Date.format(d, 'Y-m-d'));
                if(tmp.length === 20) {
                    ret.push(tmp);
                    tmp = [];
                }
            }
            if(tmp.length && tmp.length < 20) {
                while(tmp.length != 20) {
                    d = Ext.Date.clone(start);
                    d.setDate(d.getDate() + i);
                    tmp.push(Ext.Date.format(d, 'Y-m-d'));
                    i++;
                }
                ret.push(tmp);
            }
            return ret;
        })();
        //set up anchors
        /*Ext.each(viewer.query('li'), function(li, i){
            var d = Ext.Date.clone(end);
            d.setDate(d.getDate() - (19 - i));
            d = Ext.Date.format(d, 'Y-m-d');
            li.setAttribute('data-date', d);
            Ext.get(li).child('.date').setHTML(d.substring(5));
            if(i === 0) {
                li.className += " first";
            }
            li.on('click', function(e, me){
                var selected = Ext.get(me.parentNode).child('.selected-date'), label, text, viewer;
                selected.removeCls('selected-date');

                selected = Ext.get(me);
                selected.addCls("selected-date");

                text = me.getAttribute('data-date');
                
                viewer = selected.parent('.log-viewer');

                label = viewer.down('[data-role=label]');
                label.setHTML(text);
                label.setX(selected.getX()-(label.getWidth()-selected.getWidth())/2);

                viewer.unHighlight();
                viewer.makeHighlight(selected);

                viewer.store.proxy.extraParams.date = text;
                viewer.store.load();
            });
            li.hover(function(e, el){
                var me = Ext.get(el),
                    focus = me.parent('.inner').down('.fake-focus'),
                    label = me.parent('.time-axis').child('[data-role=fake-label]');
                if(me.hasCls('selected-date')) { return; }
                label.addCls('date-text');
                label.setHTML(me.getAttribute('data-date'));
                label.setX(me.getX() - (label.getWidth()-me.getWidth())/2);
                
                label.setStyle('top', '10px');
                label.show();
                
                label.animate({
                    duration: 500,
                    to: {
                        top: '0px'
                    }
                });
                me.fakeLabel = label;
                focus.animate({
                    duration: 300,
                    to: {
                        x: me.getX() - (focus.getWidth()-me.getWidth())/2
                    }
                });
            }, function(e, el){
                var me = Ext.get(el),
                    focus = me.parent('.inner').down('.fake-focus'),
                    selected = me.prev('.selected-date');
                if(me.fakeLabel) {
                    me.fakeLabel.removeCls('date-text');
                    me.fakeLabel.hide();
                    delete me.fakeLabel;
                }
                if(!selected) {
                    selected = me.next('.selected-date');
                }
                if(!selected) {
                    return;
                }
                
                focus.animate({
                    stopAnimation: true,
                    delay: 100,
                    duration: 300,
                    to: {
                        x: selected.getX() - (focus.getWidth()-selected.getWidth())/2
                    }
                });
            });
        });*/
        bg.onBeforeDestroy = function(){
            viewer.unHighlight();
            Ext.removeNode(viewer.dom);
        };
        viewer.store = new Ext.data.Store({
            autoLoad: true,
            fields: ['grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence', 'created_at', 'url'],
            proxy: {
                type: 'ajax',
                url: this.listImageUrl,
                extraParams: {
                    date: Ext.Date.format(end, 'Y-m-d'),
                    class_uuid: model.raw.uuid,
                    lesson_period_sequence: model.store.proxy.extraParams.lesson_period_sequence
                },
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            },
            listeners: {
                load: function(s){
                    viewer.currentImageIndex = 0;
                    viewer.setByModel(s.getAt(0));
                }
            }
        });
        Ext.apply(viewer, {
            hasImageUrl: this.hasImageUrl,
            jieci: model.store.proxy.extraParams.lesson_period_sequence,
            classUUID: model.raw.uuid,
            pages: pages,
            MAX_DATE: Ext.Date.format(end, 'Y-m-d'),
            initViewerEvents: function(){
                var me = this, axis = me.child('.time-axis'), list = axis.child('ul');;
                //delegate events
                list.on('click', function(e){
                    var me = Ext.get(e.target), $this = this;
                    if(me.hasCls('circle-off') || me.hasCls('selected')) { return; }
                    Ext.each(me.parent('ul').query('.focus'), function(n){
                        var $n;
                        if(n.className.indexOf('off') === -1) {
                            $n = Ext.get(n);
                            $n.addCls('focus-off')
                            $n.child('.circle').removeCls('selected');
                            $n.next('.date').setStyle('display', 'none');
                            $n.parent('li').removeCls('colored');
                            $this.unHighlight();
                        }
                    });
                    me.addCls('selected');
                    me.parent().next('.date').setStyle('display', 'block');
                    me.parent().removeCls("focus-off");
                    me.parent('li').addCls('colored');
                    $this.makeHighlight(me);
                    viewer.store.proxy.extraParams.date = me.parent('li').getAttribute('data-date');
                    viewer.store.load();
                }, me, {delegate: '.circle'});
                list.on('mouseover', function(e){
                    var me = Ext.get(e.target);
                    if(me.hasCls('selected')) { return; }
                    if(!me.hasCls('circle-off')) {
                        me.parent().removeCls("focus-off");
                    }
                    
                    me.parent('li').child('.date').setStyle('display', 'block');
                }, null, {delegate: '.circle'});
                list.on('mouseout', function(e){
                    var me = Ext.get(e.target);
                    if(me.hasCls('selected')) { return; }
                    if(!me.hasCls('circle-off')) {
                        me.parent().addCls("focus-off");
                    }
                    
                    me.parent('li').child('.date').setStyle('display', 'none');
                }, null, {delegate: '.circle'});
                //pager events
                axis.on('click', function(e){
                    var me = Ext.get(e.target);
                    if(me.hasCls('prev-page')) {
                        this.loadTimeAsixPage('prev');
                    } else if(me.hasCls('first-page')) {
                        this.loadTimeAsixPage(0);
                    } else if(me.hasCls('next-page')) {
                        this.loadTimeAsixPage('next');
                    } else if(me.hasCls('last-page')) {
                        this.loadTimeAsixPage(-1);
                    }
                }, me, {delegate: '.pager'});
                //img operate
                me.child('img').on('mousemove', function(e){
                    var xm = e.getX(), x = this.getX(), w = this.getWidth();
                    if((xm-x) > w/2) {
                        this.setStyle("cursor", "url(/public/images/mouse-right.cur), auto");
                    } else {
                        this.setStyle("cursor", "url(/public/images/mouse-left.cur), auto");
                    }
                }).on('click', function(e){
                    var xm = e.getX(), x = this.getX(), w = this.getWidth();
                    if((xm-x) > w/2) {
                        me.nextImage();
                    } else {
                        me.prevImage();
                    }
                });

                me.child('.log-footer').child('a').on('click', function(e, me){
                    var p = Ext.get(me.parentNode), h = p.getHeight();
                    if(h === 0) {
                        p.animate({
                            stopAnimation: true,
                            duration: 400,
                            to: {
                                height: '40px'
                            },
                            callback: function(){ me.className = ''; }
                        });
                    } else {
                        p.animate({
                            duration: 400,
                            to: {height: '0px'},
                            callback: function(){ me.className = 'switch-up'; }
                        });
                    }
                    
                });
            },
            loadTimeAsixPage: function(index){
                var me = this, page, htmls = [], i, len, inner, list;
                if(typeof index == "number") {
                    if(index < 0) {
                        index = me.pages.length + index;
                    }
                    page = me.pages[index];
                } else if(typeof index == "string") {
                    for(i=0,len=me.pages.length;i<len;i++) {
                        if(me.pages[i].current) {
                            break;
                        }
                    }
                    if(index == "prev") {
                        i--;
                    } else if(index == "next") {
                        i++;
                    }
                    page = me.pages[i];
                }
                
                if(!page || (page&&page.current)) { return; }
                Ext.each(me.pages, function(p){
                    p.current && (delete p.current);
                });
                page.current = true;
                inner = '</b><div class="focus focus-off"><a class="circle"></a></div><b class="date">';
                for(i=0,len=page.length;i<len;i++) {
                    if(i === 0) {
                        htmls.push('<li class="first" data-date="' + page[i] + '"><b class="line line-off">');
                    } else {
                        htmls.push('<li data-date="' + page[i] + '"><b class="line">');
                    }
                    if(page[i] > me.MAX_DATE) {
                        htmls.push(inner.replace('circle', 'circle circle-off'));
                    } else {
                        htmls.push(inner);
                    }
                    htmls.push(page[i].substring(5) + '</b></li>');
                }
                me.unHighlight();
                list = me.child('.time-axis').child('ul');
                list.setHTML(htmls.join(''));
                Ext.Ajax.request({
                    method: 'GET',
                    url: me.hasImageUrl,
                    params: {
                        lesson_period_sequence: me.jieci,
                        class_uuid: me.classUUID,
                        start_date: page[0],
                        end_date: page[page.length-1]
                    },
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText), li, date, last;
                        if(data.status != "success") { return; }
                        data = data.data;
                        li = list.child('li');
                        while(li) {
                            date = li.dom.getAttribute('data-date');
                            if((date in data) && data[date] === 0) {
                                li.down('.circle').addCls('circle-off');
                            }
                            if(li.down('.circle').dom.className == "circle") {
                                last = li;
                            }
                            li = li.next('li');
                        }
                        last && bbt.simulateClick(last.down('.circle').dom) || me.setByModel();
                    }
                });
            },
            $func: (function(){
                var styleText = "inset 0 0 {x}px #1eff00", radius = 6, dir = 1;
                return function(){
                    var style = arguments.callee.style;
                    if(!style) { return; }
                    if(radius == 16 || radius == -2) { dir = dir * -1; }
                    radius += dir;
                    if(style.webkitBoxShadow) {
                        style.webkitBoxShadow = styleText.replace('{x}', radius);
                    } else if(style.mozBoxShadow) {
                        style.mozBoxShadow = styleText.replace('{x}', radius);
                    } else {
                        style.boxShadow = styleText.replace('{x}', radius);
                    }
                };
            })(),
            makeHighlight: function(el){
                if(Ext.isIE && Ext.ieVersion < 9) { return; }
                this.$func.style = el.dom.style;
                this.$timer = setInterval(this.$func, 80);
                this.$animateTarget = el;
            },
            unHighlight: function(){
                if(Ext.isIE && Ext.ieVersion < 9) { return; }
                if(!this.$animateTarget) { return; }
                clearInterval(this.$timer);
                var style = this.$animateTarget.dom.style;
                if(style.webkitBoxShadow) {
                    style.webkitBoxShadow = "";
                } else if(style.mozBoxShadow) {
                    style.mozBoxShadow = "";
                } else {
                    style.boxShadow = "";
                }
                delete this.$animateTarget;
            },
            setByModel: function(model){
                var img = this.down('img', true), proxy, resize, footer, me = this, timer;
                if(!model) {
                    img.style.visibility = "hidden";
                    this.child('.log-footer').down('span').setHTML('');
                    return -1;
                }
                
                
                resize = function(img, r){
                    var w, h, ah = Ext.getBody().getHeight() - 94;
                    if(r === false) {
                        w = model.raw.naturalWidth;
                        h = model.raw.naturalHeight;
                    } else {
                        h = 550;
                        w = h * model.raw.naturalWidth / model.raw.naturalHeight;
                    }
                    
                    img.width = w;
                    img.height = h;
                    img.style.marginLeft = '-' + (w/2) + 'px';
                    if(h <= ah) {
                        img.style.top = "50%";
                        img.style.marginTop = h / -2 + "px";
                        img.style.bottom = "auto";
                    } else {
                        img.style.top = "auto";
                        img.style.marginTop = "auto";
                        img.style.bottom = "0px";
                    }
                    if(img.style.visibility == "hidden") {
                        img.style.visibility = "visible";
                    }
                };
                
                
                if(typeof model.raw.naturalWidth == "undefined") {
                    proxy = new Image();
                    proxy.$target = img;
                    proxy.src = 'http://' + model.raw.host + model.raw.url;
                    me.mask('正在加载图片...');
                    proxy.onload = function(e){
                        e = e || window.event;
                        me.unmask();
                        if(proxy.naturalHeight) {
                            model.raw.naturalHeight = proxy.naturalHeight;
                            model.raw.naturalWidth = proxy.naturalWidth;
                        } else {
                            model.raw.naturalWidth = proxy.width;
                            model.raw.naturalHeight = proxy.height;
                        }
                        proxy.$target.src = proxy.src;
                        resize(proxy.$target);
                        proxy.onload = null;
                        delete proxy.$target;
                        clearTimeout(timer);
                    };
                    timer = setTimeout(function(){
                        delete proxy.$target;
                        delete proxy.onload;
                        proxy = null;
                        me.unmask();
                        img.src = "/public/images/broken.png";
                        model.raw.naturalWidth = 650;
                        model.raw.naturalHeight = 400;
                        resize(img, false);
                    }, 60*1000);
                } else {
                    img.src = 'http://' + model.raw.host + model.raw.url;
                    resize(img);
                }
                footer = this.child('.log-footer');
                footer.down('span').setHTML(Ext.String.format(
                    "时间:{0}&nbsp;&nbsp;节次:{1}&nbsp;&nbsp;班级:{2}&nbsp;&nbsp;课程:{3}&nbsp;&nbsp;授课教师:{4}",
                    model.data.created_at,
                    model.data.lesson_period_sequence,
                    model.data.grade_name + "年级" + model.data.class_name + "班",
                    model.data.lesson_name,
                    model.data.teacher_name
                ));
            },
            makeFooterVisible: function(){
                var footer = this.child('.log-footer');
                footer.setHeight(40);
            },
            prevImage: function(){
                var i, li, hasPrev = false;
                if(this.currentImageIndex === 0) {
                    try {
                        li = this.down('.selected').parent('li');
                        while(li) {
                            li = li.prev('li');
                            if(!li.down('.circle-off')) {
                                hasPrev = true;
                                break;
                            }
                        }
                        bbt.simulateClick(li.down('.circle').dom);
                    } catch(e) {}
                } else {
                    hasPrev = true;
                }
                if(!hasPrev) { return; }
                i = --this.currentImageIndex;
                i = this.setByModel(this.store.getAt(i));
                if(i === -1) { return; }
                this.makeFooterVisible();
            },
            nextImage: function(){
                var i, li, hasNext = false;
                if(this.currentImageIndex === (this.store.count()-1)) {
                    try {
                        li = this.down('.selected').parent('li');
                        while(li) {
                            li = li.next('li');
                            if(!li.down('.circle-off')) {
                                hasNext = true;
                                break;
                            }
                        }
                        bbt.simulateClick(li.down('.circle').dom);
                    } catch(e) {}
                } else {
                    hasNext = true;
                }
                if(!hasNext) { return; }
                i = ++this.currentImageIndex;
                i = this.setByModel(this.store.getAt(i));
                if(i === -1) { return; }
                this.makeFooterVisible();
            }
        });
        viewer.initViewerEvents();
        viewer.loadTimeAsixPage(-1);
    },
    suffle: function(level){
        var arr, i = 0, len, pos, tmp;
        tmp = Ext.Array.indexOf('province city country town school grade class'.split(' '), level);
        if(tmp <= 2) { //big level
            arr = this.allColors[1];
            this.fontColor = "#FFF";
        } else {
            arr = this.allColors[0];
            this.fontColor = "#8b7d72";
        }
        for(len=arr.length;i<len;i++) {
            pos = Math.floor(Math.random() * len);
            if(pos == i) { continue; }
            else {
                tmp = arr[i];
                arr[i] = arr[pos];
                arr[pos] = tmp;
            }
        }
        return arr;
    },
    prepareData: function(data, index, record) {
        data.bgcolor = this.colors[index%this.colors.length];
        data.fontColor = this.fontColor;
        data.firstChar = data.name.charAt(0);
        data.top = 0;
        if(data.name.length > 10) {
            data.group_text = data.name.substr(0, 9)+'..';
        } else {
            data.group_text = data.name;
            if(data.name.length < 6) {
                data.top = -14;
            }
        }
        
        switch(data.group_type) {
            case 'class':
                data.majorText = data.pic_count + '次';
                data.juniorText = '桌面预览';
                break;
            case 'school':
                data.majorText = data.class_count + '个班级';
                break;
            default:
                data.majorText = data.school_count + '所学校';
                data.juniorText = data.class_count + '个班级';
                break;
        }
        return data;
    }
});
/* edu 色块 */
Ext.define('bbt.ColorBlockViewEdu', {
    extend: 'Ext.view.View',
    alias: 'widget.colorblockedu',
    itemSelector: 'div.color-block-item',
    tpl: ['<div class="color-block-view">',
        '<div class="color-block-view-inner">',
        '<tpl for=".">',
            '<div class="color-block-item" style="background-color:#{bgcolor}">',
                '<div class="icon-block">{firstChar}</div>',
                '<div class="detail-block" style="top:{top}px;">',
                    '<div class="level-text" title="{name}"><span>{group_text}</span></div>',
                    '<p style="color: {fontColor};" class="info-text">{majorText}<br/>{juniorText}</p>',
                '</div>',
            '</div>',
        '</tpl>',
        '<div style="clear:both;"></div>',
        '</div></div>'],
    allColors: [
        ['facca8', '98d0dd', 'd2c9de', 'cadaa9', 'eccdcb', 'c9d6e6'],
        ['f8b57e', '71bfd3', 'bfb0cf', 'b5ca85', 'da9791', 'b0c2da']
    ],
    constructor: function(o){
        this.listGroupUrl = '/edu-unit/screenshot/node-info/';
        this.listImageUrl = '/edu-unit/screenshot/details/';
        this.hasImageUrl = '/edu-unit/screenshot/node-timeline/';
        var store = new Ext.data.Store({
            fields: ['parent_name', 'uuid', 'unit_count', 'room_count', 'pic_count', 'node_type', 'child_type'],
            proxy: {
                url: this.listGroupUrl,
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            },
            pageSize: 6
        });
        this.store = store;
        this.colors = this.suffle(bbt.UserInfo.level);
        this.listeners = {
            itemclick: function(me, rc){
                var term, startDate, endDate, now, ctype = rc.get('node_type');
                if(ctype == "room") {
                    term = me.up('previewlog').down('[name=term_type]');
                    term = term.findRecordByValue(term.getValue());
                    startDate = Ext.Date.parse(term.get('start_date'), 'Y-m-d');
                    endDate = Ext.Date.parse(term.get('end_date'), 'Y-m-d');
                    now = new Date();
                    if(now > startDate && now < endDate) {
                        endDate = now;
                    }
                    me.viewBlock(rc, startDate, endDate);
                } else {
                    if(this._stack.length === 0 && ctype == 'town') {
                        this._stack.push([store.proxy.reader.rawData.data.conditions.country_name, 'country', null]);
                    }
                    Ext.apply(store.proxy.extraParams, store.proxy.reader.rawData.data.conditions);
                    store.proxy.extraParams.node_type = rc.get('child_type');
                    store.proxy.extraParams.parent = rc.get('parent_name');
                    store.load();
                    this.crumbsEl && this.updateCrambs(rc.get('parent_name'), ctype, Ext.clone(store.proxy.extraParams));
                    this.colors = this.suffle(ctype);
                }
            }
        };
        this.callParent();
    },
    _stack: [],
    updateCrambs: function(name, type, params){
        var stack = [], found = false, htmls = [];
        Ext.each(this._stack, function(item){
            if(item[1] === type) {//event source: spreadCrumbs
                found = true;
                stack.push([name, type, params]);
                return false;
            } else {
                stack.push(item);
            }
        });
        //event source: colorblock
        if(!found) {
            stack.push([name, type, params]);
        }
        Ext.each(stack, function(item, i, a){
            if(i+1 === a.length) {
                htmls.push(item[0]);
            } else {
                htmls.push('<a href="javascript:void(0);" data-type="' + item[1] + '">' + item[0] + '</a>');
            }
        });
        this.crumbsEl.setHTML('<p class="spread-crumbs">' + htmls.join('&nbsp;&gt;&nbsp;') + '</p>');
        this._stack = stack;
    },
    viewBlock: function(model, start, end){
        var bg = bbt.createOverlay(), viewer, store, pages;
        viewer = document.createElement('div');
        viewer.style.zIndex = 20;
        viewer.className = "log-viewer";
        viewer.innerHTML = '<div class="time-axis"><a class="pager first-page"></a><a class="pager prev-page"></a><ul>' + new Array(21).join('<li></li>') + '</ul><a class="pager next-page"></a><a class="pager last-page"></a></div><img src=""/><div class="log-footer"><a href="javascript:void(0);"></a><span></span></div>';
        document.body.appendChild(viewer);
        viewer = Ext.get(viewer);
        
        pages = (function(){
            var ret = [], tmp = [], d, i = 0, len = (end - start) / (24*60*60*1000);
            for(;i<=len;i++) {
                d = Ext.Date.clone(start);
                d.setDate(d.getDate() + i);
                tmp.push(Ext.Date.format(d, 'Y-m-d'));
                if(tmp.length === 20) {
                    ret.push(tmp);
                    tmp = [];
                }
            }
            if(tmp.length && tmp.length < 20) {
                while(tmp.length != 20) {
                    d = Ext.Date.clone(start);
                    d.setDate(d.getDate() + i);
                    tmp.push(Ext.Date.format(d, 'Y-m-d'));
                    i++;
                }
                ret.push(tmp);
            }
            return ret;
        })();
        //set up anchors
        bg.onBeforeDestroy = function(){
            viewer.unHighlight();
            Ext.removeNode(viewer.dom);
        };
        viewer.store = new Ext.data.Store({
            autoLoad: true,
            fields: ['grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence', 'created_at', 'url'],
            proxy: {
                type: 'ajax',
                url: this.listImageUrl,
                extraParams: {
                    date: Ext.Date.format(end, 'Y-m-d'),
                    room_id: model.raw.room_id,
                    point_id: model.raw.point_id,
                    lesson_period_sequence: model.store.proxy.extraParams.lesson_period_sequence
                },
                reader: {
                    type: 'json',
                    root: 'data.records'
                }
            },
            listeners: {
                load: function(s){
                    viewer.currentImageIndex = 0;
                    viewer.setByModel(s.getAt(0));
                }
            }
        });
        Ext.apply(viewer, {
            hasImageUrl: this.hasImageUrl,
            jieci: model.store.proxy.extraParams.lesson_period_sequence,
            classUUID: model.raw.uuid,
            pages: pages,
            MAX_DATE: Ext.Date.format(end, 'Y-m-d'),
            initViewerEvents: function(){
                var me = this, axis = me.child('.time-axis'), list = axis.child('ul');;
                //delegate events
                list.on('click', function(e){
                    var me = Ext.get(e.target), $this = this;
                    if(me.hasCls('circle-off') || me.hasCls('selected')) { return; }
                    Ext.each(me.parent('ul').query('.focus'), function(n){
                        var $n;
                        if(n.className.indexOf('off') === -1) {
                            $n = Ext.get(n);
                            $n.addCls('focus-off')
                            $n.child('.circle').removeCls('selected');
                            $n.next('.date').setStyle('display', 'none');
                            $n.parent('li').removeCls('colored');
                            $this.unHighlight();
                        }
                    });
                    me.addCls('selected');
                    me.parent().next('.date').setStyle('display', 'block');
                    me.parent().removeCls("focus-off");
                    me.parent('li').addCls('colored');
                    $this.makeHighlight(me);
                    viewer.store.proxy.extraParams.date = me.parent('li').getAttribute('data-date');
                    viewer.store.load();
                }, me, {delegate: '.circle'});
                list.on('mouseover', function(e){
                    var me = Ext.get(e.target);
                    if(me.hasCls('selected')) { return; }
                    if(!me.hasCls('circle-off')) {
                        me.parent().removeCls("focus-off");
                    }
                    
                    me.parent('li').child('.date').setStyle('display', 'block');
                }, null, {delegate: '.circle'});
                list.on('mouseout', function(e){
                    var me = Ext.get(e.target);
                    if(me.hasCls('selected')) { return; }
                    if(!me.hasCls('circle-off')) {
                        me.parent().addCls("focus-off");
                    }
                    
                    me.parent('li').child('.date').setStyle('display', 'none');
                }, null, {delegate: '.circle'});
                //pager events
                axis.on('click', function(e){
                    var me = Ext.get(e.target);
                    if(me.hasCls('prev-page')) {
                        this.loadTimeAsixPage('prev');
                    } else if(me.hasCls('first-page')) {
                        this.loadTimeAsixPage(0);
                    } else if(me.hasCls('next-page')) {
                        this.loadTimeAsixPage('next');
                    } else if(me.hasCls('last-page')) {
                        this.loadTimeAsixPage(-1);
                    }
                }, me, {delegate: '.pager'});
                //img operate
                me.child('img').on('mousemove', function(e){
                    var xm = e.getX(), x = this.getX(), w = this.getWidth();
                    if((xm-x) > w/2) {
                        this.setStyle("cursor", "url(/public/images/mouse-right.cur), auto");
                    } else {
                        this.setStyle("cursor", "url(/public/images/mouse-left.cur), auto");
                    }
                }).on('click', function(e){
                    var xm = e.getX(), x = this.getX(), w = this.getWidth();
                    if((xm-x) > w/2) {
                        me.nextImage();
                    } else {
                        me.prevImage();
                    }
                });

                me.child('.log-footer').child('a').on('click', function(e, me){
                    var p = Ext.get(me.parentNode), h = p.getHeight();
                    if(h === 0) {
                        p.animate({
                            stopAnimation: true,
                            duration: 400,
                            to: {
                                height: '40px'
                            },
                            callback: function(){ me.className = ''; }
                        });
                    } else {
                        p.animate({
                            duration: 400,
                            to: {height: '0px'},
                            callback: function(){ me.className = 'switch-up'; }
                        });
                    }
                    
                });
            },
            loadTimeAsixPage: function(index){
                var me = this, page, htmls = [], i, len, inner, list;
                if(typeof index == "number") {
                    if(index < 0) {
                        index = me.pages.length + index;
                    }
                    page = me.pages[index];
                } else if(typeof index == "string") {
                    for(i=0,len=me.pages.length;i<len;i++) {
                        if(me.pages[i].current) {
                            break;
                        }
                    }
                    if(index == "prev") {
                        i--;
                    } else if(index == "next") {
                        i++;
                    }
                    page = me.pages[i];
                }
                
                if(!page || (page&&page.current)) { return; }
                Ext.each(me.pages, function(p){
                    p.current && (delete p.current);
                });
                page.current = true;
                inner = '</b><div class="focus focus-off"><a class="circle"></a></div><b class="date">';
                for(i=0,len=page.length;i<len;i++) {
                    if(i === 0) {
                        htmls.push('<li class="first" data-date="' + page[i] + '"><b class="line line-off">');
                    } else {
                        htmls.push('<li data-date="' + page[i] + '"><b class="line">');
                    }
                    if(page[i] > me.MAX_DATE) {
                        htmls.push(inner.replace('circle', 'circle circle-off'));
                    } else {
                        htmls.push(inner);
                    }
                    htmls.push(page[i].substring(5) + '</b></li>');
                }
                me.unHighlight();
                list = me.child('.time-axis').child('ul');
                list.setHTML(htmls.join(''));
                Ext.Ajax.request({
                    method: 'GET',
                    url: me.hasImageUrl,
                    params: {
                        room_id: model.raw.room_id,
                        point_id: model.raw.point_id,
                        start_date: page[0],
                        end_date: page[page.length-1]
                    },
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText), li, date, last;
                        if(data.status != "success") { return; }
                        data = data.data;
                        li = list.child('li');
                        while(li) {
                            date = li.dom.getAttribute('data-date');
                            if((date in data) && data[date] === 0) {
                                li.down('.circle').addCls('circle-off');
                            }
                            if(li.down('.circle').dom.className == "circle") {
                                last = li;
                            }
                            li = li.next('li');
                        }
                        last && bbt.simulateClick(last.down('.circle').dom) || me.setByModel();
                    }
                });
            },
            $func: (function(){
                var styleText = "inset 0 0 {x}px #1eff00", radius = 6, dir = 1;
                return function(){
                    var style = arguments.callee.style;
                    if(!style) { return; }
                    if(radius == 16 || radius == -2) { dir = dir * -1; }
                    radius += dir;
                    if(style.webkitBoxShadow) {
                        style.webkitBoxShadow = styleText.replace('{x}', radius);
                    } else if(style.mozBoxShadow) {
                        style.mozBoxShadow = styleText.replace('{x}', radius);
                    } else {
                        style.boxShadow = styleText.replace('{x}', radius);
                    }
                };
            })(),
            makeHighlight: function(el){
                if(Ext.isIE && Ext.ieVersion < 9) { return; }
                this.$func.style = el.dom.style;
                this.$timer = setInterval(this.$func, 80);
                this.$animateTarget = el;
            },
            unHighlight: function(){
                if(Ext.isIE && Ext.ieVersion < 9) { return; }
                if(!this.$animateTarget) { return; }
                clearInterval(this.$timer);
                var style = this.$animateTarget.dom.style;
                if(style.webkitBoxShadow) {
                    style.webkitBoxShadow = "";
                } else if(style.mozBoxShadow) {
                    style.mozBoxShadow = "";
                } else {
                    style.boxShadow = "";
                }
                delete this.$animateTarget;
            },
            setByModel: function(model){
                var img = this.down('img', true), proxy, resize, footer, me = this, timer;
                if(!model) {
                    img.style.visibility = "hidden";
                    this.child('.log-footer').down('span').setHTML('');
                    return -1;
                }
                
                
                resize = function(img, r){
                    var w, h, ah = Ext.getBody().getHeight() - 94;
                    if(r === false) {
                        w = model.raw.naturalWidth;
                        h = model.raw.naturalHeight;
                    } else {
                        h = 550;
                        w = h * model.raw.naturalWidth / model.raw.naturalHeight;
                    }
                    
                    img.width = w;
                    img.height = h;
                    img.style.marginLeft = '-' + (w/2) + 'px';
                    if(h <= ah) {
                        img.style.top = "50%";
                        img.style.marginTop = h / -2 + "px";
                        img.style.bottom = "auto";
                    } else {
                        img.style.top = "auto";
                        img.style.marginTop = "auto";
                        img.style.bottom = "0px";
                    }
                    if(img.style.visibility == "hidden") {
                        img.style.visibility = "visible";
                    }
                };
                
                
                if(typeof model.raw.naturalWidth == "undefined") {
                    proxy = new Image();
                    proxy.$target = img;
                    proxy.src = 'http://' + model.raw.host + model.raw.url;
                    me.mask('正在加载图片...');
                    proxy.onload = function(e){
                        e = e || window.event;
                        me.unmask();
                        if(proxy.naturalHeight) {
                            model.raw.naturalHeight = proxy.naturalHeight;
                            model.raw.naturalWidth = proxy.naturalWidth;
                        } else {
                            model.raw.naturalWidth = proxy.width;
                            model.raw.naturalHeight = proxy.height;
                        }
                        proxy.$target.src = proxy.src;
                        resize(proxy.$target);
                        proxy.onload = null;
                        delete proxy.$target;
                        clearTimeout(timer);
                    };
                    timer = setTimeout(function(){
                        delete proxy.$target;
                        delete proxy.onload;
                        proxy = null;
                        me.unmask();
                        img.src = "/public/images/broken.png";
                        model.raw.naturalWidth = 650;
                        model.raw.naturalHeight = 400;
                        resize(img, false);
                    }, 60*1000);
                } else {
                    img.src = 'http://' + model.raw.host + model.raw.url;
                    resize(img);
                }
                footer = this.child('.log-footer');
                footer.down('span').setHTML(Ext.String.format(
                    "时间:{0}", model.data.created_at
                ));
            },
            makeFooterVisible: function(){
                var footer = this.child('.log-footer');
                footer.setHeight(40);
            },
            prevImage: function(){
                var i, li, hasPrev = false;
                if(this.currentImageIndex === 0) {
                    try {
                        li = this.down('.selected').parent('li');
                        while(li) {
                            li = li.prev('li');
                            if(!li.down('.circle-off')) {
                                hasPrev = true;
                                break;
                            }
                        }
                        bbt.simulateClick(li.down('.circle').dom);
                    } catch(e) {}
                } else {
                    hasPrev = true;
                }
                if(!hasPrev) { return; }
                i = --this.currentImageIndex;
                i = this.setByModel(this.store.getAt(i));
                if(i === -1) { return; }
                this.makeFooterVisible();
            },
            nextImage: function(){
                var i, li, hasNext = false;
                if(this.currentImageIndex === (this.store.count()-1)) {
                    try {
                        li = this.down('.selected').parent('li');
                        while(li) {
                            li = li.next('li');
                            if(!li.down('.circle-off')) {
                                hasNext = true;
                                break;
                            }
                        }
                        bbt.simulateClick(li.down('.circle').dom);
                    } catch(e) {}
                } else {
                    hasNext = true;
                }
                if(!hasNext) { return; }
                i = ++this.currentImageIndex;
                i = this.setByModel(this.store.getAt(i));
                if(i === -1) { return; }
                this.makeFooterVisible();
            }
        });
        viewer.initViewerEvents();
        viewer.loadTimeAsixPage(-1);
    },
    suffle: function(level){
        var arr, i = 0, len, pos, tmp;
        tmp = Ext.Array.indexOf('province city country town school grade class'.split(' '), level);
        if(tmp <= 2) { //big level
            arr = this.allColors[1];
            this.fontColor = "#FFF";
        } else {
            arr = this.allColors[0];
            this.fontColor = "#8b7d72";
        }
        for(len=arr.length;i<len;i++) {
            pos = Math.floor(Math.random() * len);
            if(pos == i) { continue; }
            else {
                tmp = arr[i];
                arr[i] = arr[pos];
                arr[pos] = tmp;
            }
        }
        return arr;
    },
    prepareData: function(data, index, record) {
        data.bgcolor = this.colors[index%this.colors.length];
        data.fontColor = this.fontColor;
        data.firstChar = data.parent_name.charAt(0);
        data.top = 0;
        if(data.parent_name.length > 10) {
            data.group_text = data.parent_name.substr(0, 9)+'..';
        } else {
            data.group_text = data.parent_name;
            if(data.parent_name.length < 6) {
                data.top = -14;
            }
        }
        
        switch(data.node_type) {
            case 'room':
                data.majorText = data.pic_count + '次';
                data.juniorText = '桌面预览';
                break;
            case 'unit':
                data.majorText = data.room_count + '个教室';
                break;
            default:
                data.majorText = data.unit_count + '所教学点';
                data.juniorText = data.room_count + '个教室';
                break;
        }
        return data;
    }
});
/* 桌面预览 */
Ext.define('bbt.DesktopPreview', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.desktoppreview',
    initComponent: function(){
        var me = this, store = new Ext.data.Store({
            pageSize: 4,
            fields: ['grade_name', 'class_name', 'lesson_name', 'teacher_name', 'lesson_period_sequence', 'url'],
            proxy: {
                url: this.computerclass ? '/global/desktop-preview/computer-class/' : '/global/desktop-preview/',
                type: 'ajax',
                reader: {
                    type: 'json',
                    root: 'data.records',
                    totalProperty: 'data.record_count'
                }
            }
        });
        store.on('load', function(s){
            me.eachBlock(function(blk, i){
                var data = s.getAt(i);
                if(data) { data = data.raw; }
                else { data = {}; }
                blk = Ext.get(blk);
                blk.removeCls('preview-loading');
                me.fillBlock(blk.parent(), data);
            });
        });
        Ext.apply(this, {
            store: store,
            autoScroll: true,
            minWidth: 800,
            layout: {type: 'vbox', align: 'stretch'},
            defaultType: 'panel',
            defaults: {
                border: false,
                flex: 1
            },
            items: [{
                layout: {type: 'hbox', align: 'stretch'},
                defaults: {flex: 1, border: true},
                defaultType: 'panel',
                items: [{
                    margin: '5 2 2 5',
                    html: '<div class="desktop-preview"><img style="width:100%;height:100%;" src=""/></div><div class="preview-footer"><span></span><a class="open-viewer" href="javascript:void(0);"></a></div>'
                }, {
                    margin: '5 5 2 3',
                    html: '<div class="desktop-preview"><img style="width:100%;height:100%;" src=""/></div><div class="preview-footer"><span></span><a class="open-viewer" href="javascript:void(0);"></a></div>'
                }]
            }, {
                layout: {type: 'hbox', align: 'stretch'},
                defaults: {flex: 1, border: true},
                defaultType: 'panel',
                items: [{
                    margin: '3 2 5 5',
                    html: '<div class="desktop-preview"><img style="width:100%;height:100%;" src=""/></div><div class="preview-footer"><span></span><a class="open-viewer" href="javascript:void(0);"></a></div>'
                }, {
                    margin: '3 5 5 3',
                    html: '<div class="desktop-preview"><img style="width:100%;height:100%;" src=""/></div><div class="preview-footer"><span></span><a class="open-viewer" href="javascript:void(0);"></a></div>'
                }]
            }],
            listeners: {
                afterrender: function(){
                    var me = this, doc;
                    Ext.each(me.getEl().query('.desktop-preview'), function(el){
                        var footer;
                        el = Ext.get(el);
                        //img load event handle
                        el.down('img').on('load', function(e, element){
                            if(!element.naturalHeight) {
                                element.naturalWidth = element.width;
                                element.naturalHeight = element.height;
                            }
                        });
                        //block hover event
                        /*el.hover(function(){
                            Ext.get(this).next('.preview-footer').animate({
                                stopAnimation: true,
                                to: {
                                    marginTop: '-28px'
                                }
                            });
                        }, function(){
                            Ext.get(this).next('.preview-footer').animate({
                                stopAnimation: true,
                                to: {
                                    marginTop: '0px'
                                }
                            });
                        });*/
                        //footer hover event
                        footer = el.parent().down('.preview-footer');
                        /*footer.hover(function(){
                            var me = Ext.get(this);
                            me.animate({stopAnimation: true});
                            me.setStyle('marginTop', '-28px');
                        }, function(){
                            Ext.get(this).animate({
                                stopAnimation: true,
                                to: {
                                    marginTop: '0px'
                                }
                            });
                        });*/
                        footer.hover(function(){
                            this.style.zIndex = 20;
                        }, function(){
                            this.style.zIndex = "auto";
                        });
                        //footer open viewer
                        footer.down('.open-viewer').on('click', function(e, a){
                            var viewer = Ext.get(a).parent('.preview-footer').prev('.desktop-preview'), img;
                            img = viewer.down('img', true);
                            if(!img.src || img.src.indexOf(location.href) != -1) { return; }
                            
                            me.openViewer(viewer);
                        });
                    });
                    me.body.insertHtml('beforeEnd', '<a class="prev-page" href="javascript:void(0);"></a><a class="next-page" href="javascript:void(0);"></a>');
                    me.body.child('.prev-page').on('click', function(){
                        var pageCount = 0;
                        try {
                            pageCount = this.store.proxy.reader.rawData.data.page_count;
                            if(this.store.currentPage === 1) {
                                this.store.currentPage = pageCount;
                            } else {
                                this.store.currentPage--;
                            }
                            this.store.load();
                        } catch (e){}
                    }, me);
                    me.body.child('.next-page').on('click', function(){
                        var pageCount = 0;
                        try {
                            pageCount = this.store.proxy.reader.rawData.data.page_count;
                            if(this.store.currentPage === pageCount) {
                                this.store.currentPage = 1;
                            } else {
                                this.store.currentPage++;
                            }
                            
                            this.store.load();
                        } catch (e){}
                    }, me);
                }
            }
        });
        this.callParent();
    },
    openViewer: function(viewer){
        var img = viewer.down('img', true), w, h = 580, bg;
        if(!img.src) { return; }
        document.body.appendChild(img);
        w = h * img.naturalWidth / img.naturalHeight;
        img.style.cssText = Ext.String.format(
            "position:absolute;z-index:21;width:{0}px;height:{1}px;top:50%;left:50%;margin-left:-{2}px;margin-top:-{3}px;",
            w, h, w/2, h/2);
        bg = bbt.createOverlay(20);

        bg.$image = img;
        bg.onBeforeDestroy = function(element){
            var el = Ext.get(element.$image), frombox, tobox, from, to;
            frombox = el.getPageBox();
            from = {
                left: frombox.left + 'px',
                top: frombox.top + 'px',
                width: frombox.width + 'px',
                height: frombox.height + 'px'
            };
            tobox = viewer.getPageBox();
            to = {
                left: tobox.left + 'px',
                top: tobox.top + 'px',
                width: tobox.width + 'px',
                height: tobox.height + 'px'
            };
            element.$image.style.cssText = "position: absolute;z-index: 21;";
            el.animate({
                duration: 500,
                from: from,
                to: to,
                callback: function(){
                    viewer.appendChild(el);
                    el.dom.style.cssText = "width:100%;height:100%;";
                }
            });
            delete element.$image;
        };
    },
    eachBlock: function(cb){
        Ext.each(this.getEl().query('.desktop-preview'), cb);
    },
    fillBlock: function(block, data){
        var footer, img, info;
        if(!block.$cache) {
            block = Ext.get(block);
        }
        
        footer = block.down('.preview-footer');
        img = block.down('img', true);
        info = block.down('.preview-no-img');
        if(data && data.url) {
            info && info.hide();
            img.style.visibility = "visible";
            img.src = 'http://' + data.host + data.url;
            footer.down('span').setHTML(Ext.String.format('节次：{0} 班级：{1}年级{2}班 课程：{3} 授课教师：{4}', data.lesson_period_sequence, data.grade_name, data.class_name, data.lesson_name, data.teacher_name));
            footer.animate({to: {marginTop: "-28px"}});
        } else {
            img.style.visibility = "hidden";
            footer.down('span').setHTML('');
            footer.animate({to: {marginTop: "0px"}});
            if(!info) {
                footer.insertHtml('afterEnd', '<div class="preview-no-img">桌面预览：无</div>');
                info = block.down('.preview-no-img');
            }
            info.show();
        }
    },
    showWarn: function(){
        this.eachBlock(function(blk){
            blk = Ext.get(blk.parentNode);
            var overlay = document.createElement('div');
            overlay.setAttribute('data-remove', 'yes');
            overlay.style.cssText = "position:absolute;font-size:24px;top:0;right:0;bottom:0;left:0;text-align:center;background-color:#FFF;line-height:"+blk.getHeight()+"px;";
            overlay.style.fontFamily = "微软雅黑";
            overlay.innerHTML = "请点击某个学校后进行桌面预览！";
            blk.appendChild(overlay);
        });
    },
    removeWarn: function(){
        Ext.each(this.getEl().query('div[data-remove=yes]'), function(node){
            Ext.removeNode(node);
        });
    },
    onLevelChange: function(level, uuid){
        switch(level) {
            case 'school':
            case 'grade':
                if(this.__warn) {
                    this.removeWarn();
                    delete this.__warn;
                }
                this.store.proxy.extraParams.uuid = uuid;
                this.store.currentPage = 1;
                this.eachBlock(function(blk){
                    var c;
                    blk = Ext.get(blk);
                    blk.addCls('preview-loading');
                    c = blk.child('.preview-no-img');
                    c && c.hide();
                });
                this.store.load();
                break;
            default:
                /*if(!this.__warn) {
                    this.showWarn();
                    this.__warn = true;
                }*/
                break;
        }
        
    }
});
/* 桌面使用记录 */
Ext.define('bbt.DesktopPreviewLog', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.previewlog',
    
    layout: 'fit',
    initComponent: function(){
        this.tbar = [bbt.ToolBox.get('schoolYear', {useCurrent: true}),
        bbt.ToolBox.get('term'),
        {
            xtype: 'combo',
            value: 'class',
            editable: false,
            disabled: true,
            store: [['class', '按班级'], ['jieci', '按节次']],
            fieldLabel: '查询方式',
            labelWidth: 75,
            width: 150,
            hidden: true,
            myrole: 'querymethod'
        }, bbt.ToolBox.get('jieciOld', {disabled: true, hidden: true})];
        if(!bbt.UserInfo.isSchool()) {
            this.tbar.push({
                xtype: 'tbtext',
                cls: 'my-tbtext icon-toolbar'
            });
        }
        if(this.edupoint) {
            this.items = [{xtype: 'colorblockedu'}];
        } else {
            this.items = [{xtype: 'colorblock'}];
        }
        
        this.callParent();
    },
    listeners: {
        afterrender: function(){
            var view = this.items.getAt(0), toolbar = this.down('toolbar[dock=top]'), sy, term, qm, jieci, cb, crumbs;
            this.store = view.store;
            /* school year combo */
            sy = toolbar.down('[name=school_year]');
            sy.store.owner = sy;
            /*sy.store.on('refresh', function(){
                var o = this.owner, rc = this.getAt(0);
                if(rc) {
                    o.setValue(rc.get(o.valueField));
                }
            });*/
            sy.on('change', function(me, v){
                me.up('previewlog').store.proxy.extraParams.school_year = v;
            });

            /* term type combo */
            term = toolbar.down('[name=term_type]');
            term.on('change', function(me, v){
                var m, seq, store;
                store = me.up('previewlog').store;
                store.proxy.extraParams = {term_type: v, school_year: me.ownerCt.down('[name=school_year]').getValue()};
                try {
                    me.ownerCt.down('tbtext').getEl().setHTML('');
                } catch(e) {
                    //this is school server, ignore
                }
                
                try {
                    m = me.ownerCt.down('[myrole=querymethod]');
                    if(!m.isVisible()) {
                        throw new Error('xx');
                    }
                    seq = me.ownerCt.down('[name=lesson_period]');
                    if(!seq.isDisabled()) {
                        seq.setDisabled(true);
                    }
                    seq.store.reload();
                    m.setDisabled(!!!v);
                    
                    if(v) {
                        if(m.getValue() == 'class'){
                            m.fireEvent('change', m, 'class');
                        } else {
                            m.setValue('class');
                        }
                    }
                } catch(e) {
                    store.load();
                }
            });
            if(!this.edupoint) {
                /* query method combo */
                qm = toolbar.down('combo[myrole=querymethod]');
                qm.show();
                jieci = toolbar.down('combo[name=lesson_period]');
                jieci.show();
                qm.on('change', function(me, v){
                    var lp = me.ownerCt.down('combo[name=lesson_period]'), store;
                    if(v == "class") {
                        lp.setDisabled(true);
                        lp.setValue('');
                        store = me.up('previewlog').items.getAt(0).store;
                        delete store.proxy.extraParams.lesson_period_sequence;
                        delete store.proxy.extraParams.uuid;
                        //由于学年变化后直接引起学期变化，导致事件提前触发，学年未正确设置到proxy.extraParams
                        setTimeout(function(){ store.load(); }, 50);
                    } else if(v == "jieci") {
                        lp.setDisabled(false);
                        lp.setValue(lp.store.getAt(0).get(lp.valueField));
                    }
                    try {
                        me.ownerCt.down('tbtext').getEl().setHTML('');
                    } catch(e) {
                        //this is school server, ignore
                    }
                });
                /* jie ci combo */
                jieci.on('change', function(me, v){
                    var store = me.up('previewlog').items.getAt(0).store;
                    if(v === '所有') {
                        delete store.proxy.extraParams.lesson_period_sequence;
                    } else {
                        store.proxy.extraParams.lesson_period_sequence = v;
                    }
                    delete store.proxy.extraParams.uuid;
                    try {
                        me.ownerCt.down('tbtext').getEl().setHTML('');
                    } catch(e) {
                        //this is school server, ignore
                    }
                    //学年学期变化时，会重置节次为空，所以不考虑延后加载
                    store.load();
                });
                jieci.store.on('beforeload', function(){
                    this.proxy.extraParams = {school_year: sy.getValue(), term_type: term.getValue()};
                });
                jieci.store.on('load', function(s){
                    s.each(function(m){
                        if(m.data.value === "") {
                            s.remove(m);
                            return false;
                        }
                    });
                });
                jieci.store.load();
            }
            
            
            
            //this.store.load();
            //pagination
            this.body.insertHtml('beforeEnd', '<a class="prev-page" href="javascript:void(0);"></a><a class="next-page" href="javascript:void(0);"></a>');
            
            this.body.child('.prev-page').on('click', function(){
                if(this.store.currentPage === 1) { return; }
                this.store.currentPage--;
                this.store.isClickFromPager = true;
                this.store.load();
            }, this);
            this.body.child('.next-page').on('click', function(){
                var pageCount = 0;
                try {
                    pageCount = this.store.proxy.reader.rawData.data.page_count;
                    if((this.store.currentPage + 1) > pageCount) { return; }
                    this.store.currentPage++;
                    this.store.isClickFromPager = true;
                    this.store.load();
                } catch (e){}
            }, this);
            //load current year
            /* use `school_year`'s attribute useCurrent replace following code
            bbt.loadCurrentSchoolYear(function(opts, _, resp){
                var data = Ext.decode(resp.responseText);
                if(data.status == "success") {
                    sy.setValue(data.data.school_year);
                    term.setValue(data.data.term_type);
                }
            });*/
            //spread crumbs
            crumbs = toolbar.down('tbtext');
            if(!crumbs) { return; }
            view.crumbsEl = crumbs.getEl();
            view.crumbsEl.on('click', function(e){
                var me = this, t = e.target, type = t.getAttribute('data-type'), oldParams;
                Ext.each(me._stack, function(item){
                    if(item[1] === type) {
                        me.updateCrambs.apply(me, item);
                        me.store.currentPage = 1;
                        if(item[2] === null) {
                            oldParams = me.store.proxy.extraParams;
                            me.store.proxy.extraParams = {school_year: oldParams.school_year, term_type: oldParams.term_type};
                        } else {
                            Ext.apply(me.store.proxy.extraParams, item[2]);
                        }
                        return false;
                    }
                });
                me.store.load();
            }, view, {delegate: 'a[data-type]'});
        }
    }
});


/* 班班通授课综合分析 */
Ext.define('bbt.ComprehensiveAnalysis', {
    extend: 'Ext.tab.Panel',
    alias: 'widget.cphcount',
    initComponent: function(){
        var onColumnItemCreated = function(item){
            var series = item.series, exp = series.chart.extraParams, opacity = 0.5, prev, last, k;
            item.clearListeners();
            for(k in exp) {
                if(~k.indexOf('previous')) {
                    prev = true;
                } else if(~k.indexOf('lastyear')) {
                    last = true;
                }
            }
            switch(item.yFieldIndex) {
                case 1:
                    if(prev) {
                        opacity = 1;
                        series.showAll(1);
                    } else {
                        series.hideAll(1);
                    }
                    break;
                case 2:
                    if(last) {
                        opacity = 1;
                        series.showAll(2);
                    } else {
                        series.hideAll(2);
                    }
                    break;
                default:
                    return;
            }
            item.setAttributes({opacity: opacity}, true);
            item.on('click', function(){
                var c = this.series.chart, p, field = this.series.yField[this.yFieldIndex];
                if(typeof c.extraParams == "undefined") {
                    c.extraParams = {};
                }
                if(field in c.extraParams) {
                    delete c.extraParams[field];
                } else {
                    c.extraParams[field] = 'true';
                }
                p = c.up('panel');
                p.ownerCt.reloadPanel(p, 1);
            });
        }, onLineItemCreated = function(item){
            var series = item.series, exp = series.chart.extraParams||{}, opacity = 0.5, prev, last, k;
            item.clearListeners();
            if(~series.yField.indexOf('current')) { return; }
            try {
                if(series.yField in exp) {
                    opacity = 1;
                    series.showAll();
                } else {
                    series.hideAll();
                }
            } catch(e){}
            
            item.setAttributes({opacity: opacity}, true);
            item.on('click', function(){
                var c = this.series.chart, p, field = this.series.yField;
                if(typeof c.extraParams == "undefined") {
                    c.extraParams = {};
                }
                if(field in c.extraParams) {
                    delete c.extraParams[field];
                } else {
                    c.extraParams[field] = 'true';
                }
                p = c.up('panel');
                p.ownerCt.reloadPanel(p, 1);
            });
        };
        Ext.apply(this, {
            defaultType: 'panel',
            defaults: {border: false},
            items: [{
                layout: {type: 'vbox', align: 'stretch'},
                title: '课程授课次数分析',
                tbar: bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term', 'town', 'school']),
                method: 'teachCountByCourse',
                dataUrl: '/statistic/teaching-analysis/count/by-lesson/',
                delayTimer: null,
                getParams: function(){
                    var params = {};
                    Ext.each(this.down('toolbar').query('combo'), function(f){
                        f.name && (params[f.name] = f.getValue());
                    });
                    return params;
                },
                loadData: function(){
                    var me = this;
                    if(me.delayTimer !== null) { return; }
                    me.setLoading(true);
                    me.delayTimer = setTimeout(function(){
                        Ext.Ajax.request({
                            url: me.dataUrl,
                            params: me.getParams(),
                            method: 'GET',
                            success: function(resp){
                                var data = Ext.decode(resp.responseText);
                                if(data.status == "success") {
                                    me.up('tabpanel')[me.method](me, data.data, data.term);
                                } else {
                                    Ext.Msg.alert("提示", "服务器返回了错误的数据！");
                                }
                            },
                            failure: function(){
                                Ext.Msg.alert("提示", "加载数据失败！");
                            },
                            callback: function(){
                                me.setLoading(false);
                                me.delayTimer = null;
                            }
                        });
                    }, 50);
                },
                listeners: {
                    show: function(){
                        this.loadData();
                    },
                    afterrender: function(){
                        var tb = this.down('toolbar'), cb;
                        cb = function(){
                            this.up('panel').loadData();
                        };
                        tb.down('[name=town_name]').on('change', cb);
                        tb.down('[name=school_name]').on('change', cb);
                        tb.down('[name=term_type]').on('change', cb);
                    }
                }
            }, {
                xtype: 'panel',
                title: '年级授课次数分析',
                tbar: bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term', 'town', 'school']),
                layout: {type: 'vbox', align: 'stretch'},
                defaults: {flex: 1},
                url: '/statistic/teaching-analysis/count/by-grade/',
                items: [{
                    xtype: 'chart',
                    animate: false,
                    shadow: false,
                    store: new Ext.data.Store({
                        fields: ['grade_name', 'sum', 'class_count']
                    }),
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: ['sum'],
                        minorTickSteps: 1,
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['grade_name'],
                        label: {
                            renderer: function(v){
                                return v + "年级";
                            }
                        },
                        title: '年级授课次数分析'
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        gutter: 100,
                        highlight: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle('班级数：' + model.get('class_count'));
                            }
                        },
                        label: {
                            display: 'outside',
                            'text-anchor': 'middle',
                            field: ['sum']
                        },
                        xField: 'grade_name',
                        yField: ['sum']
                    }]
                }, {
                    xtype: 'chart',
                    style: {borderTop: '1px solid #99bce8 !important'},
                    animate: false,
                    shadow: false,
                    store: new Ext.data.Store({
                        fields: ['grade_name', 'sum', 'class_count']
                    }),
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: ['sum'],
                        minorTickSteps: 1,
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['grade_name'],
                        label: {
                            renderer: function(v){
                                return v + "年级";
                            }
                        },
                        title: '年级授课平均次数分析'
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        gutter: 100,
                        highlight: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle('班级数：' + model.get('class_count'));
                            }
                        },
                        label: {
                            display: 'outside',
                            'text-anchor': 'middle',
                            field: 'sum'
                        },
                        showInLegend: true,
                        xField: 'grade_name',
                        yField: 'sum'
                    }]
                }],
                reloadPanel: function(){
                    var me = this, params = {}, uuidRe = /(\w+\-)+\w+/i;
                    Ext.each(me.down('toolbar').query('combo'), function(c){
                        var v = c.getValue(), rc;
                        if(uuidRe.test(v)) {
                            rc = c.findRecordByValue(v);
                            v = rc.get(c.displayField);
                        }
                        params[c.name] = v;
                    });
                    me.setLoading(true);
                    Ext.Ajax.request({
                        url: me.url,
                        method: 'GET',
                        params: params,
                        callback: function(_1, _2, resp){
                            var data = Ext.decode(resp.responseText);
                            if(data.status == "success") {
                                me.reloadChart1(data.data);
                                me.reloadChart2(data.data);
                            }
                            me.setLoading(false);
                        }
                    });
                },
                reloadChart1: function(data){
                    var ret = Ext.Array.map(data, function(o){
                            return {grade_name: o.grade_name, sum: o.sum, class_count: o.class_count};
                        }),
                        grades = [null, "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"],
                        i = ret.length + 1;
                    for(;i<=12;i++) {
                        ret.push({grade_name: grades[i], sum: 0, class_count: 0});
                    }
                    this.items.get(0).store.loadData(ret);
                },
                reloadChart2: function(data){
                    var ret = Ext.Array.map(data, function(o){
                            return {grade_name: o.grade_name, sum: o.average, class_count: o.class_count};
                        }),
                        grades = [null, "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"],
                        i = ret.length + 1;
                    for(;i<=12;i++) {
                        ret.push({grade_name: grades[i], sum: 0, class_count: 0});
                    }
                    this.items.get(1).store.loadData(ret);
                },
                listeners: {
                    show: function(){
                        this.ownerCt.bindTools(this);
                        this.reloadPanel();
                    }
                }
            }, {
                xtype: 'panel',
                title: '周授课次数分析',
                tbar: bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term', 'town', 'school', 'grade', 'class']),
                layout: {type: 'vbox', align: 'stretch'},
                defaults: {flex: 1},
                items: [{
                    xtype: 'chart',
                    url: '/statistic/teaching-analysis/count/by-week/',
                    animate: false,
                    shadow: false,
                    store: new Ext.data.Store({
                        fields: [{name: 'week_count', defaultValue: 0}, 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: ['week_count'],
                        minorTickSteps: 1,
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课次数分析'
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        highlight: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(model.get(item.yField));
                            }
                        },
                        label: {
                            display: 'outside',
                            'text-anchor': 'middle',
                            field: ['week_count']
                        },
                        xField: 'week',
                        yField: ['week_count'],
                    }]
                }, {
                    xtype: 'chart',
                    style: {borderTop: '1px solid #99bce8 !important'},
                    url: '/statistic/teaching-analysis/count/by-week/average/',
                    animate: false,
                    shadow: false,
                    legend: {position: 'bottom', onItemCreated: onColumnItemCreated},
                    store: new Ext.data.Store({
                        fields: [{name: 'count_current', defaultValue: 0},{name: 'count_previous', defaultValue: 0}, {name: 'count_lastyear', defaultValue: 0}, 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: ['count_current', 'count_previous', 'count_lastyear'],
                        minorTickSteps: 1,
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课平均次数分析'
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        highlight: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(model.get(item.yField));
                            }
                        },
                        label: {
                            display: 'outside',
                            'text-anchor': 'middle',
                            field: ['count_current', 'count_previous', 'count_lastyear']
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: ['count_current', 'count_previous', 'count_lastyear'],
                        title: ['当前学期', '上学期', '上学年同学期']
                    }]
                }],
                listeners: {
                    show: function(){
                        this.ownerCt.reloadPanel(this);
                        this.ownerCt.bindTools(this);
                    }
                }
            }, {
                xtype: 'panel',
                title: '周授课时长分析',
                tbar: bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term', 'town', 'school', 'grade', 'class']),
                layout: {type: 'vbox', align: 'stretch'},
                defaults: {flex: 1},
                items: [{
                    xtype: 'chart',
                    url: '/statistic/teaching-analysis/time/by-week/',
                    animate: false,
                    shadow: false,
                    store: new Ext.data.Store({
                        fields: [{name:'week_time', defaultValue:0}, 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: ['week_time'],
                        minorTickSteps: 1,
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课时长分析'
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        highlight: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(model.get(item.yField));
                            }
                        },
                        label: {
                            display: 'outside',
                            'text-anchor': 'middle',
                            field: ['week_time']
                        },
                        xField: 'week',
                        yField: ['week_time']
                    }]
                }, {
                    xtype: 'chart',
                    style: {borderTop: '1px solid #99bce8 !important'},
                    url: '/statistic/teaching-analysis/time/by-week/average/',
                    animate: false,
                    shadow: false,
                    legend: {position: 'bottom', onItemCreated: onColumnItemCreated},
                    store: new Ext.data.Store({
                        fields: [{name:'time_current',defaultValue:0}, {name:'time_previous', defaultValue:0}, {name:'time_lastyear',defaultValue:0}, 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        position: 'left',
                        fields: ['time_current', 'time_previous', 'time_lastyear'],
                        minorTickSteps: 1,
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课平均时长分析'
                    }],
                    series: [{
                        type: 'column',
                        axis: 'left',
                        highlight: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(model.get(item.yField));
                            }
                        },
                        label: {
                            display: 'outside',
                            'text-anchor': 'middle',
                            field: ['time_current', 'time_previous', 'time_lastyear']
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: ['time_current', 'time_previous', 'time_lastyear'],
                        title: ['当前学期', '上学期', '上学年同学期']
                    }]
                }],
                listeners: {
                    show: function(){
                        this.ownerCt.reloadPanel(this);
                        this.ownerCt.bindTools(this);
                    }
                }
            }, {
                title: '周授课累积次数分析',
                tbar: bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term', 'town', 'school', 'grade', 'class']),
                layout: {type: 'vbox', align: 'stretch'},
                defaults: {flex: 1},
                items: [{
                    xtype: 'chart',
                    url: '/statistic/teaching-analysis/count/total/',
                    animate: true,
                    shadow: true,
                    store: new Ext.data.Store({
                        fields: ['total_count', 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        minorTickSteps: 1,
                        position: 'left',
                        fields: ['total_count'],
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课累积次数分析'
                    }],
                    series: [{
                        type: 'line',
                        axis: 'left',
                        highlight: true,
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        xField: 'week',
                        yField: 'total_count',
                    }]
                }, {
                    xtype: 'chart',
                    url: '/statistic/teaching-analysis/count/total/average/',
                    style: {borderTop: '1px solid #99bce8 !important'},
                    animate: true,
                    shadow: true,
                    legend: {position: 'bottom', onItemCreated: onLineItemCreated},
                    store: new Ext.data.Store({
                        fields: ['count_current', 'count_previous', 'count_lastyear', 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        minorTickSteps: 1,
                        position: 'left',
                        fields: ['count_current', 'count_previous', 'count_lastyear'],
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课累积平均次数分析'
                    }],
                    series: [{
                        type: 'line',
                        axis: 'left',
                        highlight: true,
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: 'count_current',
                        title: '当前学期'
                    }, {
                        type: 'line',
                        axis: 'left',
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: 'count_previous',
                        title: '上学期'
                    }, {
                        type: 'line',
                        axis: 'left',
                        highlight: true,
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: 'count_lastyear',
                        title: '上学年同学期'
                    }]
                }],
                listeners: {
                    show: function(){
                        this.ownerCt.reloadPanel(this);
                        this.ownerCt.bindTools(this);
                    }
                }
            }, {
                title: '周授课累积时长分析',
                tbar: bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term', 'town', 'school', 'grade', 'class']),
                layout: {type: 'vbox', align: 'stretch'},
                defaults: {flex: 1},
                items: [{
                    xtype: 'chart',
                    url: '/statistic/teaching-analysis/time/total/',
                    animate: true,
                    shadow: true,
                    store: new Ext.data.Store({
                        fields: ['total_time', 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        minorTickSteps: 1,
                        position: 'left',
                        fields: ['total_time'],
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课累积时长分析'
                    }],
                    series: [{
                        type: 'line',
                        axis: 'left',
                        highlight: true,
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        xField: 'week',
                        yField: 'total_time',
                    }]
                }, {
                    xtype: 'chart',
                    url: '/statistic/teaching-analysis/time/total/average/',
                    style: {borderTop: '1px solid #99bce8 !important'},
                    animate: true,
                    shadow: true,
                    legend: {position: 'bottom', onItemCreated: onLineItemCreated},
                    store: new Ext.data.Store({
                        fields: ['time_current', 'time_previous', 'time_lastyear', 'week']
                    }),
                    axes: [{
                        type: 'Numeric',
                        minorTickSteps: 1,
                        position: 'left',
                        fields: ['time_current', 'time_previous', 'time_lastyear'],
                        grid: true,
                        minimum: 0
                    }, {
                        type: 'Category',
                        position: 'bottom',
                        fields: ['week'],
                        label: {
                            renderer: function(v){
                                return "第" + v + "周";
                            }
                        },
                        title: '周授课累积平均时长分析'
                    }],
                    series: [{
                        type: 'line',
                        axis: 'left',
                        highlight: true,
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: 'time_current',
                        title: '当前学期'
                    }, {
                        type: 'line',
                        axis: 'left',
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: 'time_previous',
                        title: '上学期'
                    }, {
                        type: 'line',
                        axis: 'left',
                        highlight: true,
                        smooth: true,
                        tips: {
                            width: 100,
                            trackMouse: true,
                            renderer: function(model, item){
                                this.setTitle(item.value[1]||'0');
                            }
                        },
                        showInLegend: true,
                        xField: 'week',
                        yField: 'time_lastyear',
                        title: '上学年同学期'
                    }]
                }],
                listeners: {
                    show: function(){
                        this.ownerCt.reloadPanel(this);
                        this.ownerCt.bindTools(this);
                    }
                }
            }],
            listeners: {
                beforerender: function(){
                    bbt.autoArea(this);
                }
            }
        });
        this.callParent();
    },
    teachCountByCourse: function(cmp, data, term){
        var fields = [], c1data = {}, config, chart1, chart2, border, clone;
        clone = function(){
            var arr = Ext.Array.clone(fields), i = 0, len = arguments.length;
            for(;i<len;i++) {
                arr.push(arguments[i]);
            }
            return arr;
        };
        Ext.each(data, function(d){
            fields.push(d.name);
            c1data[d.name] = d.lesson_count;
        });
        c1data.term = term;
        
        chart1 = {
            xtype: 'chart',
            height: 150,
            cls: 'b-border',
            style: {borderTopWidth: '0px'},
            store: new Ext.data.Store({
                fields: clone('term'),
                data: c1data
            }),
            axes: [{
                type: 'category',
                fields: ['term'],
                position: 'left'
            }, {
                type: 'Numeric',
                position: 'bottom',
                fields: clone(),
                grid: true
            }],
            series: [{
                type: 'bar',
                stacked: true,
                highlight: true,
                tips: {
                    trackMouse: true,
                    width: 100,
                    renderer: function(model, item){
                        var sum = 0, data = model.data, v;
                        for(k in data) {
                            if(typeof data[k] == "number") {
                                sum += data[k]
                            }
                        }
                        if(sum == 0) {
                            v = 0;
                        } else {
                            v = model.get(item.yField) * 100 / sum;
                        }
                        
                        this.setTitle(item.yField + ": " + v.toFixed(2) + '%');
                    }
                },
                axis: 'bottom',
                xField: 'term',
                yField: clone()
            }],
            legend: {position: 'bottom'}
        };
        chart2 = {
            xtype: 'chart',
            flex: 1,
            border: false,
            axes: [{
                position: 'left',
                type: 'category',
                fields: ['name']
            }, {
                position: 'top',
                type: 'Numeric',
                grid: true,
                fields: ['lesson_count']
            }],
            series: [{
                type: 'bar',
                axis: 'left',
                gutter: 50,
                highlight: true,
                xField: 'name',
                yField: 'lesson_count',
                label: {
                    display: 'outside',
                    field: 'lesson_count'
                }
            }],
            store: new Ext.data.Store({
                fields: ['name', 'lesson_count'],
                data: data
            })
        };
        cmp.removeAll();
        cmp.add([chart1, chart2]);
    },
    reloadPanel: function(p, index){
        var me = this, charts = p.query('chart'), params = {}, uuidRe = /(\w+\-)+\w+/i;
        Ext.each(p.query('combo'), function(c){
            var v = c.getValue(), rc;
            if(uuidRe.test(v)) {
                rc = c.findRecordByValue(v);
                v = rc.get(c.displayField);
            }
            params[c.name] = v;
        });
        Ext.each(charts, function(c, i){
            var b = typeof index == "number" ? i === index : true;
            if(c.url.lastIndexOf('/average/') > -1) {
                b && me.loadAverageData(c, params);
            } else {
                b && me.loadGeneralData(c, params);
            }
        });
    },
    loadGeneralData: function(chart, params){
        chart.setLoading(true);
        Ext.Ajax.request({
            url: chart.url,
            method: 'GET',
            params: params,
            callback: function(_1, _2, resp){
                var data = Ext.decode(resp.responseText), i, len;
                if(data.status == "success") {
                    i = data.data.length, len = Math.max(20, i++);
                    for(;i<=len;i++) {
                        data.data.push({week: i});
                    }
                    chart.store.loadData(data.data);
                }
                chart.setLoading(false);
            }
        });
    },
    loadAverageData: function(chart, params){
        var req = chart.prevRequest;
        if(req) {
            Ext.Ajax.abort(req);
        }
        chart.setLoading(true);
        chart.extraParams && Ext.apply(params, chart.extraParams);
        chart.prevRequest = Ext.Ajax.request({
            url: chart.url,
            method: 'GET',
            params: params,
            callback: function(_1, _2, resp){
                var data = Ext.decode(resp.responseText), i, len;
                if(data && data.status == "success") {
                    i = data.data.length, len = Math.max(20, i++);
                    for(;i<=len;i++) {
                        data.data.push({week: i});
                    }
                    chart.store.loadData(data.data);
                }
                chart.setLoading(false);
            }
        });
    },
    bindTools: function(p){
        var tb = p.down('toolbar'), cb;
        if(p.hasBind) { return; }
        cb = function(){
            var op = this.up('panel');
            if(op.reloadPanel) {
                op.reloadPanel();
            } else {
                op.ownerCt.reloadPanel(op);
            }
        };
        Ext.each(tb.query('combo'), function(c){
            c.on('change', cb);
        });
        p.hasBind = true;
    }
});
/* 资源使用综合分析 */
Ext.define('bbt.ResourceUsage', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.resourceusage',
    initComponent: function(){
        this.tbar = bbt.ToolBox.convert([{tool: 'schoolYear', useCurrent: true}, 'term']);
        this.items = [{
            region: 'west',
            xtype: 'bbt_area',
            bodyCls: 'r-border',
            width: 200,
            split: true,
            //schoolFirst: true,
            expandAllNodes: false,
            autoLevel: bbt.UserInfo.level,
            pinyinSupport:true,
            quickSearch: true,
            skipComputerClass: true,
            hidden: bbt.UserInfo.isSchool()
        }, {
            region: 'center',
            xtype: 'container',
            layout: {type: 'vbox', align: 'stretch'},
            defaults: {border: true, flex: 1},
            items: [{
                xtype: 'container',
                layout: {type: 'hbox', align: 'stretch'},
                defaults: {border: true, flex: 1},
                items: [{
                    xtype: 'chart',
                    legend: {position: 'right'},
                    style: {borderLeft: '1px solid #99BCE8', backgroundColor: '#FFF'},
                    store: new Ext.data.Store({
                        fields: ['count', 'resource_from', 'rate', 'short_name']
                    }),
                    animate: true,
                    series: [{
                        type: 'pie',
                        angleField: 'count',
                        highlight: true,
                        showInLegend: true,
                        tips: {trackMouse: true, width: 120, renderer: function(r){ this.setTitle(r.get('resource_from') + ': ' + r.get('rate')); }},
                        label: {display: 'rotate', field: 'short_name', contrast: true}
                    }]
                }, {
                    xtype: 'chart',
                    legend: {position: 'right'},
                    style: {borderLeft: '1px solid #99BCE8', backgroundColor: '#FFF'},
                    store: new Ext.data.Store({
                        fields: ['count', 'resource_type', 'rate', 'short_name']
                    }),
                    animate: true,
                    series: [{
                        type: 'pie',
                        highlight: true,
                        showInLegend: true,
                        angleField: 'count',
                        tips: {trackMouse: true, width: 120, renderer: function(r){ this.setTitle(r.get('resource_type') + ': ' + r.get('rate')); }},
                        label: {display: 'rotate', field: 'short_name', contrast: true}
                    }]
                }]
            }, {
                xtype: 'chart',
                style: {borderLeft: '1px solid #99BCE8', borderTop: '1px solid #99BCE8', backgroundColor: '#FFF'},
                store: new Ext.data.Store({
                    fields: ['count', 'name']
                }),
                animate: true,
                axes: [{
                    type: 'Numeric',
                    position: 'left',
                    fields: ['count'],
                    title: '资源使用次数（TOP10）',
                    minimum: 0,
                    maximum: 200
                }, {
                    type: 'Category',
                    position: 'bottom',
                    fields: ['name'],
                    label: {renderer:function(v){
                        if(v && v.length > 5) {
                            return v.substring(0, 5)+'...';
                        }
                        return v;
                    }}
                }],
                series: [{
                    type: 'column',
                    axis: 'left',
                    style: {width: 32},
                    gutter: 100,
                    highlight: true,
                    tips: {trackMouse: true, width: 140, renderer: function(r){ this.setTitle(r.get('name')+': '+r.get('count')); }},
                    label: {display: 'insideEnd', field: 'count', contrast: true},
                    xField: 'name',
                    yField: 'count'
                }]
            }],
            prevType: null,
            prevUuid: null,
            onLevelChange: function(type, uuid){
                var me = this, tb = me.up('resourceusage').down('toolbar[dock=top]'), params;
                if(typeof type == "undefined") {
                    type = me.prevType;
                }
                if(typeof uuid == "undefined") {
                    uuid = me.prevUuid;
                }
                params = {uuid: uuid, type: type, school_year: tb.down('[name=school_year]').getValue(), term_type: tb.down('[name=term_type]').getValue()};
                Ext.Ajax.request({
                    url: "/statistic/resource-global/",
                    params: params,
                    method: 'GET',
                    callback: function(_1, _2, resp){
                        var data = Ext.decode(resp.responseText);
                        if(data.status == "success") {
                            me._parse(data.data.resource_from, data.data.resource_type, data.data.top);
                        } else {
                            console.log(data.msg);
                        }
                    }
                });
                me.prevType = type;
                me.prevUuid = uuid;
            },
            _parse: function(resource_from, resource_type, top10){
                var charts = this.query('chart'), store, max = 0;
                store = charts[0].store;
                Ext.Array.each(resource_from.records, function(item){
                    if(item.resource_from.length > 5) {
                        item.short_name = item.resource_from.substring(0, 4) + '...';
                    } else {
                        item.short_name = item.resource_from;
                    }
                    item.rate = resource_from.sum === 0 ? "..%" : (item.count * 100 / resource_from.sum).toFixed(2)+'%'
                });
                store.removeAll();
                store.loadData(resource_from.records);
                store = charts[1].store;
                Ext.Array.each(resource_type.records, function(item){
                    if(item.resource_type.length > 5) {
                        item.short_name = item.resource_type.substring(0, 4) + '...';
                    } else {
                        item.short_name = item.resource_type;
                    }
                    item.rate = resource_type.sum === 0 ? "..%" : (item.count * 100 / resource_type.sum).toFixed(2)+'%'
                });
                store.removeAll();
                store.loadData(resource_type.records);
                store = charts[2].store;
                Ext.each(top10, function(item){
                    max = max > item.count ? max : item.count;
                });
                charts[2].axes.getAt(0).maximum = Math.floor(max / 10) * 10 + 10;
                store.removeAll();
                store.loadData(top10);
            }
        }];
        this.listeners = {
            afterrender: function(){
                var query = this.down('toolbar[dock=top]').query('combo'), cb, timer;
                cb = function(){
                    var cp = this.up('resourceusage').down('[region=center]');
                    if(timer) {
                        clearTimeout(timer);
                    }
                    timer = setTimeout(function(){ cp.onLevelChange(); }, 100);
                };
                Ext.each(query, function(c){
                    c.on('change', cb);
                });
                if(bbt.UserInfo.isSchool()) {
                    this.down('[region=center]').onLevelChange();
                }
            }
        };
        this.layout = 'border';
        //this.defaults = {border: false};
        this.title = '资源使用 > 资源使用综合分析';
        this.callParent();
    }
});

Ext.define('bbt.About', {
    extend: 'Ext.window.Window',
    alias: 'widget.bbt_about',
    getDetails: function(){
        var win = this;
        apiRequest.target = win;
        apiRequest('/system/about/', {}, function(data){
            var form = win.down('form').getForm();
            Ext.Object.each(data.data, function(k, v){
                var f = form.findField(k);
                f && f.setValue(v);
            });
        });
    },
    initComponent: function(){
        Ext.apply(this, {
            layout: 'fit',
            modal: true,
            width: 400,
            height: 300,
            bodyStyle: {background: 'url(/public/images/logo.png) no-repeat 47% 11%'},
            resizable: false,
            closable: false,
            items: [{
                xtype: 'form',
                border: false,
                margin: 30,
                bodyCls: 'no-bg',
                defaultType: 'displayfield',
                layout: 'anchor',
                defaults: {margin: 15},
                items: [{
                    fieldLabel: '产品名称',
                    name: 'product_name',
                    value: '噢易班班通管理分析系统',
                    margin: '90 7 7 15'
                }, {
                    fieldLabel: '版本号',
                    name: 'version',
                    value: ''
                }, {
                    fieldLabel: '版权所有',
                    name: 'copyright',
                    value: '武汉噢易云计算股份有限公司'
                }, {
                    hidden: true,
                    fieldLabel: '软件授权',
                    name: 'privilege',
                    value: ''
                }]
            }],
            buttons: [{
                text: '关闭',
                action: 'destroy'
            }],
            buttonAlign: 'center',
            listeners: {
                afterrender: function(){
                    this.down('button[action=destroy]').setHandler(this.destroy, this);
                }
            }
        });
        this.callParent();
        this.show();
        this.getDetails();
    }
});
Ext.define('bbt.Activation', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.bbt_activation',
    initComponent: function(){
        this.bodyStyle = {background: 'url(/public/images/logo.png) no-repeat left top'},
        this.bodyCls = 'no-bg';
        this.layout = 'column';
        this.defaults = {columnWidth: 1, margin: '7 15'};
        this.defaultType = 'displayfield';
        this.items = [{
            fieldLabel: '产品名称',
            name: 'product_name',
            value: '噢易班班通管理分析系统',
            fieldBodyCls: 'product_name',
            margin: '90 7 7 15'
        }, {
            fieldLabel: '授权状态',
            name: 'status',
            value: '未授权'
        }, {
            fieldLabel: '授权区域',
            name: 'area',
            value: '',
            hidden: true
        }, {
            fieldLabel: '授权终端数',
            name: 'number',
            value: '',
            hidden: true
        }, {
            fieldLabel: '授权年限',
            name: 'year',
            value: '',
            hidden: true
        }, {
            xtype: 'container',
            name: 'bottom',
            hidden: true,
            height: 22,
            layout: 'column',
            items: [{
                xtype: 'component',
                name: 'useinfo',
                template: new Ext.XTemplate(bbt.UserInfo.isSchool()?'班班通教室已授权：{class_count}、电脑教室已授权：{class_computer_count}':'学校终端已授权：{school_count}、教学点终端已授权：{edu_point_count}')
            }, {
                xtype: 'button',
                text: '更新授权',
                margin: '0 0 0 20',
                handler: function(me, e){
                    e.preventDefault();
                    e.stopPropagation();
                    me.up('bbt_activation').showLicenseWindow(me.text);
                }
            }]
            
        }];
        this.listeners = {
            afterrender: this._autoHideActivateWindow,
            beforedestroy: this._onBeforeDestroy
        };
        this.callParent();
        this.show();
        this.loadActivateInfomation();
    },
    loadActivateInfomation: function(){
        var me = this;
        me.setLoading(true);
        Ext.Ajax.request({
            url: '/activation/api/has_activate/',
            method: 'GET',
            callback: function(_1, _2, resp){
                var data = Ext.decode(resp.responseText);
                me.setLoading(false);
                //debug: me.applyActivateInfomation({}, true);
                if(data.status == "success") {
                    data = data.data;
                    if(data.is_active) {
                        me.applyActivateInfomation(data.info, data.active_status);
                    } else {
                        me.showLicenseWindow();
                    }
                } else {
                    me.showLicenseWindow();
                }
            }
        });
    },
    sendLicense: function(license){
        var me = this;
        if(!license) {
            return false;
        }
        me.setLoading(true);
        Ext.Ajax.request({
            url: '/activation/activate/',
            method: 'POST',
            params: {activate_key: license},
            callback: function(_1, suc, resp){
                var data = suc ? Ext.decode(resp.responseText) : null;
                me.setLoading(false);
                if(!data) {
                    Ext.Msg.alert('提示', '服务器错误！', function(){
                        me.showLicenseWindow();
                    });
                } else if(data.status == "success") {
                    me.loadActivateInfomation();
                } else {
                    Ext.Msg.alert('提示', data.msg, function(){
                        me.showLicenseWindow();
                    });
                }
            }
        })
    },
    applyActivateInfomation: function(data, status){
        var me = this, dv = '0', tmp, sm;
        sm = {
            on: '已激活',
            off: '未激活',
            overtime: '超出授权时间',
            waittime: '未到授权时间',
            overnumber: '授权点数已全部使用'
        };
        me.down('[name=status]').show().setValue(sm[status]);
        me.down('[name=area]').show().setValue(data.area);
        me.down('[name=number]').show().setValue(data.quota || dv);
        me.down('[name=year]').show().setValue(data.start_date ? (data.start_date + '~' + data.end_date) : dv);
        me.down('[name=bottom]').show();
        tmp = me.down('[name=useinfo]').show();
        if(bbt.UserInfo.isSchool()) {
            tmp.el.setHTML(tmp.template.apply({class_count: data.class_count || dv, class_computer_count: data.class_computer_count || dv}));
            me.down('button').hide();
        } else {
            tmp.el.setHTML(tmp.template.apply({school_count: data.school_count || dv, edu_point_count: data.edu_point_count || dv}));
        }
        me.el[status=='overtime'?'addCls':'removeCls']('form_error');
        me.activated = true;
    },
    showLicenseWindow: function(btnText){
        var winc, box = this.down('[name=status]').getBox();
        if(this._window || bbt.UserInfo.isSchool()) { return; }
        winc = {
            xtype: 'window',
            x: this.getBox().x,
            y: box.y + box.height + 5,
            header: false,
            baseCls: '',
            resizable: false,
            closable: false,
            owner: this,
            width: 400,
            layout: 'fit',
            items: [{
                xtype: 'form',
                layout: 'column',
                
                items: [{
                    xtype: 'component',
                    columnWidth: 1,
                    margin: '10 0 0 10',
                    html: '请输入产品序列号'
                }, {
                    xtype: 'container',
                    columnWidth: 0.8,
                    layout: 'hbox',
                    defaults: {margin: '10 0 20 10', width: 60, regex: /^\d*$/, maxLength: 4},
                    defaultType: 'textfield',
                    items: [{
                        name: 'k1'
                    }, {
                        name: 'k2'
                    }, {
                        name: 'k3'
                    }, {
                        name: 'k4'
                    }]
                }, {
                    xtype: 'button',
                    columnWidth: 0.2,
                    margin: '10 10 0 0',
                    text: btnText || '激活',
                    handler: function(){
                        var win = this.up('window'), fm = win.down('form').getForm(), k = [];
                        k.push(fm.findField('k1').getValue());
                        k.push(fm.findField('k2').getValue());
                        k.push(fm.findField('k3').getValue());
                        k.push(fm.findField('k4').getValue());
                        if(false === win.owner.sendLicense(k.join(''))) {
                            return
                        }
                        win.destroy();
                    }
                }]
            }],
            listeners: {
                beforedestroy: function(){
                    delete this.owner._window;
                }
            }
        };
        this._window = Ext.widget(winc);
        this._window.show();
    },
    _autoHideActivateWindow: function(){
        this.body.on('click', function(){
            if(this.activated && this._window) {
                this._window.destroy();
                delete this._window;
            }
        }, this);
    },
    _onBeforeDestroy: function(){
        if(this._window) {
            this._window.destroy();
            delete this._window;
        }
    }
});

Ext.define('bbt.NewFeature', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.new_feature',
    initComponent: function(){
        var me = this;
        me.border = false;
        me.layout = 'absolute';
        me.bodyStyle = {backgroundColor: '#d7e4f5'};
        me.items = [{
            xtype: 'image',
            width: 841,
            height: 481,
            src: '/public/images/new-feature.jpg'
        }, {
            xtype: 'component',
            hidden: true,
            height: 30,
            width: 450,
            html: '<p class="wryh" style="font-size:24px;line-height:30px;white-space: nowrap;">功能暂未开放，敬请期待系统更新！</p>'
        }];
        me.listeners = {
            beforedestroy: function(){
                if(this.currentAnim) {
                    Ext.fx.Manager.removeAnim(this.currentAnim);
                }
            },
            afterrender: function(){
                var x, img = this.down('image'), anim;
                x = this.getWidth() - img.getWidth();
                img.setPosition(x, -70, false);
                anim = new Ext.fx.Anim({
                    target: img.el,
                    stopAnimation: true,
                    easing: 'backIn',
                    delay: 300,
                    duration: 800,
                    to: {
                        top: '0px'
                    },
                    callback: function(){
                        me.showText();
                    }
                });
                me.currentAnim = anim;
                me.el.insertHtml('beforeEnd', '<div style="position:absolute;top:0;left:0;bottom:0;right:0;z-index:100;"></div>');
            }
        };
        me.callParent();
    },
    showText: function(){
        var cmp = this.down('component[hidden=true]'), x, y;
        x = (this.getWidth() - 450) / 2;
        y = (this.getHeight() - cmp.getHeight()) / 2;
        cmp.setPosition(x, y + 80);
        cmp.show();
        cmp.setPosition(x, y, true);
    }
});
Ext.chart.Legend.prototype.createItems = function() {
        var me = this,
            chart = me.chart,
            seriesItems = chart.series.items,
            ln, series,
            surface = chart.surface,
            items = me.items,
            padding = me.padding,
            itemSpacing = me.itemSpacing,
            spacingOffset = 2,
            maxWidth = 0,
            maxHeight = 0,
            totalWidth = 0,
            totalHeight = 0,
            vertical = me.isVertical,
            math = Math,
            mfloor = math.floor,
            mmax = math.max,
            index = 0,
            i = 0,
            len = items ? items.length : 0,
            x, y, spacing, item, bbox, height, width,
            fields, field, nFields, j;

        //remove all legend items
        if (len) {
            for (; i < len; i++) {
                items[i].destroy();
            }
        }
        //empty array
        items.length = [];
        // Create all the item labels, collecting their dimensions and positioning each one
        // properly in relation to the previous item
        for (i = 0, ln = seriesItems.length; i < ln; i++) {
            series = seriesItems[i];
            if (series.showInLegend) {
                fields = [].concat(series.yField);
                for (j = 0, nFields = fields.length; j < nFields; j++) {
                    field = fields[j];
                    item = new Ext.chart.LegendItem({
                        legend: this,
                        series: series,
                        surface: chart.surface,
                        yFieldIndex: j,
                        listeners: this.itemListeners
                    });
                    if(this.onItemCreated) {
                        this.onItemCreated(item);
                    }
                    bbox = item.getBBox();

                    //always measure from x=0, since not all markers go all the way to the left
                    width = bbox.width;
                    height = bbox.height;

                    if (i + j === 0) {
                        spacing = vertical ? padding + height / 2 : padding;
                    }
                    else {
                        spacing = itemSpacing / (vertical ? 2 : 1);
                    }
                    // Set the item's position relative to the legend box
                    item.x = mfloor(vertical ? padding : totalWidth + spacing);
                    item.y = mfloor(vertical ? totalHeight + spacing : padding + height / 2);

                    // Collect cumulative dimensions
                    totalWidth += width + spacing;
                    totalHeight += height + spacing;
                    maxWidth = mmax(maxWidth, width);
                    maxHeight = mmax(maxHeight, height);

                    items.push(item);
                }
            }
        }

        // Store the collected dimensions for later
        me.width = mfloor((vertical ? maxWidth : totalWidth) + padding * 2);
        if (vertical && items.length === 1) {
            spacingOffset = 1;
        }
        me.height = mfloor((vertical ? totalHeight - spacingOffset * spacing : maxHeight) + (padding * 2));
        me.itemHeight = maxHeight;
    };
