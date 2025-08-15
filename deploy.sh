#!/bin/bash

# UniMind AI Assistant - 快速部署脚本
# Universal AI Assistant with Multi-Agent Architecture

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  UniMind AI Assistant 部署脚本${NC}"
    echo -e "${BLUE}  基于多智能体架构的通用型AI助手${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

check_requirements() {
    print_message "🔍 检查系统要求..." $BLUE
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_message "❌ Docker 未安装，请先安装 Docker" $RED
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_message "❌ Docker Compose 未安装，请先安装 Docker Compose" $RED
        exit 1
    fi
    
    print_message "✅ Docker 和 Docker Compose 已安装" $GREEN
}

setup_environment() {
    print_message "🔧 设置环境变量..." $BLUE
    
    if [ ! -f ".env" ]; then
        if [ -f "env.docker.template" ]; then
            cp env.docker.template .env
            print_message "📝 已创建 .env 文件，请编辑配置 OpenAI API Key" $YELLOW
        else
            print_message "❌ 环境变量模板文件不存在" $RED
            exit 1
        fi
    else
        print_message "✅ .env 文件已存在" $GREEN
    fi
    
    # 检查是否配置了OpenAI API Key
    if grep -q "your_openai_api_key_here" .env; then
        print_message "⚠️  请在 .env 文件中配置正确的 OPENAI_API_KEY" $YELLOW
        read -p "是否现在编辑 .env 文件? (y/n): " edit_env
        if [ "$edit_env" = "y" ] || [ "$edit_env" = "Y" ]; then
            ${EDITOR:-nano} .env
        fi
    fi
}

create_directories() {
    print_message "📁 创建必要的目录..." $BLUE
    
    mkdir -p data/phone_auto_answer
    mkdir -p data/voice_responses
    mkdir -p logs
    mkdir -p screenshots
    
    print_message "✅ 目录创建完成" $GREEN
}

build_and_start() {
    print_message "🏗️  构建 Docker 镜像..." $BLUE
    
    # 检查是否使用镜像源
    read -p "是否使用中国镜像源? (y/n): " use_mirror
    
    if [ "$use_mirror" = "y" ] || [ "$use_mirror" = "Y" ]; then
        export PIP_MIRROR=true
        print_message "🇨🇳 使用中国镜像源构建" $YELLOW
    else
        export PIP_MIRROR=false
    fi
    
    # 构建镜像
    docker-compose build --no-cache
    
    print_message "🚀 启动服务..." $BLUE
    docker-compose up -d
    
    # 等待服务启动
    print_message "⏳ 等待服务启动..." $BLUE
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_message "✅ 服务启动成功!" $GREEN
        print_message "🌐 访问地址: http://localhost:8501" $GREEN
    else
        print_message "❌ 服务启动失败，请检查日志" $RED
        docker-compose logs --tail=20 unimind
        exit 1
    fi
}

show_logs() {
    print_message "📋 显示实时日志 (Ctrl+C 退出)..." $BLUE
    docker-compose logs -f unimind
}

show_status() {
    print_message "📊 服务状态:" $BLUE
    docker-compose ps
    
    print_message "\n🔗 有用的命令:" $BLUE
    echo "  查看日志:     docker-compose logs -f unimind"
    echo "  停止服务:     docker-compose down"
    echo "  重启服务:     docker-compose restart"
    echo "  进入容器:     docker-compose exec unimind bash"
    echo "  检查健康:     curl http://localhost:8501/_stcore/health"
}

cleanup() {
    print_message "🧹 清理环境..." $BLUE
    docker-compose down
    docker system prune -f
    print_message "✅ 清理完成" $GREEN
}

main() {
    print_header
    
    case "${1:-start}" in
        "start")
            check_requirements
            setup_environment
            create_directories
            build_and_start
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "stop")
            print_message "🛑 停止服务..." $BLUE
            docker-compose down
            print_message "✅ 服务已停止" $GREEN
            ;;
        "restart")
            print_message "🔄 重启服务..." $BLUE
            docker-compose restart
            print_message "✅ 服务已重启" $GREEN
            ;;
        "clean")
            cleanup
            ;;
        "help"|"-h"|"--help")
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  start    - 启动服务 (默认)"
            echo "  stop     - 停止服务"
            echo "  restart  - 重启服务"
            echo "  logs     - 查看日志"
            echo "  status   - 查看状态"
            echo "  clean    - 清理环境"
            echo "  help     - 显示帮助"
            ;;
        *)
            print_message "❌ 未知命令: $1" $RED
            print_message "使用 '$0 help' 查看帮助" $YELLOW
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'print_message "\n👋 部署中断" $YELLOW; exit 1' INT

# 执行主函数
main "$@"
