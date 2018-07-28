#! /bin/bash
TOP_DIR="${TOP_DIR:=$(cd $(dirname -- $0) && pwd)}"
[ -e $TOP_DIR/setuprc ] && echo "using source: $TOP_DIR/setuprc" && source $TOP_DIR/setuprc
export PS4='+{$LINENO:${FUNCNAME[0]}} '
declare os_VENDOR os_RELEASE os_PACKAGE os_CODENAME

[ -z "$DEBUG" ] && DEBUG="0"
[ -z "$USERNAME" ] && USERNAME="oseasy"
[ -z "$APPNAME" ] && APPNAME="bbt"
[ -z "$RELEASE" ] && RELEASE="bbt-enshi"
[ -z "$WSGI" ] && WSGI="wsgi"
[ -z "$VENV" ] && VENV="bbt"
[ -z "$DB_HOST" ] && DB_HOST="127.0.0.1"
[ -z "$DB_PORT" ] && DB_PORT="3306"
[ -z "$DB_NAME" ] && DB_NAME="$APPNAME"
[ -z "$DB_USER" ] && DB_USER="root"
[ -z "$DB_PASS" ] && DB_PASS="oseasy"
[ -z "$DST_DIR" ] && DST_DIR="/opt"
[ -z "$NGINX_PORT" ] && NGINX_PORT="8000 11111"
[ -z "$UWSGI_PORT" ] && UWSGI_PORT="8080"
[ -z "$STATS_PORT" ] && STATS_PORT="9090"
[ -z "$WEBSOCKET_PORT" ] && WEBSOCKET_PORT="8001"

UWSGI_CONF_DIR=${UWSGI_CONF_DIR:=/etc/uwsgi/conf.d}
NGINX_CONF_DIR=${NGINX_CONF_DIR:=/etc/nginx/conf.d}
SUPERVISOR_CONF_DIR=${SUPERVISOR_CONF_DIR:=/etc/supervisor/conf.d}
VIRTUALENV_HOME=${VIRTUALENV_HOME:=/usr/lib/venvs}
PIP_MIRROR=${PIP_MIRROR:=http://mirrors.aliyun.com/pypi/simple/}
TRUSTED_HOST=$(egrep -o '[^/]*\..*\.[^/]*' <<< $PIP_MIRROR)
API_MIRROR=${API_MIRROR:=http://mirrors.aliyun.com/ubuntu/}

function _ensure_lsb_release {
    if [[ -x $(command -v lsb_release 2>/dev/null) ]]; then
        return
    fi

    if [[ -x $(command -v apt-get 2>/dev/null) ]]; then
        sys_install -y lsb-release

    elif [[ -x $(command -v yum 2>/dev/null) ]]; then
        # all rh patforms (fedora, centos, rhel) have this pkg
        sudo yum install -y redhat-lsb-core
    else
        echo "Unable to find or auto-install lsb_release"
        exit 1
    fi
}

function GetOSVersion {
    _ensure_lsb_release

    os_RELEASE=$(lsb_release -r -s)
    os_CODENAME=$(lsb_release -c -s)
    os_VENDOR=$(lsb_release -i -s)

    if [[ $os_VENDOR =~ (Debian|Ubuntu|LinuxMint) ]]; then
        os_PACKAGE="deb"
    else
        os_PACKAGE="rpm"
    fi

    typeset -xr os_VENDOR
    typeset -xr os_RELEASE
    typeset -xr os_PACKAGE
    typeset -xr os_CODENAME
}

function is_fedora {
    if [[ -z "$os_VENDOR" ]]; then
        GetOSVersion
    fi

    [ "$os_VENDOR" = "Fedora" ] || \
    [ "$os_VENDOR" = "Red Hat" ] || \
    [ "$os_VENDOR" = "RedHatEnterpriseServer" ] || \
    [ "$os_VENDOR" = "CentOS" ] || \
    [ "$os_VENDOR" = "OracleLinux" ] || \
    [ "$os_VENDOR" = "Virtuozzo" ] || \
    [ "$os_VENDOR" = "kvmibm" ]
}

function is_ubuntu {
    if [[ -z "$os_PACKAGE" ]]; then
        GetOSVersion
    fi
    [ "$os_PACKAGE" = "deb" ]
}

function is_installed {
    if [[ -z "$@" ]]; then
        return 1
    fi

    if [[ -z "$os_PACKAGE" ]]; then
        GetOSVersion
    fi

    if [[ "$os_PACKAGE" = "deb" ]]; then
        dpkg -s "$@" > /dev/null 2> /dev/null
    elif [[ "$os_PACKAGE" = "rpm" ]]; then
        rpm --quiet -q "$@"
    else
        echo "finding if a package is installed"
        exit 1
    fi
}

function sys_install {
    if is_ubuntu; then
        echo -e "\033[32m sys install $@ \033[0m"
        sudo apt-get install "$@"
    elif is_fedora; then
        echo -e "\033[32m sys install $@ \033[0m"
        sudo yum install "$@"
    else
        echo "distro not supported installing packages"
        exit 1
    fi
}

function pip_install {
    echo -e "\033[32m pip install $@ \033[0m"
    sudo pip install "$@"
}

function get_inet_addr {
    if [ -z "$1" ]; then
        error "nic required."
        exit 1
    elif [ $(ls /sys/class/net | grep -E "^$1$" | wc -l) != 1 ]; then
        error "Invalid nic name $1, which does not exit."
        exit 1
    fi
    if [ "$LANG" == 'zh_CN.UTF-8' ]; then
        echo "$(ifconfig $1 | grep "inet 地址:" | awk  '{print $2}' | cut -c 8-)"
    else
        echo "$(ifconfig $1 | grep "inet addr:" | awk '{print $2}' | cut -c 6-)"
    fi
}

function require_or_die {
    for i in $args;
    do
        test -z "${!i}" && error "setting:[${i}] required."
    done
}

function check_service_running {
    local service="$@"
    for i in $service;
    do
        test $(service $i status | grep 'active (running)' | wc -l) -eq 0 && echo "waiting $i service..." && sleep 5 ||
        test $(service $i status | grep 'active (running)' | wc -l) -eq 0 && echo "$i service is not running(or installed)." && exit 1
    done
    return 0
}

function check_sudo {
    if [ "$(sudo -l > /dev/null && echo 'True' || echo 'False')" = "False" ]; then
        error "当前用户$USER没有sudo权限或用户密码错误."
        exit 1
    fi
}

function check_root {
    if [ "$NO_CHECK_ROOT" = "1" ]; then
        return 0
    elif test $EUID -eq 0; then
        error "
            请用具备sudo权限的非root账户运行此脚本.
            或者添加 NO_CHECK_ROOT=1
        "
        exit 1
    fi
}

function check_venv {
    if [ "$NO_CHECK_VENV" = "1" ]; then
        return 0
    elif test -n "$VIRTUAL_ENV"; then
        error "请先退出python virtualenv环境."
        exit 1
    fi
}

function debug {
    echo -e "\033[32m $@ \033[0m"
}

function warning {
    echo -e "\033[33m $@ \033[0m"
}

function error {
    echo -e "\033[31m $@ \033[0m" && exit 1
}

function mk_backup {
    if [ -n "$1" ]; then
        if [ ! -e "$1" ]; then
            error "file ${1} does not exist."
            exit 1
        elif [ ! -e "${1}.bak" ]; then
            sudo cp -p $1 ${1}.bak
            sudo bash -c "cat ${1}.bak|grep -v ^#|grep -v ^$ > ${1}"
        else
            warning "backup ${1}.bak already exist."
        fi
    else
        error "path required."
        exit 1
    fi
}

function readtp {
    local value
    local delay
    local text="$1"
    local default="$2"
    local delay="$3"
    local regex="$4"
    test -z "$text" && text="Input"

    [ -n "$default" ] && text="${text}[$default]"
    [ $delay -gt 0 ] 2>/dev/null || delay=10

    read -t $delay -p "${text}:" value
    if [[ -n "$regex" && -n "$value" ]]; then
        while [ -z "$(egrep -o "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" <<< "$value")" ]; do
            warning "Bad input, retry."
            read -t $delay -p "${text}:" value
        done
    elif [ -z "$value" ]; then
        value="$default"
        if [[ -n "$regex" && -n "$value" && -z "$(egrep -o "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" <<< "$value")" ]]; then
            error "Bad default value."
            exit 1
        fi
    fi
    echo "$value"
}

# 配置阿里源
function setup_aliyun {
    if [[ -z "$os_PACKAGE" ]]; then
        GetOSVersion
    fi
    if is_ubuntu; then
        if ! grep -q "$(egrep -o '[^/]*\..*\.[^/]*' <<< $API_MIRROR)" /etc/apt/sources.list; then
            mk_backup /etc/apt/sources.list
            sudo bash -c "echo '# Ubuntu $os_CODENAME Mirror from %API_MIRROR' > /etc/apt/sources.list";
            for i in $os_CODENAME  $os_CODENAME-security $os_CODENAME-updates $os_CODENAME-proposed $os_CODENAME-backports;
            do
                for j in deb deb-src;
                do
                    sudo bash -c "echo '$j $API_MIRROR $i main restricted universe multiverse' >> /etc/apt/sources.list";
                done
            done

            sudo apt-get update -y
            sudo apt-get upgrade -y
        fi
    elif is_fedora; then
        if [[ ${os_RELEASE%%.*} -ge 5 && ${os_RELEASE%%.*} -le 7 ]]; then
            sudo wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-${os_RELEASE%%.*}.repo
            sys_install epel-release -y
            sudo yum makecache
        fi
    fi
}

# 安装pip
function install_pip {
    local index_url="${PIP_MIRROR:-http://mirrors.aliyun.com/pypi/simple/}"
    local trusted_host="$(egrep -o '[^/]*\..*\.[^/]*' <<< $index_url)"
    sys_install python-pip -y
    mkdir -p ~/.pip && touch ~/.pip/pip.conf
    sudo mkdir -p /root/.pip && sudo touch /root/.pip/pip.conf
    sudo crudini --set ~/.pip/pip.conf global index-url $index_url
    sudo crudini --set ~/.pip/pip.conf install trusted-host $trusted_host
    sudo crudini --set /root/.pip/pip.conf global index-url $index_url
    sudo crudini --set /root/.pip/pip.conf install trusted-host $trusted_host
    pip_install pip --upgrade
}

# 安装一些基础库
function install_libs {
    if is_ubuntu; then
        # is_installed build-essential || sys_install build-essential -y
        is_installed python-dev || sys_install python-dev -y
        is_installed libmysqld-dev || sys_install libmysqld-dev -y
    elif is_fedora; then
        is_installed epel-release || sys_install epel-release -y
        is_installed python-devel || sys_install python-devel -y
        is_installed mysql-devel || sys_install mysql-devel -y
    fi
    is_installed crudini || sys_install crudini -y
    is_installed chrony || sys_install chrony -y
    return 0
}

# 安装Mariadb-Server
function install_mariadb_server {
    DB_PASS="${DB_PASS:=`readtp 数据库密码 mysql`}"
    require_or_die DB_PASS

    local success=0
    if ! is_installed mariadb-server; then
        sys_install mariadb-server -y
        if is_ubuntu; then
            check_service_running mysql
        elif is_fedora; then
            sudo systemctl enable mariadb.service
            sudo systemctl start mariadb.service
            check_service_running mariadb
        fi
    fi
    if sudo mysql -uroot -e 'show databases' 2>/dev/null | grep -q 'information_schema'; then
        success=1
    elif sudo mysql -uroot -p$DB_PASS -e 'show databases' 2>/dev/null | grep -q 'information_schema'; then
        success=2
    else
        error "mariadb-server varify failed."
        exit 1
    fi

    if test $success -eq 1; then
        sudo mysql -uroot -e "update mysql.user set plugin='mysql_native_password';flush privileges;"
        sudo mysqladmin -uroot password "$DB_PASS"
    fi

    sudo mysql -uroot -p$DB_PASS -e"
        use mysql;
        grant all privileges on *.* to 'root'@'localhost' identified by '$DB_PASS';
        grant all privileges on *.* to 'root'@'%' identified by '$DB_PASS';
        update user set grant_priv = 'Y' where user = 'root';
        flush privileges;
    "
}

# 安装Memcached
function install_memcached {
    is_installed memcached || sys_install memcached -y
    check_service_running memcached
}

# 安装Redis-Server
function install_redis_server {
    is_installed redis-server || sys_install redis-server -y
    check_service_running redis-server
}

# 安装supervisor
function install_supervisor {
    pip_install supervisor
    local conf_file=/etc/supervisor/supervisord.conf
    local service_file=/lib/systemd/system/supervisor.service
    sudo mkdir -p $SUPERVISOR_CONF_DIR
    sudo touch $conf_file $service_file
    sudo bash -c "mkdir -p /etc/supervisor && echo_supervisord_conf > /etc/supervisor/supervisord.conf"

    sudo crudini --set $conf_file unix_http_server file /var/run/supervisor.sock
    sudo crudini --set $conf_file supervisord logfile /var/log/supervisor/supervisord.log
    sudo crudini --set $conf_file supervisord pidfile /var/run/supervisord.pid
    sudo crudini --set $conf_file supervisord childlogdir /var/log/supervisor
    sudo crudini --set $conf_file supervisord user root
    sudo crudini --set $conf_file supervisorctl serverurl unix:///var/run/supervisor.sock
    sudo crudini --set $conf_file include files $SUPERVISOR_CONF_DIR/\*.ini

    if is_ubuntu; then
        # [Unit]
        # Description=Supervisor process control system for UNIX
        # Documentation=http://supervisord.org
        # After=network.target

        # [Service]
        # ExecStartPre=/bin/mkdir -p /var/log/supervisor
        # ExecStartPre=/bin/chown root:adm /var/log/supervisor
        # ExecStart=$(which supervisord) -n -c /etc/supervisor/supervisord.conf
        # ExecStop=$(which supervisorctl) \\\$OPTIONS shutdown
        # ExecReload=$(which supervisorctl) -c /etc/supervisor/supervisord.conf \\\$OPTIONS reload
        # KillMode=process
        # Restart=on-failure
        # RestartSec=50s

        # [Install]
        # WantedBy=multi-user.target

        sudo crudini --set $service_file Unit Description 'Supervisor process control system for UNIX'
        sudo crudini --set $service_file Unit Documentation 'http://supervisord.org'
        sudo crudini --set $service_file Unit After 'network.target'

        sudo crudini --set $service_file Service ExecStartPre '/bin/mkdir -p /var/log/supervisor'
        sudo crudini --set $service_file Service ExecStartPreChown '/bin/chown root:adm /var/log/supervisor'
        sudo crudini --set $service_file Service ExecStart "$(which supervisord) -n -c /etc/supervisor/supervisord.conf"
        sudo crudini --set $service_file Service ExecStop "$(which supervisorctl) \$OPTIONS shutdown"
        sudo crudini --set $service_file Service ExecReload "$(which supervisorctl) -c /etc/supervisor/supervisord.conf \$OPTIONS reload"
        sudo crudini --set $service_file Service KillMode 'process'
        sudo crudini --set $service_file Service Restart 'on-failure'
        sudo crudini --set $service_file Service RestartSec '50s'

        sudo crudini --set $service_file Install WantedBy 'multi-user.target'
        sudo sed -i "s:ExecStartPreChown:ExecStartPre:g" $service_file

    elif is_fedora; then
        sudo wget -O $service_file https://raw.githubusercontent.com/Supervisor/initscripts/master/centos-systemd-etcs
    fi

    # sudo systemctl unmask supervisor.service
    sudo chmod +x $service_file
    sudo systemctl enable supervisor.service
    sudo systemctl daemon-reload
    sudo systemctl start supervisor.service
}

function install_uwsgi {
    pip_install uwsgi
    sudo mkdir -p $UWSGI_CONF_DIR
}

function install_nginx {
    if is_ubuntu; then
        is_installed nginx-full || sys_install nginx-full -y
    elif is_fedora; then
        is_installed nginx-full || sys_install nginx -y
    else
        exit 1
    fi
    sudo mkdir -p $NGINX_CONF_DIR
}

function install_virtualenv {
    pip_install virtualenv
    sudo mkdir -p $VIRTUALENV_HOME && sudo chmod 755 -R $VIRTUALENV_HOME
    return 0
}

function mk_conf {
    local nginx_conf=$NGINX_CONF_DIR/$APPNAME.conf
    local uwsgi_conf=$UWSGI_CONF_DIR/$APPNAME.ini
    local supervisor_conf=$SUPERVISOR_CONF_DIR/$APPNAME.ini
    sudo mkdir -p $NGINX_CONF_DIR $UWSGI_CONF_DIR $SUPERVISOR_CONF_DIR
    sudo touch $nginx_conf $uwsgi_conf $supervisor_conf

    debug "mk_conf: $uwsgi_conf"
    sudo crudini --set $uwsgi_conf uwsgi http-socket 127.0.0.1:$UWSGI_PORT
    sudo crudini --set $uwsgi_conf uwsgi socket-timeout 60
    sudo crudini --set $uwsgi_conf uwsgi chmod-socket 660
    sudo crudini --set $uwsgi_conf uwsgi master true
    sudo crudini --set $uwsgi_conf uwsgi workers 8
    sudo crudini --set $uwsgi_conf uwsgi no-orphans true
    sudo crudini --set $uwsgi_conf uwsgi vacuum true
    sudo crudini --set $uwsgi_conf uwsgi log-date true
    sudo crudini --set $uwsgi_conf uwsgi user $USERNAME
    sudo crudini --set $uwsgi_conf uwsgi gid $USERNAME
    sudo crudini --set $uwsgi_conf uwsgi limit-as 1024
    sudo crudini --set $uwsgi_conf uwsgi reload-on-as 1024
    sudo crudini --set $uwsgi_conf uwsgi max-requests 10000
    sudo crudini --set $uwsgi_conf uwsgi virtualenv $VIRTUALENV_HOME/$VENV
    sudo crudini --set $uwsgi_conf uwsgi chdir $DST_DIR/$APPNAME
    sudo crudini --set $uwsgi_conf uwsgi wsgi $WSGI
    sudo crudini --set $uwsgi_conf uwsgi touch-reload $uwsgi_conf
    # sudo crudini --set $uwsgi_conf uwsgi harakiri 60
    # sudo crudini --set $uwsgi_conf uwsgi log-x-forwarded-for true
    # sudo crudini --set $uwsgi_conf uwsgi logto $DST_DIR/$APPNAME/files/logs/uwsgi.log
    # sudo crudini --set $uwsgi_conf uwsgi py-autoreload 60


    debug "mk_conf: $supervisor_conf"
    sudo crudini --set $supervisor_conf program:uwsgi command "$(which uwsgi) --ini $uwsgi_conf"
    sudo crudini --set $supervisor_conf program:uwsgi directory $DST_DIR/$APPNAME
    sudo crudini --set $supervisor_conf program:uwsgi startsecs 0
    sudo crudini --set $supervisor_conf program:uwsgi stopwaitsecs 0
    sudo crudini --set $supervisor_conf program:uwsgi autostart true
    sudo crudini --set $supervisor_conf program:uwsgi autorestart true
    sudo crudini --set $supervisor_conf program:uwsgi user $USERNAME

    if [ ${RELEASE#*-} = 'enshi' ]; then
        sudo crudini --set $supervisor_conf program:twserver command "$VIRTUALENV_HOME/$VENV/bin/python $DST_DIR/$APPNAME/manage.pyc twserver"
        sudo crudini --set $supervisor_conf program:twserver directory $DST_DIR/$APPNAME
        sudo crudini --set $supervisor_conf program:twserver autostart true
        sudo crudini --set $supervisor_conf program:twserver autorestart true

        sudo crudini --set $supervisor_conf program:twclient command "$VIRTUALENV_HOME/$VENV/bin/python $DST_DIR/$APPNAME/manage.pyc twclient"
        sudo crudini --set $supervisor_conf program:twclient directory $DST_DIR/$APPNAME
        sudo crudini --set $supervisor_conf program:twclient autostart true
        sudo crudini --set $supervisor_conf program:twclient autorestart true

        sudo crudini --set $supervisor_conf program:task command "$VIRTUALENV_HOME/$VENV/bin/python $DST_DIR/$APPNAME/manage.pyc start_tasks"
        sudo crudini --set $supervisor_conf program:task directory $DST_DIR/$APPNAME
        sudo crudini --set $supervisor_conf program:task autostart true
        sudo crudini --set $supervisor_conf program:task autorestart true
        sudo crudini --set $supervisor_conf program:task user $USERNAME

        sudo crudini --set $supervisor_conf program:rqworker command "$VIRTUALENV_HOME/$VENV/bin/python $DST_DIR/$APPNAME/manage.pyc rqworker"
        sudo crudini --set $supervisor_conf program:rqworker process_name '%(program_name)s-%(process_num)d'
        sudo crudini --set $supervisor_conf program:rqworker numprocs 4
        sudo crudini --set $supervisor_conf program:rqworker directory $DST_DIR/$APPNAME
        sudo crudini --set $supervisor_conf program:rqworker autostart true
        sudo crudini --set $supervisor_conf program:rqworker autorestart true
        sudo crudini --set $supervisor_conf program:rqworker user $USERNAME
    fi

    if [ ${RELEASE#*-} = 'changsha' ]; then
        sudo crudini --set $supervisor_conf program:cameraroom_task command "$VIRTUALENV_HOME/$VENV/bin/python $DST_DIR/$APPNAME/manage.pyc start_cameraroom_tasks"
        sudo crudini --set $supervisor_conf program:cameraroom_task autostart true
        sudo crudini --set $supervisor_conf program:cameraroom_task autorestart true
        sudo crudini --set $supervisor_conf program:cameraroom_task user $USERNAME
    fi

    local listen_ports=''
    for i in $NGINX_PORT; do listen_ports="$listen_ports\n\tlisten $i;"; done
    debug "mk_conf: /etc/nginx/sites-enabled/$APPNAME.$port.conf"
    # server {
    #     listen $port;
    #     server_name _;

    #     location /public {
    #         alias $DST_DIR/$APPNAME/files/public;
    #     }

    #     location ^~ /ws {
    #         proxy_pass http://127.0.0.1:8001/ws;
    #         proxy_redirect default;
    #         proxy_set_header Host $host:8001;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-Host $host:$server_port;
    #         proxy_set_header X-Forwarded-Server $host:$server_port;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header Cookie $http_cookie;

    #         proxy_http_version 1.1;
    #         proxy_set_header Upgrade $http_upgrade;
    #         proxy_set_header Connection "upgrade";
    #     }

    #     location / {
    #         proxy_pass http://127.0.0.1:$backend;
    #         proxy_redirect default;
    #         proxy_set_header Host    $host:$server_port;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-Host $host:$server_port;
    #         proxy_set_header X-Forwarded-Server $host:$server_port;
    #         proxy_set_header X-Forwarded-For  $proxy_add_x_forwarded_for;
    #         proxy_set_header Cookie $http_cookie;
    #     }
    # }
    sudo bash -c "
        echo -e 'server {\n$listen_ports\nserver_name _;\n\nlocation /public {\n\talias $DST_DIR/$APPNAME/files/public;\n}\n\nlocation /ws {\n\tproxy_pass http://127.0.0.1:$WEBSOCKET_PORT/ws;\n\tproxy_redirect\tdefault;\n\tproxy_set_header\tHost \$host:$WEBSOCKET_PORT;\n\tproxy_set_header\tX-Real-IP \$remote_addr;\n\tproxy_set_header\tX-Forwarded-Host \$host:\$server_port;\n\tproxy_set_header\tX-Forwarded-Server \$host:\$server_port;\n\tproxy_set_header\tX-Forwarded-For \$proxy_add_x_forwarded_for;\n\tproxy_set_header\tCookie \$http_cookie;\n\tproxy_http_version 1.1;\n\tproxy_set_header Upgrade \$http_upgrade;\n\tproxy_set_header Connection 'upgrade';\n}\n\nlocation / {\n\tproxy_pass http://127.0.0.1:$UWSGI_PORT;\n\tproxy_redirect\tdefault;\n\tproxy_set_header\tHost \$host:\$server_port;\n\tproxy_set_header\tX-Real-IP \$remote_addr;\n\tproxy_set_header\tX-Forwarded-Host \$host:\$server_port;\n\tproxy_set_header\tX-Forwarded-Server \$host:\$server_port;\n\tproxy_set_header\tX-Forwarded-For \$proxy_add_x_forwarded_for;\n\tproxy_set_header\tCookie \$http_cookie;\n}\n}' > $nginx_conf
    "

    grep -q net.core.somaxconn /etc/sysctl.conf || sudo bash -c "echo 'net.core.somaxconn=32768' >> /etc/sysctl.conf"
    sudo sysctl -p
}

function create_user {
    if ! getent group $USERNAME >/dev/null; then
        debug "Creating a group called $USERNAME"
        sudo groupadd $USERNAME
    fi

    if ! getent passwd $USERNAME >/dev/null; then
        debug "Creating a user called $USERNAME"
        sudo useradd -g $USERNAME -r $USERNAME -s /bin/bash -M
        sudo usermod -a -G adm $USERNAME
        sudo usermod -a -G sudo $USERNAME
        local pass=`readtp 为账户$USERNAME设置密码 $USERNAME`
        if is_ubuntu; then
            echo $USERNAME:$pass | sudo chpasswd
        elif is_fedora; then
            echo $pass | sudo passwd $USERNAME --stdin
        fi
    fi
}

function create_db {
    require_or_die DB_PASS
    sudo mysql -uroot -p$DB_PASS -e "
        create database if not exists \`$DB_NAME\` default character set utf8;
        grant all privileges on \`$DB_NAME\`.* to '$DB_USER'@'localhost' identified by '$DB_PASS';
        grant all privileges on \`$DB_NAME\`.* to '$DB_USER'@'%' identified by '$DB_PASS';
    "
}

function create_cron {
    local cron_conf=/etc/cron.d/$APPNAME
    debug 'create cron jobs.'
    sudo touch $cron_conf
    sudo bash -c "echo '# Dynamic jobs added by BBT deploy script.' > $cron_conf"
    sudo bash -c "echo '0 5 * * * root service nginx stop' >> $cron_conf"
    sudo bash -c "echo '5 5 * * * root supervisorctl stop all' >> $cron_conf"
    sudo bash -c "echo '10 5 * * * root supervisorctl start all' >> $cron_conf"
    sudo bash -c "echo '15 5 * * * root service nginx start' >> $cron_conf"
}

function deploy_app {
    if [ -d $DST_DIR/$APPNAME ]; then
        warning "
            $DST_DIR/$APPNAME exists.
        "
        if [ "$(echo `readtp 'overwrite existing files?' 'Y' 10` | tr A-Z a-z)" =  'y' ]; then
            sudo rm -rf $DST_DIR/$APPNAME
        else
            sudo chmod -R 755 $DST_DIR/$APPNAME
        fi
    fi

    sudo mkdir -p $VIRTUALENV_HOME $DST_DIR/$APPNAME $TOP_DIR/pip_pkgs
    cd $VIRTUALENV_HOME && sudo virtualenv $VENV
    if [ ! -d $VIRTUALENV_HOME/$VENV ]; then
        error 'failed to create virtualenv.'
        exit 1
    fi
    source $VIRTUALENV_HOME/$VENV/bin/activate

    if [[ "$DEBUG" = "1" || "$(tr A-Z a-z <<<  $DEBUG)" = "true" ]]; then
        WSGI="${APPNAME}.wsgi"
        sudo $VIRTUALENV_HOME/$VENV/bin/pip download \
            -d $TOP_DIR/pip_pkgs django \
            --trusted-host $TRUSTED_HOST

        sudo $VIRTUALENV_HOME/$VENV/bin/pip install \
            --no-index --find-links=$TOP_DIR/pip_pkgs django \
            -i $PIP_MIRROR --trusted-host $TRUSTED_HOST
        sudo bash -c "rm -rf $DST_DIR/$APPNAME && cd $DST_DIR && $VIRTUALENV_HOME/$VENV/bin/django-admin startproject $APPNAME;"
        sudo sed -i 's:ALLOWED_HOSTS = \[\]:ALLOWED_HOSTS = \["*"\]:g' $DST_DIR/$APPNAME/$APPNAME/settings.py
        sudo chown -R $USERNAME:$USERNAME $DST_DIR/$APPNAME
        sudo su -s /bin/bash -c "cd $DST_DIR/$APPNAME && $VIRTUALENV_HOME/$VENV/bin/python manage.py makemigrations" $USERNAME
        sudo su -s /bin/bash -c "cd $DST_DIR/$APPNAME && $VIRTUALENV_HOME/$VENV/bin/python manage.py migrate" $USERNAME

    else
        if [ ! -e $TOP_DIR/$RELEASE-*.tar.gz ]; then
            error "missing source code file $TOP_DIR/$RELEASE-*.tar.gz"
            exit 1
        fi
        sudo tar -xvzf $TOP_DIR/$RELEASE-*.tar.gz -C $DST_DIR/$APPNAME > /dev/null
        if [ -e $DST_DIR/$APPNAME/settings.sample.ini ]; then
            debug "mk_conf: $DST_DIR/$APPNAME/settings.ini"
            sudo cp $DST_DIR/$APPNAME/settings.sample.ini $DST_DIR/$APPNAME/settings.ini
        fi
        sudo touch $DST_DIR/$APPNAME/settings.ini
        sudo crudini --set $DST_DIR/$APPNAME/settings.ini db host "$DB_HOST"
        sudo crudini --set $DST_DIR/$APPNAME/settings.ini db port "$DB_PORT"
        sudo crudini --set $DST_DIR/$APPNAME/settings.ini db name "$DB_NAME"
        sudo crudini --set $DST_DIR/$APPNAME/settings.ini db user "$DB_USER"
        sudo crudini --set $DST_DIR/$APPNAME/settings.ini db password "$DB_PASS"

        if [ -e $DST_DIR/$APPNAME/requirements.txt ]; then
            local n=1
            while true; do
                sudo $VIRTUALENV_HOME/$VENV/bin/pip download \
                    -d $TOP_DIR/pip_pkgs \
                    -i $PIP_MIRROR \
                    --trusted-host $TRUSTED_HOST \
                    -r $DST_DIR/$APPNAME/requirements.txt 2>&1 && break
                (( n = n + 1 ))
                if [[ n -eq 5 ]]; then
                    error "pip packages download failed."
                fi
            done
            sudo bash -c "CFLAGS='-Wno-error' $VIRTUALENV_HOME/$VENV/bin/pip install \
                --no-index --find-links=$TOP_DIR/pip_pkgs \
                -i $PIP_MIRROR \
                --trusted-host $TRUSTED_HOST \
                -r $DST_DIR/$APPNAME/requirements.txt"
        fi

        sudo chmod -R 755 $VIRTUALENV_HOME/$VENV
        sudo chown -R $USERNAME:$USERNAME $DST_DIR/$APPNAME
        sudo chmod -R 755 $DST_DIR/$APPNAME
        sudo su -s /bin/bash -c "source $VIRTUALENV_HOME/$VENV/bin/activate && cd $DST_DIR/$APPNAME && python manage.pyc migrate" $USERNAME

        if [ -e $TOP_DIR/GroupTB.sql.gz ]; then
            debug 'load post_init.sql.'
            gunzip < $TOP_DIR/GroupTB.sql.gz | mysql -u$DB_USER -p$DB_PASS $DB_NAME
        fi
    fi
}

function restart_service {
    sudo service supervisor restart
    sudo service nginx restart
    sudo service cron restart
}

if [[ "$1" == "install" ]]; then
    set -ex
    check_sudo
    check_venv
    create_user
    install_libs
    install_pip
    install_mariadb_server
    # install_memcached
    install_redis_server
    install_nginx
    install_uwsgi
    install_supervisor
    install_virtualenv

    create_user
    create_db
    deploy_app
    mk_conf
    create_cron
    restart_service
    debug "
        Installing finished.
        UI is avialable on:
        http://$(get_inet_addr "$(ls /sys/class/net/ | grep -vE '^lo$' | head -n 1)"):$(awk '{print $1}' <<< $NGINX_PORT)
        Username: admin Password:admin
    "
    set +ex
fi
