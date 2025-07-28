// 系统设置相关功能

// 默认设置配置
const defaultSettings = {
    refreshInterval: 30,
    emailNotifications: false
};

// 加载设置
function loadSettings() {
    const savedSettings = localStorage.getItem('systemSettings');
    const settings = savedSettings ? JSON.parse(savedSettings) : defaultSettings;
    
    // 应用设置到界面
    const refreshIntervalEl = document.getElementById('refresh-interval');
    const emailNotificationsEl = document.getElementById('email-notifications');
    
    if (refreshIntervalEl) {
        refreshIntervalEl.value = settings.refreshInterval;
    }
    if (emailNotificationsEl) {
        emailNotificationsEl.checked = settings.emailNotifications;
    }
    
    return settings;
}

// 保存设置
function saveSettings() {
    const refreshIntervalEl = document.getElementById('refresh-interval');
    const emailNotificationsEl = document.getElementById('email-notifications');
    
    const settings = {
        refreshInterval: refreshIntervalEl ? parseInt(refreshIntervalEl.value) : defaultSettings.refreshInterval,
        emailNotifications: emailNotificationsEl ? emailNotificationsEl.checked : defaultSettings.emailNotifications
    };
    
    localStorage.setItem('systemSettings', JSON.stringify(settings));
    
    // 显示保存成功提示
    showNotification('设置已保存', 'success');
}

// 重置设置
function resetSettings() {
    if (confirm('确定要重置所有设置为默认值吗？')) {
        localStorage.removeItem('systemSettings');
        loadSettings();
        showNotification('设置已重置为默认值', 'info');
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    
    // 根据类型设置背景色
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#4CAF50';
            break;
        case 'error':
            notification.style.backgroundColor = '#f44336';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ff9800';
            break;
        default:
            notification.style.backgroundColor = '#2196F3';
    }
    
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 自动隐藏
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 页面加载时初始化设置
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载设置，确保DOM元素已存在
    setTimeout(() => {
        loadSettings();
    }, 100);
});