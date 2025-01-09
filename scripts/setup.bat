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

:: 检查命令是否存在
:check_command
where %~1 >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %RED% "错误: 未找到命令 '%~1'"
    call :print_message %YELLOW% "请先安装 %~1"
    exit /b 1
)
exit /b 0

:: 检查Python版本
:check_python_version
for /f "tokens=2 delims=." %%I in ('python -c "import sys; print(sys.version.split()[0])"') do set PYTHON_VERSION=%%I
if %PYTHON_VERSION% LSS 8 (
    call :print_message %RED% "错误: Python版本必须 >= 3.8"
    call :print_message %YELLOW% "当前版本: %PYTHON_VERSION%"
    exit /b 1
)
exit /b 0

:: 创建目录
:create_directories
if not exist "data" mkdir "data"
if not exist "logs" mkdir "logs"
if not exist "data\faiss_index" mkdir "data\faiss_index"
call :print_message %GREEN% "创建必要目录完成"
exit /b 0

:: 安装Poetry
:install_poetry
where poetry >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %YELLOW% "正在安装Poetry..."
    curl -sSL https://install.python-poetry.org | python -
    call :print_message %GREEN% "Poetry安装完成"
) else (
    call :print_message %GREEN% "Poetry已安装"
)
exit /b 0

:: 配置Poetry
:configure_poetry
call :print_message %YELLOW% "配置Poetry..."
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
exit /b 0

:: 安装项目依赖
:install_dependencies
call :print_message %YELLOW% "安装项目依赖..."
poetry install
call :print_message %GREEN% "依赖安装完成"
exit /b 0

:: 创建环境变量文件
:create_env_file
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        call :print_message %GREEN% "创建.env文件"
    ) else (
        call :print_message %RED% "错误: 未找到.env.example文件"
        exit /b 1
    )
) else (
    call :print_message %GREEN% ".env文件已存在"
)
exit /b 0

:: 检查Neo4j
:check_neo4j
call :print_message %YELLOW% "检查Neo4j..."
where neo4j >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %RED% "警告: 未找到Neo4j"
    call :print_message %YELLOW% "请参考文档安装Neo4j: https://neo4j.com/docs/operations-manual/current/installation/"
) else (
    call :print_message %GREEN% "Neo4j已安装"
)
exit /b 0

:: 检查Redis
:check_redis
call :print_message %YELLOW% "检查Redis..."
where redis-cli >nul 2>nul
if %ERRORLEVEL% neq 0 (
    call :print_message %RED% "警告: 未找到Redis"
    call :print_message %YELLOW% "请参考文档安装Redis: https://redis.io/docs/getting-started/"
) else (
    call :print_message %GREEN% "Redis已安装"
)
exit /b 0

:: 主函数
:main
call :print_message %GREEN% "开始设置Agent Memory System环境..."

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

:: 检查数据库
call :check_neo4j
call :check_redis

call :print_message %GREEN% "环境设置完成!"
call :print_message %YELLOW% "请确保:"
call :print_message %YELLOW% "1. 配置.env文件中的必要参数"
call :print_message %YELLOW% "2. 启动Neo4j服务"
call :print_message %YELLOW% "3. 启动Redis服务"
call :print_message %GREEN% "然后运行: poetry run python -m agent_memory_system.main"

exit /b 0

:: 执行主函数
call :main 