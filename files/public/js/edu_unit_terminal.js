var programVersion = "V4.0.0", cpuId, ui, sock, Task, utils, DEBUG = true, DEV = false;
(function(global){"use strict";var _Base64=global.Base64;var version="2.1.6";var buffer;if(typeof module!=="undefined"&&module.exports){buffer=require("buffer").Buffer}var b64chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";var b64tab=function(bin){var t={};for(var i=0,l=bin.length;i<l;i++)t[bin.charAt(i)]=i;return t}(b64chars);var fromCharCode=String.fromCharCode;var cb_utob=function(c){if(c.length<2){var cc=c.charCodeAt(0);return cc<128?c:cc<2048?fromCharCode(192|cc>>>6)+fromCharCode(128|cc&63):fromCharCode(224|cc>>>12&15)+fromCharCode(128|cc>>>6&63)+fromCharCode(128|cc&63)}else{var cc=65536+(c.charCodeAt(0)-55296)*1024+(c.charCodeAt(1)-56320);return fromCharCode(240|cc>>>18&7)+fromCharCode(128|cc>>>12&63)+fromCharCode(128|cc>>>6&63)+fromCharCode(128|cc&63)}};var re_utob=/[\uD800-\uDBFF][\uDC00-\uDFFFF]|[^\x00-\x7F]/g;var utob=function(u){return u.replace(re_utob,cb_utob)};var cb_encode=function(ccc){var padlen=[0,2,1][ccc.length%3],ord=ccc.charCodeAt(0)<<16|(ccc.length>1?ccc.charCodeAt(1):0)<<8|(ccc.length>2?ccc.charCodeAt(2):0),chars=[b64chars.charAt(ord>>>18),b64chars.charAt(ord>>>12&63),padlen>=2?"=":b64chars.charAt(ord>>>6&63),padlen>=1?"=":b64chars.charAt(ord&63)];return chars.join("")};var btoa=global.btoa?function(b){return global.btoa(b)}:function(b){return b.replace(/[\s\S]{1,3}/g,cb_encode)};var _encode=buffer?function(u){return new buffer(u).toString("base64")}:function(u){return btoa(utob(u))};var encode=function(u,urisafe){return!urisafe?_encode(String(u)):_encode(String(u)).replace(/[+\/]/g,function(m0){return m0=="+"?"-":"_"}).replace(/=/g,"")};var encodeURI=function(u){return encode(u,true)};var re_btou=new RegExp(["[À-ß][-¿]","[à-ï][-¿]{2}","[ð-÷][-¿]{3}"].join("|"),"g");var cb_btou=function(cccc){switch(cccc.length){case 4:var cp=(7&cccc.charCodeAt(0))<<18|(63&cccc.charCodeAt(1))<<12|(63&cccc.charCodeAt(2))<<6|63&cccc.charCodeAt(3),offset=cp-65536;return fromCharCode((offset>>>10)+55296)+fromCharCode((offset&1023)+56320);case 3:return fromCharCode((15&cccc.charCodeAt(0))<<12|(63&cccc.charCodeAt(1))<<6|63&cccc.charCodeAt(2));default:return fromCharCode((31&cccc.charCodeAt(0))<<6|63&cccc.charCodeAt(1))}};var btou=function(b){return b.replace(re_btou,cb_btou)};var cb_decode=function(cccc){var len=cccc.length,padlen=len%4,n=(len>0?b64tab[cccc.charAt(0)]<<18:0)|(len>1?b64tab[cccc.charAt(1)]<<12:0)|(len>2?b64tab[cccc.charAt(2)]<<6:0)|(len>3?b64tab[cccc.charAt(3)]:0),chars=[fromCharCode(n>>>16),fromCharCode(n>>>8&255),fromCharCode(n&255)];chars.length-=[0,0,2,1][padlen];return chars.join("")};var atob=global.atob?function(a){return global.atob(a)}:function(a){return a.replace(/[\s\S]{1,4}/g,cb_decode)};var _decode=buffer?function(a){return new buffer(a,"base64").toString()}:function(a){return btou(atob(a))};var decode=function(a){return _decode(String(a).replace(/[-_]/g,function(m0){return m0=="-"?"+":"/"}).replace(/[^A-Za-z0-9\+\/]/g,""))};var noConflict=function(){var Base64=global.Base64;global.Base64=_Base64;return Base64};global.Base64={VERSION:version,atob:atob,btoa:btoa,fromBase64:decode,toBase64:encode,utob:utob,encode:encode,encodeURI:encodeURI,btou:btou,decode:decode,noConflict:noConflict};if(typeof Object.defineProperty==="function"){var noEnum=function(v){return{value:v,enumerable:false,writable:true,configurable:true}};global.Base64.extendString=function(){Object.defineProperty(String.prototype,"fromBase64",noEnum(function(){return decode(this)}));Object.defineProperty(String.prototype,"toBase64",noEnum(function(urisafe){return encode(this,urisafe)}));Object.defineProperty(String.prototype,"toBase64URI",noEnum(function(){return encode(this,true)}))}}})(this);Base64.extendString()
//默认离线
app.window.tray_icon("set_icon", "Icon_off.ico");
//constant variables
$.each({
	SNAPSHOT_INTERVAL: 1 * 60 * 1000,
	TRAY_ICON_BLINK: 300,
	OFFLINE_NOTIFICATION_INTERVAL: 5 * 60 * 1000,
	UPLOAD_IMG_INTERVAL: 10 * 60 * 1000
}, function(k, v){
	window[k] = v;
});
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
			setOnline(false);
			socket.onopen = null;
			socket.onmessage = null;
			socket.onclose = null;
			socket = null;
			utils.trayBlink('stop');
			console.log('%cWebSocket onclose ...', 'color:red');
			if(me._destroyed) { return; }
			else {
				if(timer) { return; }
				timer = setTimeout(function(){
					me._socket = buildSocket();
					timer = null;
					console.log("rebuild websocket instance!");
				}, 10000);
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
			me._readyCallback.forEach(function(fn){
				fn.call(me);
			});
			while(me._queue.length) {
				me._socket.send(me._queue.shift());
			}
			console.log("websocket was opened!");
			setOnline(true);
			if(!utils.isReported()) {
				utils.trayBlink();
			}
		};
		return socket;
	};
	me._socket = buildSocket();
}

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
				me._queue.push(JSON.stringify(data));
			}
		} catch(e) {
			console.log(e);
			delete me[key];
		}
	},
	//包装主动请求的消息
	request: function(operation, data, category, callback){
		if(arguments.length == 3) {
			callback = category;
			category = "edu-unit";
		}
		this.emit({category: category, operation: operation, data: data}, function(e, data){
			if(e) {
				callback && callback(e);
			} else {
				if(data.ret === 0) {
					callback && callback(null, data);
				} else {
					data.msg && console.log('%c[SERVER] ' + data.msg, 'color: red;');
					callback && callback(data.msg || ERRORMSG[data.ret] || "unknow error");
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
	},
	login: function(callback){
		this.request('login', {'hardware-id': cpuId/*, version: programVersion*/}, function(e, data){
			//setOnline(data && data.ret === 0);
			callback && callback(e, data);
		});
	},
	queryKey: function(key, callback){
		this.request('query-key', {key: key}, callback);
	},
	report: function(keys, callback){
		var me = this;
		me.request('report', {key: keys, 'hardware-id': cpuId}, function(e, data){
			if(data && data.reported === true) {
				utils.trayBlink('stop');
				DEBUG && console.log("清除历史记录");
				app.utils.collection_times("clear_collect_times")
				app.utils.collection_ldletimes("clear_collect_times");
				app.file.write(utils.appRoot + 'status.dat', '');
				//trigger login
				me._readyCallback.forEach(function(fn){
					fn.call(me);
				});
			}
			callback && callback(e, data);
		});
	},
	getStatus: function(callback){
		this.request('status', {'hardware-id': cpuId}, function(e, data){
			if(data && data.ret === 0) {
				app.file.write(utils.appRoot + 'status.dat', JSON.stringify(data).toBase64());
				ui.showInfo();
			}
			callback && callback(e, data);
		});
	},
	getSettingInfo: function(callback){
		this.request('setting-info', {}, callback);
	},
	lastUploadTime: function(type, callback){
		this.request('classroom-query-date', {'hardware-id': cpuId, func: type}, callback);
	},
	getDirectoryInfo: function(callback){
		this.request('lookups-path', {'hardware-id': cpuId}, callback);
	},
	sendMachineTimeMsg: function(data, callback){
		this.request('classroom-machine-time', data, callback);
	},
	sendSnapshotMsg: function(data, callback){
		this.request('screen-upload', data, callback);
	},
	sendFileChangedMsg: function(data, callback){
		this.request('file-analysis', data, callback);
	},
	_readyCallback: [],
	ready: function(fn){
		this._readyCallback.push(fn);
	}
};

window.setOnline = function(flag){
	if(flag === window._online) { return; }
	if(typeof window._online == "undefined") {
		utils.networkMonitor();
	}
	if(flag === true) {
		window._online = true;
		window.lastOfflineTime = -1;
		if(window.START_UPLOAD_WHEN_ONLINE) {
			Task.start('uploadimg');
		}
	} else if(flag === false) {
		window._online = false;
		window.lastOfflineTime = Date.now();
	}
	if($('#page-report').is(":visible")) {
		$('#offline-indicator')[flag?'hide':'show']();
	}
	if(!utils._blinkTimer) {
		app.window.tray_icon("set_icon", "Icon_" + (flag?'on':'off') + ".ico");
	}
};

window.isOnline = function(){
	return window._online;
};

ui = {
	initSettingUI: function(){
		var modal;
		$('.report-footer').children('button').click(function(){
			var me = $(this), msgObj = me.closest('.item').children('.footer-msg'), keys, tmp;
			switch(me.attr('action')) {
				case 'select':
					if(!ui.checkTerminalType()) {
						msgObj.text('至少选择一个');
						return;
					} else {
						msgObj.text('');
						$('#key-recv').closest('form').siblings('.footer-msg').text('');
					}
					break;
				case 'required':
					tmp = ui.checkKeyEmpty();
					if(typeof tmp == "undefined") {
						msgObj.text('');
					} else {
						msgObj.text({required: '请输入密钥', invalid: '密钥无效'}[tmp]);
						return;
					}
			}
			switch(me.attr('role')) {
				case 'prev':
					$('#myCarousel').carousel('prev');
					break;
				case 'next':
					$('#myCarousel').carousel('next');
					break;
				case 'checkkey':
					keys = [];
					$.each({moon: 'recv', room: 'class'}, function(k, v){
						var group = $('#key-' + v);
						if(group.css('display') == "block") {
							keys.push({type: k, key: group.find('input').val()});
						}
					});
					ui.showLoading();
					sock.queryKey(keys, function(e, data){
						ui.hideLoading();
						if(data && data.ret === 0) {
							$('#myCarousel').carousel('next');
							$('#report-location').children('.value').text([data.data.province_name, data.data.city_name, data.data.country_name, data.data.town_name].join(''));
							$('#report-name').children('.value').text(data.data.point_name);
							$('#report-type').children('.value').text(data.type.map(function(v){
								return {room: '教室终端', moon: '卫星接收终端'}[v];
							}).join('、'));
							if(data.data.name) {
								$('#report-no').children('.value').text("第 " + data.data.name + " 教室");
							} else {
								$('#report-no').hide();
							}
							
						} else {
							msgObj.text(e ? (e.message || e) : data.msg);
						}
					});
					break;
				case 'submit':
					keys = [];
					$.each({moon: 'recv', room: 'class'}, function(k, v){
						var group = $('#key-' + v);
						if(group.css('display') == "block") {
							keys.push({type: k, key: group.find('input').val()});
						}
					});
					$('#submit-confirm').modal('show');
					$('#submit-confirm').data('callback', function(){
						ui.showLoading();
						sock.report(keys, function(e, data){
							ui.hideLoading();
							if(e) {
								alert(e.message || e);
							} else {
								if(data.ret === 0) {
									ui.showInfo();
								} else {
									alert(data.msg);
								}
							}
							
						});
					});
					break;
			}
		});
		$('#select-type').find('.text').click(function(e){
			var ipt = $(this).children('input')[0];
			if(ipt === e.target) { return; }
			ipt.checked = !ipt.checked;
		});
		$('#key-class,#key-recv').keydown(function(e){
			var len = $(this).find('input').val().length, code = e.keyCode;
			if(!(code in {8:'',37:'',39:'',46:''}) && len >= 16) {
				e.stopPropagation();
				e.preventDefault();
				return false;
			}
		});
		$('#myCarousel').carousel({interval: false});
		modal = $('#submit-confirm');
		modal.find('a[action]').click(function(e){
			var action = e.target.getAttribute('action'), m = $('#submit-confirm'), _modal, cb;
			if(action == "close") {
				m.modal('hide');
			} else if(action = "submit") {
				_modal = m.data('modal');
				_modal.$element.hide();
				_modal.removeBackdrop();
				_modal.$element.trigger('hidden')
				m.data('callback')();
				m.removeData('callback');
			}
		});
		modal.modal({keyboard: false, show: false});
		this._initReport = true;
	},
	initUI: function(){
		$('#page-normal').delegate('.toggle', 'click', function(e){
			var me = $(this), body = me.closest('[id]').children('.body'), opts;
			opts = {duration: 300, progress: ui.onResize, complete: ui.onResize, easing: 'linear'};
			if(me.hasClass('collapse')) {
				me.removeClass('collapse').addClass('expand');
				body.stop().show(opts);
			} else {
				me.removeClass('expand').addClass('collapse');
				body.stop().hide(opts);
			}
		});
		this.onResize = function(){
			var page = $('#page-normal'), wrapper = page.children('[role=wrapper]'), h, em, rect;
			h = wrapper.height() + 40;
			em = page.parents();
			rect = app.window.size();
			if(h > 229) {
				page.height(h);
				em.height(h + 91 - 2);//上下边框占据了2个像素
				app.window.size({width: rect.width, height: h + 91});
			} else {
				page.height(229);
				em.height(318);
				app.window.size({width: rect.width, height: 320});
			}
		};
		this._initInfo = true;
	},
	setEnabled: function(){
		$('#offline-indicator').hide();
	},
	setDisabled: function(){
		$('#offline-indicator').show();
	},
	fixCSS: function(){
		var em = $(document.body).children('.emulator');
		if(!isOeBrowser) {
			em.css({
				'box-shadow': '0 0 80px #ADCFFF',
				position: 'absolute',
				left:'50%',
				top:'50%',
				'margin-left': -160,
				'margin-top': -160
			});
		}
		em.css('backgroundImage', 'url(' + prefix + "/images/edupoint/banner.bmp)");
		em.children('.win-control').children('button').css('background-image', 'url(' + prefix + "/images/win.png)");
		$('#loading-panel').css('background-image', 'url(' + prefix + "/images/big-loading.gif)");
	},
	autoHeight: function(){
		//$(document.body).children('.emulator').resize();
	},
	showDefault: function(){
		var page = $('#page-default'), h, indicator, indicator2;
		if(page.is(':visible')) { return; }
		page.siblings('section:visible').hide();
		page.show();
		h = 320//$(window).height();
		page.height(h);
		indicator = $('#indicator');
		indicator2 = $('#indicator-transparent');
		if(!ui.indicatorTimer) {
			ui.indicatorTimer = setInterval(function(){
				if(!page.is(':visible')) {
					clearInterval(ui.indicatorTimer);
					ui.indicatorTimer = null;
					return;
				}
				var text = indicator.text();
				if(text.length === 6) {
					indicator.text('.');
					indicator2.text('.....');
				} else {
					text += '.';
					indicator.text(text);
					indicator2.text(new Array(7-text.length).join('.'));
				}
			}, 400);
		}
	},
	showReport: function(){
		var page = $('#page-report');
		if(page.is(':visible')) { return; }
		page.siblings('section:visible').hide();
		page.show();
		page.height(229);
		app.window.tray_icon("set_tips", "请申报教学点客户端");
		this._initReport || this.initSettingUI();
	},
	showInfo: function(){
		var page = $('#page-normal'), tips = ['教学点类型：'], _ = {room: '教室终端', moon: '卫星接收终端'};
		//if(page.is(':visible')) { return; }
		page.siblings('section:visible').hide();
		page.show();
		page.height(229);
		this._initInfo || this.initUI();
		this.updateInfo();
		['base', 'room', 'moon'].forEach(function(v){
			var p = $('#' + v + '-card'), toggle;
			if(!p.is(':visible')) { return; }
			toggle = p.find('.toggle')
			if(toggle.hasClass('collapse')) {
				toggle.trigger('click');
			}
			(v in _) && tips.push('    ' + _[v]);
		});
		app.window.tray_icon("set_tips", tips.join('\n'));
		ui.setEnabled();
	},
	updateInfo: function(data){
		var format, filters;
		if(!data) {
			data = app.file.read(utils.appRoot + 'status.dat');
			if(!data) {
				data = {base:{},moon:{},room:{}};
			} else {
				data = JSON.parse(data.fromBase64());
			}
		}
		filters = {
			humanread: function(v){
				var d, h, m, str = '';
		        if(v === 0) { return '0分钟'; }
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
			classno: function(v){
				return "第 " + v + " 教室";
			},
			classtime: function(v){
				return "约合" + v + "个课时";
			},
			filter: function(name, value){
				if(name in this) {
					return this[name](value);
				} else {
					return value;
				}
			}
		};
		format = function(s){
			return s.replace(/\{([^}]+)\}/g, function(_, repl){
				var filter, value = data;
				repl = repl.split(':');
				filter = repl[1];
				repl = repl[0].split('.');
				while(repl.length) {
					value = value[repl.shift()];
				}
				return (filter ? filters.filter(filter, value) : value) || '';
			});
		};
		$.each(['base', 'room', 'moon'], function(_, v){
			var card = $('#' + v + '-card'), now;
			if(data[v].flag !== false) {
				card.show();
				now = new Date();
				card.find('[role]').each(function(){
					var me = $(this), role = me.attr('role'), s = format(role), el = me.children('.value');
					if(role.indexOf('last_connect_datetime') > -1) {
						d = new Date(s);
						if(now - d > 604800000) {
							el.css('color', '#F00');
						}
					}
					el.text(s);
				});
			} else {
				card.hide();
			}
		});
	},
	showLoading: function(){
		$('#loading-panel').show();
	},
	hideLoading: function(){
		$('#loading-panel').hide();
	},
	checkTerminalType: function(){
		var page = $('#page-report'), boxes, flag = false;
		boxes = page.find('input[type=checkbox]');
		boxes.each(function(){
			$('#key-' + this.value)[this.checked?'show':'hide']();
			if(this.checked) {
				flag = true;
			}
		});
		return flag;
	},
	checkKeyEmpty: function(){
		var ret;
		$.each(['class', 'recv'], function(_, key){
			var g = $('#key-' + key), ipt, v;
			if(g.is(':visible')) {
				ipt = g.find('input');
				v = ipt.val();
				if(!v) { ret = "required"; return false; }
				if(!/^[a-zA-Z0-9]{1,16}$/.test(ipt.val())) {
					ret = "invalid"
					return false;
				}
			}
		});
		return ret;
	}
};

utils = {
	appRoot: app.application.path(),
	/* 返回 false 表示本地存储的 cpu id 和当前机器的 cpu id 不一样 */
	checkCPUId: function(){
		var currentId = this.generateCpuId() || app.utils.get_hard_serial_id(),
			savedId = app.file.read_ini(utils.appRoot + 'settings.ini', 'data', 'terminalId');
		if(!savedId) {
			utils.saveCPUId();
		} else {
			if(currentId !== savedId) {
				console.log('[ERROR] cpu id was changed!!!');
				app.file.write_ini(utils.appRoot + 'settings.ini', 'data', 'reported', '');
				app.file.write_ini(utils.appRoot + 'settings.ini', 'data', 'terminalType', '');
			}
		}
		cpuId = savedId || currentId;
	},
	generateCpuId: function(){
		var id, ini = this.appRoot + 'dev.dat', chars;
		//if(!DEV) { return false; }
		return false;
		id = app.file.read(ini);
		if(id) { return id; }
		chars = '0123456789abcdef';
		id = [];
		while(id.length != 31) {
			id.push(chars.charAt(Math.floor(Math.random()*chars.length)));
		}
		id = id.join('');
		app.file.write(ini, id);
		return id;
	},
	saveCPUId: function(){
		var id = this.generateCpuId() || app.utils.get_hard_serial_id();
		app.file.write_ini(utils.appRoot + 'settings.ini', 'data', 'terminalId', id);
	},
	isReported: function(){
		var flag;
		flag = app.file.read_ini(utils.appRoot + 'settings.ini', 'data', 'reported');
		return flag === "true";
	},
	getTerminalType: function(){
		var str, parts, types = {};
		str = app.file.read_ini(utils.appRoot + 'settings.ini', 'data', 'terminalType');
		if(str.indexOf(',') !== -1) {
			parts = str.split(',');
		} else {
			parts = [str];
		}
		$.each(parts, function(_, p){
			types[$.trim(p.toLowerCase())] = '';
		});
		return {
			isClient: function(){
				return 'room' in types;
			},
			isReceiver: function(){
				return 'moon' in types;
			}
		};
	},
	trayBlink: function(stop){
		var interval = TRAY_ICON_BLINK, impl, icon = -1;

		impl = function(){
			var ico_name = icon > 0 ? "online" : "offline";
			if(icon > 0) {
				app.window.tray_icon("set_icon", 'Icon_att.ico');
			} else {
				app.window.tray_icon("set_icon", 'Icon_blk.ico');
			}
			icon = icon * -1;
		};
		if(stop === "stop") {
			this._blinkTimer && clearInterval(this._blinkTimer) && (delete this._blinkTimer);
			if(isOnline()) {
				app.window.tray_icon("set_icon", 'Icon_on.ico');
			} else {
				app.window.tray_icon("set_icon", 'Icon_off.ico');
			}
		} else {
			this._blinkTimer = setInterval(impl, interval);
		}
	},
	cachePath: function(paths){
		app.file.write(utils.appRoot + 'paths.dat', JSON.stringify(paths).toBase64());
	},
	nowstr: function(){
		var now = new Date(), s = [], tmp;
		s.push(now.getFullYear());
		tmp = now.getMonth() + 1;
		s.push(tmp < 10 ? '0'+tmp : tmp);
		$.each(['getDate', 'getHours', 'getMinutes', 'getSeconds'], function(_, m){
			var n = now[m]();
			s.push(n < 10 ? '0' + n : n);
		});
		return s.join('');
	},
	timeFromSnapshot: function(file){
		var dot = file.indexOf('.'), time = file.substring(0, dot);
		return time.substr(0, 4) + '-' + 
			   time.substr(4, 2) + '-' +
			   time.substr(6, 2) + ' ' +
			   time.substr(8, 2) + ':' +
			   time.substr(10, 2) + ':' +
			   time.substr(12, 2);
	},
	networkMonitor: function(){
		var cb = function(){
			var now = Date.now(), taskbar = app.screen.taskbar(), x, y, id, ww, wh;
			console.log("最开始检测到不在线时间：" + (new Date(lastOfflineTime).toISOString()));
			console.log("当前时间：" + (new Date(now).toISOString()));
			//忽略 5 秒的误差
			if(!isOnline() && Math.abs(now - lastOfflineTime - OFFLINE_NOTIFICATION_INTERVAL) < 5000) {
				ww = 250, wh = 60;
				if(taskbar.position == "bottom") {
					x = screen.width - ww;
					y = screen.height - wh - taskbar.height;
				} else if(taskbar.position == "right") {
					x = screen.width - ww - taskbar.height;
					y = screen.height - wh;
				} else {
					x = screen.width - ww;
					y = screen.height - wh;
				};
				console.log("客户端 5 分钟不在线，弹出离线提示窗口！");
				id = app.window.create(ww, wh, "client://edu_unit_terminal//notification.html", {x: x, y: y});
				console.log("窗口创建完毕，id：" + id);
				app.window.show(id);
				console.log("窗口已显示");
			} else {
				console.log("网络不稳定，时断时连。重新启动在线检测");
				utils.networkMonitor();
			}
		};
		console.log("开始检测在线状态");
		var t = setTimeout(cb, OFFLINE_NOTIFICATION_INTERVAL);
		console.log("检测任务计时器：" + t);
	},
	getVersion: function(){
		var ini = this.appRoot + "version.ini";
		return app.file.read_ini(ini, 'version', 'Version number') + '-' + app.file.read_ini(ini, 'version', 'svn');
	},
	saveUPYunConfig: function(config){
		var ini = this.appRoot + 'upyun.dat', old, ignore, str;
		if(!config) { return; }
		['group_id', 'desktop-preview-interval', 'cloud-service-username', 'cloud-service-password'].forEach(function(key){
			if(!(key in config) || config[key] === '') { ignore = true; return false; }
		});
		if(ignore) { return; }
		old = app.file.read(ini);
		str = JSON.stringify(config);
		if(old) {
			old = old.fromBase64();
			if(old == str) { return; }
		}
		app.file.write(ini, str.toBase64());
	},
	getUPYunConfig: function(){
		var ini = this.appRoot + 'upyun.dat', str, conf;
		str = app.file.read(ini);
		if(str) {
			str = str.fromBase64();
			conf = JSON.parse(str);
		} else {
			conf = false;
		}
		return conf;
	}
};

Task = (function(){
	var Task, tasks = {}, runing = false, first=true;
	Task = {
		start: function(){
			if(first) {
				setTimeout(function(){
					Task.start();
				}, 5000);
				first = false;
				return;
			}
			var type = utils.getTerminalType();
			$.each(tasks, function(name, o){
				if(o.disabled) { return; }
				if(type.isClient() && o.type.room) {
					Task.run(name);
				}
				if(type.isReceiver() && o.type.moon) {
					Task.run(name);
				}
			});
		},
		run: function(task_name){
			var options;
			if(task_name in tasks) {
				options = tasks[task_name];
				if(!options.runing) {
					try {
						options.init ? options.init(options) : options.fn(options);
					} catch(e) {
						DEBUG && console.log("运行任务", task_name, "报错：", e.message);
					}
				}
			}
		},
		isRunning: function(task_name){
			if(task_name in tasks) {
				return tasks[task_name].runing;
			} else {
				return runing;
			}
		},
		stop: function(task_name){
			if(task_name == "*") {
				task_name = Object.keys(tasks);
			} else {
				task_name = [task_name];
			}
			$.each(task_name, function(_, name){
				var options = tasks[name];
				if(!options) {
					DEBUG && console.log("无效的任务：", name);
					return;
				}
				if(options.runing) {
					window[options.clearMethod](options.timer);
					options.timer = null;
					options.runing = false;
					DEBUG && console.log("停止任务：", name);
				} else {
					DEBUG && console.log("任务 ", name, " 没有在运行");
				}
			});
		},
		devRun: function(task_name){},
		register: function(task_name, options){
			if(task_name in tasks) {
				throw new Error('task ' + task_name + ' already exists!');
			}
			if(!options.type) {
				options.type = {moon: true, room: true};
			}
			options.name = task_name;
			options.runing = false;
			tasks[task_name] = options;
		}
	};
	
	return Task;
})();
//【教室终端】终端程序将记录每天开机总时长
//【教室终端】终端程序将记录每天开机总时长中的使用时长与空闲时长
Task.register('machinetimeuse', {
	init: function(o){
		app.utils.collection_ldletimes("set_ldle_value",10);
		o.fn(o);
	},
	collectData: function(d){
		var a, b, obj = {};
		if(!d) { return; }
		try {
			a = JSON.parse(app.utils.collection_ldletimes("collect_times", d));
			a.forEach(function(rc){
				obj[rc.date] = {usetimes: parseInt(rc.runtimes) - parseInt(rc.ldletimes)};
			});
		} catch(e) {}
		try {
			b = JSON.parse(app.utils.collection_times(d));
			b.forEach(function(rc){
				if(!(rc.date in obj)) {
					obj[rc.date] = {};
				}
				obj[rc.date].count = rc.count;
				obj[rc.date].runtimes = rc.runtimes;
			});
		} catch(e) {}
		$.each(obj, function(date, cfg){
			if('usetimes' in cfg) { return; }
			cfg.usetimes = cfg.runtimes;
		});
		return obj;
	},
	waitNextStart: function(){
		var d = new Date();
		this.timer = setInterval(function(){
			var now = new Date(), h = now.getHours(), m = now.getMinutes();
			if((now.getDate() === d.getDate()) && h === 23 && m > 50) {
				clearInterval(timer);
				Task.run('machinetimeuse');
			}
		}, 10 * 60 * 1000);
	},
	fn: function(o){
		var me = this;
		sock.lastUploadTime('machine-time', function(e, data){
			var list, date, item;
			if(data && data.ret === 0) {
				list = me.collectData(data['last-date']);
				for(date in list) {
					item = list[date];
					item.date = date;
					item['hardware-id'] = cpuId;
					sock.sendMachineTimeMsg(item);
				}
			}
			o.runing = false;
			o.waitNextStart();
			DEBUG && console.log("使用率和开机时长任务停止，等待下次启动");
		});
		o.runing = true;
		DEBUG && console.log("使用率和开机时长任务启动");
	},
	type: {room: true},
	clearMethod: 'clearInterval'
});
//【教室终端】终端程序将记录每天开机时段的屏幕截图日志
//always
Task.register('snapshot', {
	init: function(o){
		var upy = utils.getUPYunConfig(), interval;
		if(upy) {
			interval = parseInt(upy['desktop-preview-interval']);
		}
		if(!interval) {
			interval = 10;
		}
		DEBUG && console.log("截图间隔时间：", interval, "分钟");
		SNAPSHOT_INTERVAL = interval * 60 * 1000;
		this.fn(o);
	},
	fn:function(o){
		var impl = function(){
			var filename = utils.nowstr() + '.jpg';
			app.utils.upyun_snapshot("snapshot_local", filename);
			DEBUG && console.log('截图成功：', filename);
		};
		o.timer = setInterval(impl, SNAPSHOT_INTERVAL);
		o.runing = true;
		DEBUG && console.log('截图任务启动 ...');
	},
	type: {room: true, moon: false},
	clearMethod: 'clearInterval'
});
//online -> restart
Task.register('uploadimg', {
	getCachedImages: function(){
		var raw = app.utils.upyun_snapshot("img_cache_list"), imgs;
		return raw[0] === 0 ? [] : JSON.parse(raw[1]);
	},
	waitNextStart: function(){
		if(isOnline()) {
			delete window.START_UPLOAD_WHEN_ONLINE;
			this.timer = setTimeout(function(){
				Task.run('uploadimg');
			}, UPLOAD_IMG_INTERVAL);
		} else {
			console.log("当前离线，在线后开始上传图片");
			window.START_UPLOAD_WHEN_ONLINE = true;
		}
		
	},
	fn: function(o){
		var upy = utils.getUPYunConfig(), imgs = o.getCachedImages(), impl;
		impl = function(){
			var raw, img;
			if(!isOnline()) {
				o.runing = false;
				o.timer = null;
				o.waitNextStart();
				return;
			}
			if(imgs.length) {
				img = imgs.shift();
				if(!/^\d{14}\.jpg$/i.test(img)) {
					DEBUG && console.log("无效的图片名：", img, "，忽略！");
					o.timer = setTimeout(impl, 100);
					return;
				}
				raw = app.utils.upyun_snapshot("upyun_uploadimg", upy['cloud-service-username'], upy['cloud-service-password'], upy['group_id'], img);
				if(raw[0] === 0) {
					DEBUG && console.log('上传截图记录到服务器', img);
					sock.sendSnapshotMsg({
						'create_time': utils.timeFromSnapshot(img),
						'hardware-id': cpuId,
						url: raw[1],
						host: ''
					}, function(e, data){
						if(data && data.ret === 0) {
							DEBUG && console.log('上传图片：', img, '成功');
						} else {
							DEBUG && console.log('上传图片：', img, '失败', e && e.message || data && data.msg);
						}
						o.timer = setTimeout(impl, 100);
					});
				} else {
					DEBUG && console.log('上传图片：', img, '底层失败！！！');
				}
			} else {
				o.runing = false;
				o.waitNextStart();
			}
		};
		if(upy === false) {
			DEBUG && console.log("县级服务器没有配置又拍云账户，取消上传图片");
			return;
		}
		o.timer = setTimeout(impl, 100);
		o.runing = true;
		DEBUG && console.log('上传图片任务启动 ...');
	},
	type: {room: true},
	clearMethod: 'clearTimeout'
});
//once【卫星接收终端】终端程序将记录每日新增数据
Task.register('scanfile', {
	init: function(){
		var me = this, oldpaths = app.file.read(utils.appRoot + 'paths.dat');
		if(oldpaths) {
			oldpaths = JSON.parse(oldpaths.fromBase64());
			me.usePaths(oldpaths);
		}
		sock.getDirectoryInfo(function(e, data){
			if(data && data.ret === 0) {
				me.usePaths(data.path);
				utils.cachePath(data.path);
			}
		});
		me.fn(me);
	},
	usePaths: function(paths){
		var me = this;
		me._paths && $.each(me._paths, function(_, p){
			DEBUG && console.log("取消监控目录", p);
			app.utils.watch_dirs(p, 1);
		});
		$.each(paths, function(_, p){
			DEBUG && console.log("开始监控目录", p);
			app.utils.watch_dirs(p, 0);
		});
		me._paths = paths;
	},
	collectData: function(date){
		var xml = app.file.read(utils.appRoot + "resource_xml\\" + date + ".xml"),
			parser, doc, obj, el, ext;
		if(!xml) { return null; }
		parser = new DOMParser();
		obj = {xml_data: [], date: date, 'hardware-id': cpuId};
		doc = parser.parseFromString(xml, 'text/xml');
		el = doc.querySelector('statistics');
		obj.total_type = el.getAttribute('typenumber');
		obj.total_count = el.getAttribute('filenumber');
		obj.total_size = el.getAttribute('totalsize');
		el = el.firstElementChild;
		while(el) {
			ext = el.tagName.toLowerCase();
			obj.xml_data.push({type: ext, size: el.getAttribute('totalsize'), count: el.getAttribute('filenumber')});
			el = el.nextElementSibling;
		}
		return obj;
	},
	datestr: function(d){
		var y = d.getFullYear(),
			m = (d.getMonth() + 1),
			day = d.getDate();
		if(m < 10) { m = '0' + m; }
		if(day < 10) { day = '0' + day; }
		return y + '-' + m + '-' + day;
	},
	fromDate: function(date, callback){
		var from = new Date(date), today = new Date(), record;
		while(from < today) {
			record = this.collectData(this.datestr(from));
			if(record) {
				callback(record);
			}
			from.setDate(from.getDate() + 1);
		}
	},
	fn: function(o){
		var impl = function(){
			sock.lastUploadTime('moon-receive', function(e, data){
				if(data && data.ret === 0) {
					o.fromDate(data['last-date'], function(record){
						sock.sendFileChangedMsg(record);
					});
				}
				o.runing = false;
			});
		};
		impl();
		DEBUG && console.log("监控任务启动");
	},
	type: {moon: true}
});
//start websocket
if(isOeBrowser) {
	remoteHost = app.file.read_ini(utils.appRoot + 'settings.ini', 'server', 'ip') + ':' + app.file.read_ini(utils.appRoot + 'settings.ini', 'server', 'port');
}
//先本地后远程
utils.checkCPUId();
sock = new BBTWebSocket("ws://" + remoteHost + "/ws/edu-unit");
sock.ready(function(){
	this.login(function(e, data){
		if(data && data.ret === 0) {
			if(data.reported === false) {
				ui.showReport();
				app.file.write_ini(utils.appRoot + 'settings.ini', 'data', 'reported', '');
				Task.isRunning() && Task.stop();
			} else {
				Task.isRunning() || Task.start();
				utils._blinkTimer && utils.trayBlink('stop');
				if(!utils.isReported()) {
					app.file.write_ini(utils.appRoot + 'settings.ini', 'data', 'reported', 'true');
					app.file.write_ini(utils.appRoot + 'settings.ini', 'data', 'terminalType', data.type.join(','));
					ui.showInfo();
				}
				sock.getStatus();
			}
			utils.saveUPYunConfig(data.upyun_config);
			app.file.write_ini(appRoot + 'settings.ini', 'data', 'lastConnectTime', Date.now()+'');
		}
	});
});
$(function(){
	ui.fixCSS();
	ui.setDisabled();
	$(document.body).bind('contextmenu', function(e){
		return false;
	});
	$(document.body).mousedown(function(e){
		var el = e.target, flag = el.className == "emulator" && e.pageY <= 91;
		flag = flag || el.id == "offline-indicator" || el.id == "loading-panel";
		if(flag) {
			app.window.move();
		}
	});
	$('#win-controller').delegate('button', 'click', function(e){
		var me = $(this);
		e.stopPropagation();
		if(me.hasClass('win-min')) { app.window.min();sock.getStatus(); }
		else if(me.hasClass('win-close')) { app.window.hide(); }
	});
	
	if(utils.isReported()) {
		ui.showInfo();
		Task.start();
	} else {
		ui.showReport();
		Task.isRunning() && Task.stop();
	}
});