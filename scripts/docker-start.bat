@echo off
setlocal enabledelayedexpansion

:: 颜色定义
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

:: 打印带颜色的消息
:print_message
set "color=%~1"
set "message=%~2"
echo %color%%message%%NC%
exit /b

:: 检查 Docker 是否安装
:check_docker
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    call :print_message %RED% "错误: Docker 未安装"
    call :print_message %YELLOW% "请先安装 Docker Desktop: https://docs.docker.com/desktop/"
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorLevel% neq 0 (
    call :print_message %RED% "错误: Docker Compose 未安装"
    call :print_message %YELLOW% "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit /b 1
)

call :print_message %GREEN% "✓ Docker 和 Docker Compose 已安装"
exit /b 0

:: 检查环境变量文件
:check_env_file
if not exist ".env" (
    call :print_message %YELLOW% "未找到 .env 文件，正在创建..."
    if exist "env.example" (
        copy env.example .env >nul
        call :print_message %GREEN% "✓ 已从 env.example 创建 .env 文件"
        call :print_message %YELLOW% "请编辑 .env 文件配置您的环境变量"
    ) else (
        call :print_message %RED% "错误: 未找到 env.example 文件"
        exit /b 1
    )
) else (
    call :print_message %GREEN% "✓ .env 文件已存在"
)
exit /b 0

:: 创建必要的目录
:create_directories
call :print_message %BLUE% "创建必要的目录..."
if not exist "data" mkdir data
if not exist "logs" mkdir logs
call :print_message %GREEN% "✓ 目录创建完成"
exit /b 0

:: 构建和启动服务
:start_services
call :print_message %BLUE% "构建和启动服务..."

if "%1"=="--with-ollama" (
    call :print_message %YELLOW% "启动包含 Ollama 的完整服务..."
    docker-compose --profile ollama up -d --build
) else (
    call :print_message %YELLOW% "启动基础服务..."
    docker-compose up -d --build
)

if %errorLevel% neq 0 (
    call :print_message %RED% "错误: 服务启动失败"
    exit /b 1
)

call :print_message %GREEN% "✓ 服务启动完成"
exit /b 0

:: 等待服务就绪
:wait_for_services
call :print_message %BLUE% "等待服务就绪..."

:: 等待 Neo4j
call :print_message %YELLOW% "等待 Neo4j 就绪..."
set timeout=60
:wait_neo4j
if %timeout% leq 0 (
    call :print_message %RED% "错误: Neo4j 启动超时"
    exit /b 1
)
docker-compose exec -T neo4j cypher-shell -u neo4j -p password123 "RETURN 1" >nul 2>&1
if %errorLevel% equ 0 (
    call :print_message %GREEN% "✓ Neo4j 已就绪"
    goto wait_redis
)
timeout /t 2 /nobreak >nul
set /a timeout-=2
goto wait_neo4j

:wait_redis
:: 等待 Redis
call :print_message %YELLOW% "等待 Redis 就绪..."
set timeout=30
:wait_redis_loop
if %timeout% leq 0 (
    call :print_message %RED% "错误: Redis 启动超时"
    exit /b 1
)
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %errorLevel% equ 0 (
    call :print_message %GREEN% "✓ Redis 已就绪"
    goto wait_app
)
timeout /t 1 /nobreak >nul
set /a timeout-=1
goto wait_redis_loop

:wait_app
:: 等待应用服务
call :print_message %YELLOW% "等待应用服务就绪..."
set timeout=60
:wait_app_loop
if %timeout% leq 0 (
    call :print_message %RED% "错误: 应用服务启动超时"
    exit /b 1
)
curl -f http://localhost:8000/health >nul 2>&1
if %errorLevel% equ 0 (
    call :print_message %GREEN% "✓ 应用服务已就绪"
    goto end_wait
)
timeout /t 2 /nobreak >nul
set /a timeout-=2
goto wait_app_loop

:end_wait
exit /b 0

:: 显示服务状态
:show_status
call :print_message %BLUE% "服务状态:"
docker-compose ps

call :print_message %BLUE% "服务访问地址:"
call :print_message %GREEN% "  - 应用 API: http://localhost:8000"
call :print_message %GREEN% "  - API 文档: http://localhost:8000/docs"
call :print_message %GREEN% "  - Neo4j 浏览器: http://localhost:7474"
call :print_message %GREEN% "  - Redis 客户端: localhost:6379"

if "%1"=="--with-ollama" (
    call :print_message %GREEN% "  - Ollama API: http://localhost:11434"
)
exit /b 0

:: 显示日志
:show_logs
call :print_message %BLUE% "显示服务日志 (按 Ctrl+C 退出)..."
docker-compose logs -f
exit /b 0

:: 停止服务
:stop_services
call :print_message %BLUE% "停止服务..."
docker-compose down
call :print_message %GREEN% "✓ 服务已停止"
exit /b 0

:: 清理服务
:cleanup_services
call :print_message %BLUE% "清理服务..."
docker-compose down -v --remove-orphans
call :print_message %GREEN% "✓ 服务已清理"
exit /b 0

:: 主函数
:main
if "%1"=="start" (
    call :check_docker
    call :check_env_file
    call :create_directories
    call :start_services "%2"
    call :wait_for_services
    call :show_status "%2"
    goto end
)

if "%1"=="stop" (
    call :stop_services
    goto end
)

if "%1"=="restart" (
    call :stop_services
    timeout /t 2 /nobreak >nul
    call :start_services "%2"
    call :wait_for_services
    call :show_status "%2"
    goto end
)

if "%1"=="logs" (
    call :show_logs
    goto end
)

if "%1"=="cleanup" (
    call :cleanup_services
    goto end
)

if "%1"=="status" (
    docker-compose ps
    goto end
)

:: 显示帮助信息
echo 用法: %0 {start^|stop^|restart^|logs^|cleanup^|status} [--with-ollama]
echo.
echo 命令:
echo   start       启动服务
echo   stop        停止服务
echo   restart     重启服务
echo   logs        显示日志
echo   cleanup     清理服务（包括数据卷）
echo   status      显示服务状态
echo.
echo 选项:
echo   --with-ollama  包含 Ollama 服务
echo.
echo 示例:
echo   %0 start              # 启动基础服务
echo   %0 start --with-ollama # 启动包含 Ollama 的完整服务
echo   %0 logs               # 查看日志
echo   %0 stop               # 停止服务
exit /b 1

:end 