// 主要应用逻辑
class EfficiencyPlatform {
    constructor() {
        this.currentTab = 'dashboard';
        this.currentDashboardTab = 'metrics';
        this.filters = {
            department: 'all',
            date: ''
        };
        this.init();
    }

    init() {
        this.bindEvents();
        this.initFilters();
        this.loadInitialData();
    }

    bindEvents() {
        // 主导航切换
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = e.target.dataset.tab;
                this.switchMainTab(tab);
            });
        });

        // 数据大屏子标签切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.dashboardTab;
                this.switchDashboardTab(tab);
            });
        });

        // 筛选条件变化监听
        const departmentFilter = document.getElementById('department-filter');
        const dateFilter = document.getElementById('date-filter');
        
        if (departmentFilter) {
            departmentFilter.addEventListener('change', (e) => {
                this.filters.department = e.target.value;
            });
        }
        
        if (dateFilter) {
            dateFilter.addEventListener('change', (e) => {
                this.filters.date = e.target.value;
            });
        }
    }

    initFilters() {
        // 初始化日期筛选为当前月份
        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) {
            const now = new Date();
            const currentMonth = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0');
            dateFilter.value = currentMonth;
            this.filters.date = currentMonth;
        }
    }

    switchMainTab(tab) {
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // 切换内容区域
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(tab).classList.add('active');

        this.currentTab = tab;

        // 加载对应模块数据
        this.loadTabData(tab);
    }

    switchDashboardTab(tab) {
        // 更新标签状态
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-dashboard-tab="${tab}"]`).classList.add('active');

        // 切换内容
        document.querySelectorAll('.dashboard-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tab).classList.add('active');

        this.currentDashboardTab = tab;
        this.loadDashboardData(tab);
    }

    async loadInitialData() {
        await this.loadDashboardData('metrics');
    }

    async loadTabData(tab) {
        switch(tab) {
            case 'dashboard':
                await this.loadDashboardData(this.currentDashboardTab);
                break;
            case 'ai-analysis':
                await this.loadAIAnalysis();
                break;
            case 'settings':
                await this.loadSettings();
                break;
        }
    }

    async loadDashboardData(tab) {
        try {
            // 构建包含筛选条件的请求参数
            const params = new URLSearchParams();
            if (this.filters.department && this.filters.department !== 'all') {
                params.append('department', this.filters.department);
            }
            if (this.filters.date) {
                params.append('date', this.filters.date);
            }
            
            const queryString = params.toString();
            const url = `/api/dashboard/${tab}${queryString ? '?' + queryString : ''}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            switch(tab) {
                case 'metrics':
                    this.updateMetrics(data);
                    break;
                case 'trends':
                    this.updateTrends(data);
                    break;
                case 'rankings':
                    this.updateRankings(data);
                    break;
                case 'details':
                    this.updateDetails(data);
                    break;
            }
        } catch (error) {
            console.error('加载数据失败:', error);
            this.showErrorMessage('数据加载失败，请稍后重试');
        }
    }

    showErrorMessage(message) {
        // 显示错误提示
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    // 应用筛选条件
    applyFilters() {
        // 重新加载当前标签的数据
        this.loadDashboardData(this.currentDashboardTab);
        
        // 显示筛选应用成功提示
        this.showSuccessMessage('筛选条件已应用');
    }

    showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        successDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            z-index: 1001;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 2000);
    }

    updateMetrics(data) {
        document.getElementById('commit-count').textContent = data.commitCount || '--';
        document.getElementById('bug-fix-rate').textContent = (data.bugFixRate || '--') + '%';
        document.getElementById('code-quality').textContent = data.codeQuality || '--';
        document.getElementById('delivery-efficiency').textContent = (data.deliveryEfficiency || '--') + '%';
    }

    updateTrends(data) {
        // 趋势图表更新逻辑
        console.log('更新趋势数据:', data);
    }

    updateRankings(data) {
        const container = document.getElementById('developer-rankings');
        container.innerHTML = '';
        
        if (data.rankings) {
            data.rankings.forEach((item, index) => {
                const rankItem = document.createElement('div');
                rankItem.className = 'rank-item';
                rankItem.innerHTML = `
                    <span class="rank">${index + 1}</span>
                    <span class="name">${item.name}</span>
                    <span class="score">${item.score}</span>
                `;
                container.appendChild(rankItem);
            });
        }
    }

    updateDetails(data) {
        const tbody = document.getElementById('details-tbody');
        tbody.innerHTML = '';
        
        if (data.details) {
            data.details.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.projectName}</td>
                    <td>${item.developer}</td>
                    <td>${item.commits}</td>
                    <td>${item.codeLines}</td>
                    <td>${item.bugs}</td>
                    <td>${item.completionTime}</td>
                `;
                tbody.appendChild(row);
            });
        }
    }

    async loadAIAnalysis() {
        try {
            const response = await fetch('/api/ai-analysis');
            const data = await response.json();
            document.getElementById('ai-results').innerHTML = data.analysis || 'AI分析结果将在这里显示...';
        } catch (error) {
            console.error('加载AI分析失败:', error);
        }
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();
            
            if (data.refreshInterval) {
                document.getElementById('refresh-interval').value = data.refreshInterval;
            }
            if (data.emailNotifications !== undefined) {
                document.getElementById('email-notifications').checked = data.emailNotifications;
            }
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    }
}

// 保存设置函数
async function saveSettings() {
    const refreshInterval = document.getElementById('refresh-interval').value;
    const emailNotifications = document.getElementById('email-notifications').checked;
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                refreshInterval,
                emailNotifications
            })
        });
        
        if (response.ok) {
            alert('设置保存成功!');
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        alert('保存设置失败!');
    }
}

// 全局筛选应用函数
function applyFilters() {
    if (window.efficiencyPlatform) {
        window.efficiencyPlatform.applyFilters();
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.efficiencyPlatform = new EfficiencyPlatform();
});

// 在main.js中添加重置功能
function resetFilters() {
    // 重置部门筛选为默认值
    const departmentFilter = document.getElementById('department-filter');
    departmentFilter.value = 'all';
    
    // 重置日期筛选为当前月份
    const dateFilter = document.getElementById('date-filter');
    const currentDate = new Date();
    const currentMonth = currentDate.getFullYear() + '-' + String(currentDate.getMonth() + 1).padStart(2, '0');
    dateFilter.value = currentMonth;
    
    // 自动应用默认筛选条件
    applyFilters();
    
    // 显示重置成功提示
    showMessage('筛选条件已重置', 'success');
}

// 修改应用筛选函数名称显示
function applyFilters() {
    const department = document.getElementById('department-filter').value;
    const date = document.getElementById('date-filter').value;
    
    // 显示加载状态
    const applyBtn = document.querySelector('.filter-apply-btn');
    const originalText = applyBtn.textContent;
    applyBtn.textContent = '筛选中...';
    applyBtn.disabled = true;
    
    // 应用筛选逻辑
    const platform = new EfficiencyPlatform();
    platform.applyFilters(department, date).then(() => {
        // 恢复按钮状态
        applyBtn.textContent = originalText;
        applyBtn.disabled = false;
        
        // 显示成功提示
        showMessage('筛选条件已应用', 'success');
    }).catch(() => {
        // 恢复按钮状态
        applyBtn.textContent = originalText;
        applyBtn.disabled = false;
        
        // 显示错误提示
        showMessage('筛选失败，请重试', 'error');
    });
}

// 主题切换功能
class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.updateThemeIcon();
        
        // 监听系统主题变化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.currentTheme = e.matches ? 'dark' : 'light';
                this.applyTheme(this.currentTheme);
                this.updateThemeIcon();
            }
        });
    }

    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.updateThemeIcon();
        localStorage.setItem('theme', newTheme);
        
        // 显示切换成功提示
        this.showThemeMessage(`已切换到${newTheme === 'dark' ? '暗色' : '亮色'}模式`);
    }

    updateThemeIcon() {
        const themeIcon = document.querySelector('.theme-icon');
        if (themeIcon) {
            themeIcon.textContent = this.currentTheme === 'dark' ? '☀️' : '🌙';
        }
    }

    showThemeMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'theme-message';
        messageDiv.textContent = message;
        messageDiv.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: var(--apple-blue);
            color: var(--apple-white);
            padding: 12px 20px;
            border-radius: var(--apple-radius-md);
            box-shadow: var(--apple-shadow-md);
            z-index: 1001;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(messageDiv);
        
        // 触发动画
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateX(0)';
        }, 10);
        
        // 移除消息
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateX(100%)';
            setTimeout(() => {
                messageDiv.remove();
            }, 300);
        }, 2000);
    }
}

// 全局主题切换函数
function toggleTheme() {
    if (window.themeManager) {
        window.themeManager.toggleTheme();
    }
}

// 初始化主题管理器
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});