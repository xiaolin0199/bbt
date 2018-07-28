/**
 * 班班通教学点终端底层 api 兼容层，方便在浏览器内调试程序逻辑。
 * 教学点终端会在本地存储 3 个字段：
 *
 * `terminalId`     CPUId 的标志
 * `terminaType`    终端类型的标志，可以是 client 或者
 *                  receiver，也可以两者都是（以逗号分隔）
 * `reported`       是否申报的标志，true/false
 *
 * 以上字段可以在下面的 defaults 里面配置，如果教学点终端在
 * 浏览器里面运行，会自动加载这个文件。注意：和业务相关的底层
 * 逻辑都将无效。
 * 也可以不配置下面的 defaults，直接使用 url 参数，像这样：
 *     url?terminalId=fdasjklf3d3adll&terminalType
 */
var app = (function(){
var noop = function(){},
	query,
	defaults = {
		terminalId: "",
		terminalType: "client",
		reported: "true"
	};
	
query = function(k){
	var obj = [], str = location.search.substring(1);
	str.split('&').forEach(function(p){
		var ps = p.split('=');
		obj[ps[0]] = decodeURIComponent(ps[1]);
	});
	return obj[k] || '';
};
return {
    application: {
        path: noop,
        exit: noop,
        set_local_time: noop,
        get_usbkey_uuid: noop,
        show_trayicon_relat_wnd: noop,
        cur_browserid: noop
    },
    event: {
        callback: {
            add: noop,
            remove: noop
        }
    },
    screen: {
        size: noop,
        taskbar: noop
    },
    window: {
        browser_id: noop,
        load: noop,
        create: noop,
        move: noop,
        rect: noop,
        size: function(o){
            var em = $(document.body).children('.emulator');
            if(o) {
                em.width(o.width);
                em.height(o.height);
            } else {
                return {width: em.width(), height: em.height()};
            }
        },
        position: noop,
        close: noop,
        max: noop,
        min: noop,
        show: noop,
        hide: noop,
        transparent: noop,
        tray_icon: noop,
        messagebox: noop,
        set_to_toolwindow: noop,
        exist: noop,
        get_parent_window_id: noop,
        set_window_top: noop,
        register_shutdown_callback: noop
    },
    network: {
        download: noop,
        register_oper_callback: noop,
        unregister_oper_callback: noop
    },
    path: {
        join: noop
    },
    file: {
        read: noop,
        write: noop,
        read_ini: function(_, section, field){
        	if(section != "data") { return ""; }
        	return query(field) || defaults[field] || "";
        },
        write_ini: noop
    },
    utils: {
        execute_js: noop,
        local_macs: noop,
        snapshot_screen: noop,
        snapshot_screen_for_computer_class: noop,
        get_file_md5: noop,
        http_post_file: noop,
        zeromq_connect: noop,
        zeromq_sub: noop,
        winapi_tool: noop,
        collection_times: noop,
        collection_ldletimes: noop,
        watch_dirs: noop,
        upyun_snapshot: noop,
        get_hard_serial_id: function(){
        	return "bda027fcda0e3c9085534cd85ecd828";
        }
    }
}
})();