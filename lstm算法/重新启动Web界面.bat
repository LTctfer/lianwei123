@echo off
echo 🌍 重新启动智能空气质量预测系统...
echo.
echo 正在清除缓存并启动Web界面，请稍候...
echo.

cd /d "%~dp0"

REM 清除Streamlit缓存
streamlit cache clear

REM 启动应用
streamlit run simple_dashboard.py --server.port 8501

pause
