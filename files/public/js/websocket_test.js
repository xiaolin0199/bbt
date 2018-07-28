var localMac = '08-00-27-57-B7-9A',
	programVersion = "V4.0.0",
	socketHost = location.href.indexOf('file://') === 0 ? '172.16.6.20:8001' : location.host,
	ui;
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
				}, 100);
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
				me._queue.push(data);
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
			category = "classroom";
		}
		this.emit({category: category, operation: operation, data: data}, function(e, data){
			if(e) {
				callback(e);
			} else {
				if(data.ret === 0) {
					callback(null, data);
				} else {
					callback(data.msg || ERRORMSG[data.ret] || "unknow error");
				}
			}
		});
	},
	_login: function(callback){
		this.request('login', {mac: localMac, version: programVersion}, callback);
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
	/* bbt used methods */
	adminLogin: function(username, password, callback){
		this.request('report-login', {username: username, password: password}, callback);
	},
	reportClass: function(grade_uuid, class_uuid, callback){
		this.request('report', {grade_uuid: grade_uuid, class_uuid: class_uuid}, callback);
	},
	getLessonStatus: function(callback){
		this.request('lesson-status', {}, callback);
	},
	startLesson: function(data, callback){
		this.request('lesson-start', data, callback);
	},
	updateStatus: function(s){
		document.getElementById('status').innerHTML = s;
	},
	pingLoop: function(){
		var me = this, start = new Date();
		me.request('ping', (new Date()).toISOString(), 'sync', function(e, data){
			if(e) { console.log(e); me.destroy(); return; }
			var clients = data.clients.records, end = new Date();
			ui.updateClient(clients);
			ui.updateFlot(data.clients.total);
			ui.updateNetwork(start, end);
			setTimeout(function(){ me.pingLoop(); }, 100);
		});
	},
	water: function(){
		var me = this;
		//处理被动响应服务器消息
		me['undefined'] = me['null'] = function(data){ console.log('recv server message:', data); };
		//客户端循环
		me._login(function(e, data){
			if(e) {
				me.updateStatus(e.message || e);
			} else {
				if(data.reported === true) {
					me.checkLesson();
				} else {
					ui.showReport();
					me.adminLogin('admin', 'admin', function(){
						console.log(arguments)
					});
				}
			}
		});
	},
	checkLesson: function(){
		var me = this;
		me.getLessonStatus(function(e, data){
			var str, info;
			if(e) {
				me.updateStatus(e.message || e);
			} else {
				info = data.data.current_lesson || data.data.next_lesson;
				if(info) {
					str = Ext.String.format('<span>科目:{0}</span><span>年级:{1}年级({2})班</span><span>开始时间:{3}</span><span>结束时间:{4}</span>',
						info.lesson_name,
						info.grade_number,
						info.class_number,
						info.start_datetime,
						info.end_datetime
					);
					me.updateStatus(str);
				}
			}
		});
	}
};

ui = {
	updateClient: function(clients){
		var map = {}, container, tbody, trs = {};
		$.each(clients, function(_, c){
			if(c.ip in map) {
				map[c.ip].children.push(c);
			} else {
				map[c.ip] = {children: [c]};
			}
		});
		tbody = $('#client-list').find('tbody');
		tbody.children('tr').each(function(){
			trs[this.getAttribute('data-id')] = this;
		});
		$.each(map, function(ip, item){
			var htmls = [], groupEl, groupBody;
			groupEl = ui.client.getByIp(ip);
			if(!groupEl) {
				groupEl = ui.client.createByIp(ip);
			}
			groupBody = groupEl.find('tbody');
			$.each(item.children, function(_, item){
				if(item.hash in trs) {
					$(trs[item.hash]).removeClass('long-no-response').children('td:last').text(item.last_active_datetime);
					delete trs[item.hash];
				} else {
					htmls.push('<tr data-id="' + item.hash + '"><td>' + item.hash + '</td><td>' + item.peer + '</td><td>' + item.last_active_datetime + '</td></tr>');
				}
			});
			htmls.length && groupBody.append(htmls.join(''));
			$.each(trs, function(_, tr){
				$(tr).addClass('long-no-response');
			});
			groupEl.find('.accordion-toggle').text(groupEl.attr('data-ip') + '(' + groupBody.children('tr').length + ')');
		});
	},
	updateNetwork: function(start, end){
		var body = $('#network-list').find('tbody'), v = end - start;
		if(body.children('tr').length >= 30) {
			body.children('tr:first').remove();
		}
		body.append('<tr><td>' + start.toISOString() + '</td><td>' + end.toISOString() + '</td><td>' + v + '</td></tr>');
		if(v > 5000) {
			body.children('tr:last').addClass('long-time');
		}
	},
	client: {
		hasIp: function(ip){
			var el = $('#client-list'), headers, found = false;;
			headers = el.children('.accordion-group').children('.accordion-heading');
			headers.each(function(){
				var text = this.innerText || this.textContent;
				if(text.indexOf(ip) !== -1) {
					found = true;
					return false;
				}
			});
			return found;
		},
		getByIp: function(ip){
			var el = $('#client-list'), headers, found = false, item;
			headers = el.children('.accordion-group').children('.accordion-heading');
			headers.each(function(){
				var text = this.innerText || this.textContent;
				if(text.indexOf(ip) !== -1) {
					found = true;
					item = this;
					return false;
				}
			});
			return found ? $(item).closest('.accordion-group') : null;
		},
		createByIp: function(ip) {
			var htmls = [], el, _ip = ip.replace(/\./g, '-');
			if(this.hasIp(ip)) {
				return this.getByIp(ip);
			}
			htmls.push('<div class="accordion-group" data-ip="' + ip + '">');
			htmls.push('<div class="accordion-heading">');
			htmls.push('<a class="accordion-toggle" data-toggle="collapse" data-parent="#client-list" data-href="#collapse-body-' + _ip + '">');
			htmls.push(ip + '( 0 )');
			htmls.push('</a></div>');
			htmls.push('<div id="collapse-body-' + _ip + '" class="accordion-body collapse in"><div class="accordion-inner">');
			htmls.push('<table class="table table-striped table-bordered"><thead><tr><th>hash</th><th>peer</th><th>last_active_time</th></tr></thead><tbody></body></table>');
			htmls.push('</div></div></div>');
			el = $(htmls.join(''));
			el.appendTo($('#client-list'));
			return el;
		}
	},
	_data: null,
	updateFlot: function(d){
		var data = this._data;
		data.push(d);
		data.shift();
		this._flot.setData([{data: data.map(function(v, i){ return [i, v]; })}]);
		this._flot.draw();
		$('#counter').text(d);
	},
	initFlot: function(){
		var container = $('#data-chart'), plot;
		this._data = (function(){
			var len = 30, a = new Array(len), i;
			for(i=0;i<len;i++){
				a[i] = 0;
			}
			return a
		})();
		plot = $.plot(container, [{data: this._data.map(function(v,i){return [i,v]})}], {
			series: {lines: {fill: true}},
			grid: {
				borderWidth: 1,
				minBorderMargin: 20,
				labelMargin: 10,
				backgroundColor: {
					colors: ["#fff", "#e4f4f4"]
				},
				margin: {
					top: 8,
					bottom: 20,
					left: 20
				},
				markings: function(axes) {
					var markings = [];
					var xaxis = axes.xaxis;
					for (var x = Math.floor(xaxis.min); x < xaxis.max; x += xaxis.tickSize * 2) {
						markings.push({ xaxis: { from: x, to: x + xaxis.tickSize }, color: "rgba(232, 232, 255, 0.2)" });
					}
					return markings;
				}
			},
			xaxis: {
				tickFormatter: function() {
					return "";
				}
			},
			yaxis: {
				min: 0,
				max: 200
			},
			legend: {
				show: true
			}
		});
		this._flot = plot;
	}
};

$(function(){
	$('#side-tabs').tab();
	$(".client-list").collapse();
	$('#client-list').delegate('.accordion-toggle', 'click', function(e){
		var p = $($(this).attr('data-href'));
		p.toggle()
		e.preventDefault();
		return false;
	});
	if(window.app && app.window) {
		$(document.body).mousedown(function(e) {
			var name = e.target.tagName.toLowerCase();
			if(/^a|input|select|textarea|button|img|h[1-6]$/.test(name)) {
				return;
			}
			if(e.target.getAttribute('drag') == "no") { return; }
			try { app.window.move(); return false; } catch(e) {}
		});
		$('#controller').show().delegate('button', 'click', function(e){
			var name = e.target.className;
			if(name == 'win-min') {
				app.window.min();
			} else if(name == "win-close") {
				app.window.hide();
			}
		});
		$('#data-chart').css('top', 25);
		$('#client-list').closest('.sidebar').css('top', 325);
		$('#counter').closest('div').css({top: '0px', left: 10, color: '#FFF', zIndex: 10000});
	}
	ui.initFlot();
	var sock = new BBTWebSocket("ws://" + socketHost + "/ws/example");
	setTimeout(function(){ sock.pingLoop(); }, 800);
});
try {
	app.window.transparent(0);
} catch(e) {}