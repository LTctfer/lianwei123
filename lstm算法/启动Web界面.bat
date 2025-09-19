@echo off
echo 🌍 启动智能空气质量预测系统...
echo.
echo 正在启动Web界面，请稍候...
echo.

cd /d "%~dp0"
streamlit run simple_dashboard.py

pause
