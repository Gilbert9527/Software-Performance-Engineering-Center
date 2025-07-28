@echo off
echo ========================================
echo GitHub 推送重试脚本
echo ========================================
echo.

echo 检查当前状态...
git status --porcelain
if %errorlevel% neq 0 (
    echo 错误：Git仓库状态异常
    pause
    exit /b 1
)

echo.
echo 显示待推送的提交...
git log --oneline origin/main..HEAD

echo.
echo 正在尝试推送到GitHub...
set /a attempts=0
set /a max_attempts=10

:retry
set /a attempts+=1
echo.
echo [尝试 %attempts%/%max_attempts%] 推送中...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 推送成功！
    echo.
    git log --oneline -3
    echo.
    pause
    exit /b 0
) else (
    if %attempts% geq %max_attempts% (
        echo.
        echo ❌ 达到最大重试次数，推送失败
        echo.
        echo 可能的解决方案：
        echo 1. 检查网络连接
        echo 2. 检查GitHub访问权限
        echo 3. 尝试使用VPN或代理
        echo 4. 稍后再试
        echo.
        pause
        exit /b 1
    )
    echo ⚠️  推送失败，10秒后重试... (%attempts%/%max_attempts%)
    timeout /t 10 /nobreak >nul
    goto retry
)