@echo off
echo ========================================
echo    AI违规检测系统 - Windows启动脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo 选择启动模式:
echo 1. 快速启动 (推荐)
echo 2. 完整检查启动
echo 3. 安装依赖
echo.
set /p choice=请输入选择 (1-3):

if "%choice%"=="1" (
    echo 启动快速模式...
    python quick_start.py
) else if "%choice%"=="2" (
    echo 启动完整检查模式...
    python run.py --mode web
) else if "%choice%"=="3" (
    echo 安装系统依赖...
    python install.py
) else (
    echo 无效选择，使用快速启动模式...
    python quick_start.py
)

echo.
echo 系统已退出
pause
