// 系统设置相关功能

// 默认设置配置
const defaultSettings = {
    dataRefreshInterval: 5,
    autoRefresh: true,
    theme: 'light',
    chartAnimation: true,
    decimalPlaces: 2,
    enableNotifications: true,
    alertThreshold: true,
    exportFormat: 'excel',
    includeCharts: true,
    aiAnalysisLevel: 'detailed',
    autoAnalysis: false
};

// 加载设置
function loadSettings() {
    const savedSettings = localStorage.getItem('systemSettings');
    const settings = savedSettings ? JSON.parse(savedSettings) : defaultSettings;
    
    // 应用设置到界面
    document.getElementById('data-refresh-interval').value = settings.dataRefreshInterval;
    document.getElementById('auto-refresh').checked = settings.autoRefresh;
    document.getElementById('theme-select').value = settings.theme;
    document.getElementById('chart-animation').checked = settings.chartAnimation;
    document.getElementById('decimal-places').value = settings.decimalPlaces;
    document.getElementById('enable-notifications').checked = settings.enableNotifications;
    document.getElementById('alert-threshold').checked = settings.alertThreshold;
    document.getElementById('export-format').value = settings.exportFormat;
    document.getElementById('include-charts').checked = settings.includeCharts;
    document.getElementById('ai-analysis-level').value = settings.aiAnalysisLevel;
    document.getElementById('auto-analysis').checked = settings.autoAnalysis;
    
    return settings;
}

// 保存设置
function saveSettings() {
    const settings = {
        dataRefreshInterval: parseInt(document.getElementById('data-refresh-interval').value),
        autoRefresh: document.getElementById('auto-refresh').checked,
        theme: document.getElementById('theme-select').value,
        chartAnimation: document.getElementById('chart-animation').checked,
        decimalPlaces: parseInt(document.getElementById('decimal-places').value),
        enableNotifications: document.getElementById('enable-notifications').checked,
        alertThreshold: document.getElementById('alert-threshold').checked,
        exportFormat: document.getElementById('export-format').value,
        includeCharts: document.getElementById('include-charts').checked,
        aiAnalysisLevel: document.getElementById('ai-analysis-level').value,
        autoAnalysis: document.getElementById('auto-analysis').checked
    };
    
    localStorage.setItem('systemSettings', JSON.stringify(settings));
    
    // 应用设置
    applySettings(settings);
    
    // 显示保存成功提示
    showNotification('设置已保存', 'success');
}

// 应用设置
function applySettings(settings) {
    // 应用主题设置
    if (settings.theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else if (settings.theme === 'light') {
        document.body.classList.remove('dark-theme');
    } else if (settings.theme === 'auto') {
        // 跟随系统主题
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
    
    // 应用自动刷新设置
    if (settings.autoRefresh) {
        startAutoRefresh(settings.dataRefreshInterval);
    } else {
        stopAutoRefresh();
    }
    
    // 更新图表动画设置
    if (typeof Chart !== 'undefined') {
        Chart.defaults.animation = settings.chartAnimation;
    }
}

// 重置设置
function resetSettings() {
    if (confirm('确定要重置所有设置为默认值吗？')) {
        localStorage.removeItem('systemSettings');
        loadSettings();
        applySettings(defaultSettings);
        showNotification('设置已重置为默认值', 'info');
    }
}

// 导出设置
function exportSettings() {
    const settings = JSON.parse(localStorage.getItem('systemSettings') || JSON.stringify(defaultSettings));
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'system-settings.json';
    link.click();
    
    showNotification('设置配置已导出', 'success');
}

// 导入设置
function importSettings() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const settings = JSON.parse(e.target.result);
                    localStorage.setItem('systemSettings', JSON.stringify(settings));
                    loadSettings();
                    applySettings(settings);
                    showNotification('设置配置已导入', 'success');
                } catch (error) {
                    showNotification('导入失败：文件格式错误', 'error');
                }
            };
            reader.readAsText(file);
        }
    };
    
    input.click();
}

// 自动刷新相关变量
let autoRefreshInterval = null;

// 开始自动刷新
function startAutoRefresh(intervalMinutes) {
    stopAutoRefresh(); // 先停止现有的定时器
    
    autoRefreshInterval = setInterval(() => {
        if (typeof refreshDashboardData === 'function') {
            refreshDashboardData();
        }
    }, intervalMinutes * 60 * 1000);
}

// 停止自动刷新
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
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
    const settings = loadSettings();
    applySettings(settings);
    
    // 监听主题系统变化（仅在auto模式下）
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        const currentSettings = JSON.parse(localStorage.getItem('systemSettings') || JSON.stringify(defaultSettings));
        if (currentSettings.theme === 'auto') {
            if (e.matches) {
                document.body.classList.add('dark-theme');
            } else {
                document.body.classList.remove('dark-theme');
            }
        }
    });
});