#!/bin/bash
# AI-BOX Modbus PLC数据读取程序安装脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此脚本需要root权限运行"
        print_info "请使用: sudo $0"
        exit 1
    fi
}

# 检测操作系统
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "无法检测操作系统"
        exit 1
    fi
    
    print_info "检测到操作系统: $OS $VER"
}

# 更新系统包
update_system() {
    print_info "更新系统包..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt update && apt upgrade -y
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum update -y
    else
        print_warning "未知的操作系统，跳过系统更新"
    fi
    
    print_success "系统更新完成"
}

# 安装基础依赖
install_dependencies() {
    print_info "安装基础依赖..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt install -y python3 python3-pip python3-dev build-essential
        apt install -y sqlite3 git curl wget
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum install -y python3 python3-pip python3-devel gcc gcc-c++
        yum install -y sqlite git curl wget
    else
        print_error "不支持的操作系统: $OS"
        exit 1
    fi
    
    print_success "基础依赖安装完成"
}



# 安装Python依赖包
install_python_packages() {
    print_info "安装Python依赖包..."
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装依赖包
    pip3 install pymodbus
    pip3 install numpy pandas
    pip3 install pyyaml
    pip3 install flask
    pip3 install psutil
    pip3 install scipy
    pip3 install matplotlib
    
    print_success "Python依赖包安装完成"
}

# 创建工作目录
create_directories() {
    print_info "创建工作目录..."
    
    INSTALL_DIR="/opt/aibox-modbus-reader"
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/logs
    mkdir -p $INSTALL_DIR/data
    mkdir -p $INSTALL_DIR/backup

    print_success "工作目录创建完成: $INSTALL_DIR"
}

# 复制程序文件
copy_files() {
    print_info "复制程序文件..."
    
    # 检查源文件是否存在
    if [[ ! -f "aibox_s7_reader.py" ]]; then
        print_error "找不到aibox_s7_reader.py文件"
        exit 1
    fi

    # 复制文件并重命名
    cp aibox_s7_reader.py $INSTALL_DIR/aibox_modbus_reader.py
    cp s7_config.yaml $INSTALL_DIR/modbus_config.yaml

    # 设置权限
    chmod +x $INSTALL_DIR/aibox_modbus_reader.py
    chown -R root:root $INSTALL_DIR
    
    print_success "程序文件复制完成"
}

# 创建systemd服务
create_service() {
    print_info "创建systemd服务..."
    
    cat > /etc/systemd/system/aibox-modbus-reader.service << EOF
[Unit]
Description=AI-BOX Modbus PLC Data Reader
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/aibox_modbus_reader.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 环境变量
Environment=PYTHONPATH=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    systemctl daemon-reload
    
    print_success "systemd服务创建完成"
}

# 创建配置文件
create_config() {
    print_info "创建配置文件..."
    
    # 如果配置文件不存在，从模板创建
    if [[ ! -f "$INSTALL_DIR/config.yaml" ]]; then
        cp $INSTALL_DIR/modbus_config.yaml $INSTALL_DIR/config.yaml
        print_info "已创建配置文件: $INSTALL_DIR/config.yaml"
        print_warning "请编辑配置文件设置正确的PLC IP地址和数据点配置"
    fi
}

# 测试安装
test_installation() {
    print_info "测试安装..."
    
    # 测试Python导入
    python3 -c "import pymodbus; print('pymodbus导入成功')" || {
        print_error "pymodbus导入失败"
        exit 1
    }

    python3 -c "import numpy, pandas, yaml; print('其他依赖导入成功')" || {
        print_error "Python依赖导入失败"
        exit 1
    }

    # 测试程序语法
    python3 -m py_compile $INSTALL_DIR/aibox_modbus_reader.py || {
        print_error "程序语法检查失败"
        exit 1
    }
    
    print_success "安装测试通过"
}

# 显示安装后信息
show_post_install_info() {
    print_success "AI-BOX Modbus数据读取程序安装完成!"
    echo
    echo "安装目录: $INSTALL_DIR"
    echo "配置文件: $INSTALL_DIR/config.yaml"
    echo "日志目录: $INSTALL_DIR/logs"
    echo
    echo "下一步操作:"
    echo "1. 编辑配置文件设置PLC IP地址:"
    echo "   nano $INSTALL_DIR/config.yaml"
    echo
    echo "2. 启动服务:"
    echo "   systemctl start aibox-modbus-reader"
    echo
    echo "3. 设置开机自启:"
    echo "   systemctl enable aibox-modbus-reader"
    echo
    echo "4. 查看服务状态:"
    echo "   systemctl status aibox-modbus-reader"
    echo
    echo "5. 查看日志:"
    echo "   journalctl -u aibox-modbus-reader -f"
    echo
    echo "6. 手动运行 (调试模式):"
    echo "   cd $INSTALL_DIR && python3 aibox_modbus_reader.py"
    echo
}

# 主函数
main() {
    echo "========================================"
    echo "AI-BOX Modbus PLC数据读取程序安装脚本"
    echo "========================================"
    echo
    
    check_root
    detect_os
    
    print_info "开始安装..."
    
    update_system
    install_dependencies
    install_python_packages
    create_directories
    copy_files
    create_service
    create_config
    test_installation
    
    show_post_install_info
}

# 错误处理
trap 'print_error "安装过程中发生错误，请检查日志"; exit 1' ERR

# 运行主函数
main "$@"
