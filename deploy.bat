@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM UniMind AI Assistant - Windows 快速部署脚本
REM Universal AI Assistant with Multi-Agent Architecture

set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

echo.
echo %BLUE%========================================%NC%
echo %BLUE%  UniMind AI Assistant 部署脚本%NC%
echo %BLUE%  基于多智能体架构的通用型AI助手%NC%
echo %BLUE%========================================%NC%
echo.

if "%1"=="help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help
if "%1"=="stop" goto :stop_service
if "%1"=="restart" goto :restart_service
if "%1"=="logs" goto :show_logs
if "%1"=="status" goto :show_status
if "%1"=="clean" goto :cleanup

goto :start_deploy

:check_requirements
echo %BLUE%🔍 检查系统要求...%NC%

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Docker 未安装，请先安装 Docker Desktop%NC%
    echo %YELLOW%下载地址: https://www.docker.com/products/docker-desktop%NC%
    pause
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Docker Compose 未安装%NC%
    pause
    exit /b 1
)

echo %GREEN%✅ Docker 和 Docker Compose 已安装%NC%
goto :eof

:setup_environment
echo %BLUE%🔧 设置环境变量...%NC%

if not exist ".env" (
    if exist "env.docker.template" (
        copy env.docker.template .env >nul
        echo %YELLOW%📝 已创建 .env 文件，请编辑配置 OpenAI API Key%NC%
    ) else (
        echo %RED%❌ 环境变量模板文件不存在%NC%
        pause
        exit /b 1
    )
) else (
    echo %GREEN%✅ .env 文件已存在%NC%
)

REM 检查是否配置了OpenAI API Key
findstr /C:"your_openai_api_key_here" .env >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%⚠️  请在 .env 文件中配置正确的 OPENAI_API_KEY%NC%
    set /p edit_env="是否现在编辑 .env 文件? (y/n): "
    if /i "!edit_env!"=="y" (
        notepad .env
    )
)
goto :eof

:create_directories
echo %BLUE%📁 创建必要的目录...%NC%

if not exist "data\phone_auto_answer" mkdir data\phone_auto_answer
if not exist "data\voice_responses" mkdir data\voice_responses
if not exist "logs" mkdir logs
if not exist "screenshots" mkdir screenshots

echo %GREEN%✅ 目录创建完成%NC%
goto :eof

:build_and_start
echo %BLUE%🏗️  构建 Docker 镜像...%NC%

set /p use_mirror="是否使用中国镜像源? (y/n): "

if /i "!use_mirror!"=="y" (
    set PIP_MIRROR=true
    echo %YELLOW%🇨🇳 使用中国镜像源构建%NC%
) else (
    set PIP_MIRROR=false
)

REM 构建镜像
echo %BLUE%正在构建镜像，请稍候...%NC%
docker-compose build --no-cache
if errorlevel 1 (
    echo %RED%❌ 镜像构建失败%NC%
    pause
    exit /b 1
)

echo %BLUE%🚀 启动服务...%NC%
docker-compose up -d
if errorlevel 1 (
    echo %RED%❌ 服务启动失败%NC%
    pause
    exit /b 1
)

echo %BLUE%⏳ 等待服务启动...%NC%
timeout /t 10 /nobreak >nul

REM 检查服务状态
docker-compose ps | findstr "Up" >nul
if not errorlevel 1 (
    echo %GREEN%✅ 服务启动成功!%NC%
    echo %GREEN%🌐 访问地址: http://localhost:8501%NC%
) else (
    echo %RED%❌ 服务启动失败，请检查日志%NC%
    docker-compose logs --tail=20 unimind
    pause
    exit /b 1
)
goto :eof

:show_status
echo %BLUE%📊 服务状态:%NC%
docker-compose ps

echo.
echo %BLUE%🔗 有用的命令:%NC%
echo   查看日志:     docker-compose logs -f unimind
echo   停止服务:     docker-compose down
echo   重启服务:     docker-compose restart
echo   进入容器:     docker-compose exec unimind bash
echo   检查健康:     curl http://localhost:8501/_stcore/health
echo.
goto :eof

:show_logs
echo %BLUE%📋 显示实时日志 (Ctrl+C 退出)...%NC%
docker-compose logs -f unimind
goto :eof

:stop_service
echo %BLUE%🛑 停止服务...%NC%
docker-compose down
echo %GREEN%✅ 服务已停止%NC%
goto :eof

:restart_service
echo %BLUE%🔄 重启服务...%NC%
docker-compose restart
echo %GREEN%✅ 服务已重启%NC%
goto :eof

:cleanup
echo %BLUE%🧹 清理环境...%NC%
docker-compose down
docker system prune -f
echo %GREEN%✅ 清理完成%NC%
goto :eof

:show_help
echo 用法: %0 [命令]
echo.
echo 命令:
echo   start    - 启动服务 (默认)
echo   stop     - 停止服务
echo   restart  - 重启服务
echo   logs     - 查看日志
echo   status   - 查看状态
echo   clean    - 清理环境
echo   help     - 显示帮助
echo.
goto :eof

:start_deploy
call :check_requirements
if errorlevel 1 exit /b 1

call :setup_environment
if errorlevel 1 exit /b 1

call :create_directories
if errorlevel 1 exit /b 1

call :build_and_start
if errorlevel 1 exit /b 1

call :show_status

echo.
echo %GREEN%🎉 部署完成! 请访问 http://localhost:8501%NC%
echo %YELLOW%💡 使用 'deploy.bat logs' 查看运行日志%NC%
echo %YELLOW%💡 使用 'deploy.bat stop' 停止服务%NC%
echo.
pause
