@echo off
echo 正在尝试推送到GitHub...
:retry
git push origin main
if %errorlevel% equ 0 (
    echo 推送成功！
    pause
    exit /b 0
) else (
    echo 推送失败，5秒后重试...
    timeout /t 5 /nobreak >nul
    goto retry
)