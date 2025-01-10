@echo off
setlocal enabledelayedexpansion

:: 颜色定义
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set NC=[0m

:: 打印带颜色的消息
:print_message
set "color=%~1"
set "message=%~2"
echo %color%%message%%NC%
exit /b

:: 检查管理员权限
:check_admin
net session >nul 2>&1
if %errorLevel% == 0 (
    exit /b 0
) else (
    call :print_message %RED% "错误: 需要管理员权限运行此脚本"
    call :print_message %YELLOW% "请以管理员身份重新运行"
    exit /b 1
)

:: 安装Neo4j
:install_neo4j
call :print_message %YELLOW% "正在安装Neo4j..."
:: 检查是否已安装winget
where winget >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %RED% "错误: 未找到winget命令"
    call :print_message %YELLOW% "请先安装Windows Package Manager (winget)"
    exit /b 1
)
:: 使用winget安装Neo4j
winget install Neo4j.Neo4j
if %ERRORLEVEL% neq 0 (
    call :print_message %RED% "Neo4j安装失败"
    exit /b 1
)
call :print_message %GREEN% "Neo4j安装完成"
exit /b 0

:: 安装Redis
:install_redis
call :print_message %YELLOW% "正在安装Redis..."
:: 使用winget安装Redis
winget install Redis
if %ERRORLEVEL% neq 0 (
    call :print_message %RED% "Redis安装失败"
    exit /b 1
)
call :print_message %GREEN% "Redis安装完成"
exit /b 0

:: 检查Neo4j
:check_neo4j
call :print_message %YELLOW% "检查Neo4j..."
where neo4j >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %YELLOW% "未找到Neo4j，准备安装..."
    call :install_neo4j
) else (
    call :print_message %GREEN% "Neo4j已安装"
    :: 检查服务状态
    sc query "neo4j" | find "RUNNING" >nul
    if %ERRORLEVEL% neq 0 (
        call :print_message %YELLOW% "Neo4j服务未运行，正在启动..."
        net start neo4j
    )
)
exit /b 0

:: 检查Redis
:check_redis
call :print_message %YELLOW% "检查Redis..."
where redis-cli >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %YELLOW% "未找到Redis，准备安装..."
    call :install_redis
) else (
    call :print_message %GREEN% "Redis已安装"
    :: 检查服务状态
    sc query "Redis" | find "RUNNING" >nul
    if %ERRORLEVEL% neq 0 (
        call :print_message %YELLOW% "Redis服务未运行，正在启动..."
        net start Redis
    )
)
exit /b 0

:: 安装项目依赖
:install_dependencies
call :print_message %YELLOW% "安装项目依赖..."
:: 确保使用Windows版本的FAISS
poetry add "faiss-windows@^1.7.4"
poetry remove faiss-cpu
poetry install
call :print_message %GREEN% "依赖安装完成"
exit /b 0

:: 主函数
:main
call :print_message %GREEN% "开始设置Agent Memory System环境..."

:: 检查管理员权限
call :check_admin || exit /b 1

:: 检查必要的命令
call :check_command "python" || exit /b 1
call :check_command "pip" || exit /b 1
call :check_command "curl" || exit /b 1

:: 检查Python版本
call :check_python_version || exit /b 1

:: 创建必要的目录
call :create_directories || exit /b 1

:: 安装和配置Poetry
call :install_poetry || exit /b 1
call :configure_poetry || exit /b 1

:: 安装项目依赖
call :install_dependencies || exit /b 1

:: 创建环境变量文件
call :create_env_file || exit /b 1

:: 检查并安装数据库
call :check_neo4j || exit /b 1
call :check_redis || exit /b 1

call :print_message %GREEN% "环境设置完成!"
call :print_message %YELLOW% "请确保:"
call :print_message %YELLOW% "1. 配置.env文件中的必要参数"
call :print_message %YELLOW% "2. Neo4j服务已启动"
call :print_message %YELLOW% "3. Redis服务已启动"
call :print_message %GREEN% "然后运行: poetry run python -m agent_memory_system.main"

exit /b 0

:: 执行主函数
call :main 