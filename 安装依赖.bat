@echo off
chcp 65001 >nul
echo.
echo ========================================
echo        PyInstaller 安装/更新检查
echo ========================================
echo.

:: 获取当前Python路径
for /f "delims=" %%i in ('where python 2^>nul') do set "PYTHON_PATH=%%i"
if not defined PYTHON_PATH (
    echo [错误] 找不到 python 命令
    pause
    exit /b 1
)

echo [INFO] Python 路径: %PYTHON_PATH%
echo.

:: 强制使用同一个Python的pip重新安装
echo [INFO] 强制重新安装 PyInstaller...
"%PYTHON_PATH%" -m pip install pyinstaller --force-reinstall --no-warn-script-location -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [OK] 安装完成，验证中...
    echo ========================================
    echo.
    
    :: 用 python -m 方式验证（不需要 PATH）
    "%PYTHON_PATH%" -m PyInstaller --version
    if %errorlevel% equ 0 (
        echo.
        echo [OK] 安装成功，可以运行 pybuilder.py 了
    ) else (
        echo.
        echo [错误] PyInstaller 模块验证失败
        echo 尝试运行: "%PYTHON_PATH%" -m PyInstaller --version
    )
) else (
    echo.
    echo [错误] 安装失败
)

echo.
pause
