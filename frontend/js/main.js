// API基础URL配置
const API_BASE_URL = 'http://localhost:5000';

// 主要应用逻辑
class EfficiencyPlatform {
    constructor() {
        this.currentTab = 'dashboard';
        this.currentDashboardTab = 'metrics';
        this.rankingSortOrders = {
            saturation: 'desc',
            code: 'desc',
            defects: 'asc'  // 缺陷数量默认升序（越少越好）
        };
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

        // 排序切换 - 新的独立排行榜
        document.querySelectorAll('.sort-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const order = e.target.dataset.sort;
                const type = e.target.dataset.type;
                this.switchSortOrder(type, order);
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

    // 排序切换方法 - 新的独立排行榜
    switchSortOrder(type, order) {
        this.rankingSortOrders[type] = order;
        
        // 更新对应类型的排序按钮状态
        document.querySelectorAll(`.sort-btn[data-type="${type}"]`).forEach(btn => {
            btn.classList.toggle('active', btn.dataset.sort === order);
        });
        
        // 重新加载对应类型的排行榜数据
        this.loadSingleRankingData(type);
    }

    async loadInitialData() {
        await this.loadDepartments();
        await this.loadDashboardData('metrics');
    }

    async loadDepartments() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/departments`);
            const data = await response.json();
            
            const departmentFilter = document.getElementById('department-filter');
            if (departmentFilter && data.departments) {
                // 清空现有选项
                departmentFilter.innerHTML = '';
                
                // 添加"全部部门"选项
                const allOption = document.createElement('option');
                allOption.value = 'all';
                allOption.textContent = '全部部门';
                departmentFilter.appendChild(allOption);
                
                // 添加其他部门选项
                data.departments.forEach(dept => {
                    if (dept !== '全部部门') {
                        const option = document.createElement('option');
                        option.value = dept;
                        option.textContent = dept;
                        departmentFilter.appendChild(option);
                    }
                });
            }
        } catch (error) {
            console.error('加载部门列表失败:', error);
        }
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
            const url = `${API_BASE_URL}/api/dashboard/${tab}${queryString ? '?' + queryString : ''}`;
            
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

    // 加载所有排行榜数据
    async loadAllRankingsData() {
        await Promise.all([
            this.loadSingleRankingData('saturation'),
            this.loadSingleRankingData('code'),
            this.loadSingleRankingData('defects')
        ]);
    }

    // 加载单个排行榜数据
    async loadSingleRankingData(type) {
        try {
            const params = new URLSearchParams();
            if (this.filters.department && this.filters.department !== 'all') {
                params.append('department', this.filters.department);
            }
            if (this.filters.date) {
                params.append('date', this.filters.date);
            }
            params.append('type', type);
            params.append('sort', this.rankingSortOrders[type]);
            
            const queryString = params.toString();
            const url = `${API_BASE_URL}/api/dashboard/rankings${queryString ? '?' + queryString : ''}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            this.updateSingleRanking(type, data);
        } catch (error) {
            console.error(`加载${type}排行榜数据失败:`, error);
            this.showErrorMessage(`${type}排行榜数据加载失败，请稍后重试`);
        }
    }

    updateMetrics(data) {
        // 更新各项指标数据
        const elements = {
            'requirement-throughput': data.requirementThroughput || '--',
            'monthly-delivered-requirements': data.monthlyDeliveredRequirements || '--',
            'monthly-new-requirements': data.monthlyNewRequirements || '--',
            'delivery-cycle-p75': data.deliveryCycleP75 || '--',
            'online-defects': data.onlineDefects || '--',
            'reopen-rate': (data.reopenRate || '--') + (data.reopenRate ? '%' : ''),
            'emergency-releases': data.emergencyReleases || '--',
            'incident-count': data.incidentCount || '--',
            'work-saturation': (data.workSaturation || '--') + (data.workSaturation ? '%' : ''),
            'code-equivalent': data.codeEquivalent || '--'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateTrends(data) {
        // 趋势图表更新逻辑
        console.log('更新趋势数据:', data);
    }

    // 更新所有排行榜（兼容旧版本）
    updateRankings(data) {
        // 当切换到排行榜标签时，加载所有排行榜数据
        this.loadAllRankingsData();
    }

    // 更新单个排行榜
    updateSingleRanking(type, data) {
        const container = document.getElementById(`${type}-rankings`);
        if (!container) return;
        
        container.innerHTML = '';
        
        if (data.rankings && data.rankings.length > 0) {
            data.rankings.forEach((item, index) => {
                const rankItem = document.createElement('div');
                rankItem.className = 'rank-item';
                
                let valueDisplay = item.value;
                if (type === 'saturation') {
                    valueDisplay = `${item.value}%`;
                } else if (type === 'code') {
                    valueDisplay = `${item.value}行`;
                } else if (type === 'defects') {
                    valueDisplay = `${item.value}个`;
                }
                
                rankItem.innerHTML = `
                    <span class="rank">${index + 1}</span>
                    <span class="name">${item.name}</span>
                    <span class="value">${valueDisplay}</span>
                `;
                container.appendChild(rankItem);
            });
        } else {
            container.innerHTML = '<div class="no-data">暂无数据</div>';
        }
    }

    updateDetails(data) {
        const tbody = document.getElementById('details-tbody');
        tbody.innerHTML = '';
        
        if (data.details) {
            data.details.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.personName}</td>
                    <td>${item.positionName}</td>
                    <td>${item.projectName}</td>
                    <td>${item.saturation}%</td>
                    <td>${item.codeEquivalent}</td>
                    <td>${item.deliveredRequirements}</td>
                    <td>${item.totalHours}h</td>
                    <td>${item.aiUsageDays}</td>
                `;
                tbody.appendChild(row);
            });
        }
    }

    async loadAIAnalysis() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/ai-analysis`);
            const data = await response.json();
            const aiResults = document.getElementById('ai-results');
            if (aiResults) {
                aiResults.innerHTML = data.analysis || 'AI分析结果将在这里显示...';
            }
        } catch (error) {
            console.error('加载AI分析失败:', error);
        }
    }

    async loadSettings() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/settings`);
            const data = await response.json();
            
            const refreshInterval = document.getElementById('refresh-interval');
            const emailNotifications = document.getElementById('email-notifications');
            
            if (refreshInterval && data.refreshInterval) {
                refreshInterval.value = data.refreshInterval;
            }
            if (emailNotifications && data.emailNotifications !== undefined) {
                emailNotifications.checked = data.emailNotifications;
            }
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    }

    // 应用筛选条件
    applyFilters() {
        // 重新加载当前标签的数据
        this.loadDashboardData(this.currentDashboardTab);
        
        // 显示筛选应用成功提示
        this.showSuccessMessage('筛选条件已应用');
    }

    // 下载报告功能
    async downloadReport() {
        try {
            // 显示下载开始提示
            this.showSuccessMessage('正在生成PDF报告，请稍候...');
            
            // 构建包含筛选条件的请求参数
            const params = new URLSearchParams();
            if (this.filters.department && this.filters.department !== 'all') {
                params.append('department', this.filters.department);
            }
            if (this.filters.date) {
                params.append('date', this.filters.date);
            }
            
            const queryString = params.toString();
            const url = `${API_BASE_URL}/api/download/report${queryString ? '?' + queryString : ''}`;
            
            // 发起下载请求
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/pdf'
                }
            });
            
            if (!response.ok) {
                throw new Error('下载失败');
            }
            
            // 获取文件blob
            const blob = await response.blob();
            
            // 创建下载链接
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            
            // 生成文件名
            const department = this.filters.department === 'all' ? '全部部门' : this.filters.department;
            const date = this.filters.date || new Date().toISOString().slice(0, 7);
            link.download = `研发效能报告_${department}_${date}.pdf`;
            
            // 触发下载
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 清理URL对象
            window.URL.revokeObjectURL(downloadUrl);
            
            // 显示下载成功提示
            this.showSuccessMessage('PDF报告下载成功！');
            
        } catch (error) {
            console.error('下载报告失败:', error);
            this.showErrorMessage('下载报告失败，请稍后重试');
        }
    }

    showErrorMessage(message) {
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
}

// 保存设置函数
async function saveSettings() {
    const refreshInterval = document.getElementById('refresh-interval');
    const emailNotifications = document.getElementById('email-notifications');
    
    if (!refreshInterval || !emailNotifications) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                refreshInterval: refreshInterval.value,
                emailNotifications: emailNotifications.checked
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

// 全局下载报告函数
function downloadReport() {
    if (window.efficiencyPlatform) {
        window.efficiencyPlatform.downloadReport();
    }
}

// 重置筛选条件
function resetFilters() {
    const departmentFilter = document.getElementById('department-filter');
    const dateFilter = document.getElementById('date-filter');
    
    if (departmentFilter) {
        departmentFilter.value = 'all';
    }
    
    if (dateFilter) {
        const currentDate = new Date();
        const currentMonth = currentDate.getFullYear() + '-' + String(currentDate.getMonth() + 1).padStart(2, '0');
        dateFilter.value = currentMonth;
    }
    
    // 更新平台实例的筛选条件
    if (window.efficiencyPlatform) {
        window.efficiencyPlatform.filters.department = 'all';
        window.efficiencyPlatform.filters.date = dateFilter ? dateFilter.value : '';
        window.efficiencyPlatform.applyFilters();
    }
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
        
        // 触发主题变更事件，通知图表更新
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
        
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

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.efficiencyPlatform = new EfficiencyPlatform();
    window.themeManager = new ThemeManager();
});