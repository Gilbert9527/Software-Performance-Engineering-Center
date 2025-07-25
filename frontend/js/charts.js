// 图表管理类
class ChartsManager {
    constructor() {
        this.charts = {};
        this.weekLabels = ['第一周', '第二周', '第三周', '第四周'];
        this.init();
    }

    init() {
        // 等待DOM加载完成后初始化图表
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.initializeCharts();
            });
        } else {
            this.initializeCharts();
        }
    }

    initializeCharts() {
        // 初始化所有图表
        this.initThroughputChart();
        this.initDeliveredRequirementsChart();
        this.initNewRequirementsChart();
        this.initDeliveryCycleChart();
        this.initOnlineDefectsChart();
        this.initReopenRateChart();
        this.initCodeEquivalentChart();
    }

    // 获取苹果风格的图表配置
    getAppleChartConfig(hasYAxis = true) {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? '#2c2c2e' : '#ffffff',
                    titleColor: isDark ? '#f2f2f7' : '#1d1d1f',
                    bodyColor: isDark ? '#f2f2f7' : '#1d1d1f',
                    borderColor: isDark ? '#48484a' : '#e8e8ed',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: false,
                    titleFont: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                        size: 13
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: isDark ? '#aeaeb2' : '#6d6d70',
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                y: {
                    display: hasYAxis,
                    grid: {
                        color: isDark ? '#3a3a3c' : '#f2f2f7',
                        lineWidth: 1
                    },
                    ticks: {
                        color: isDark ? '#aeaeb2' : '#6d6d70',
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                            size: 12
                        }
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.4,
                    borderWidth: 3
                },
                point: {
                    radius: 6,
                    hoverRadius: 8,
                    borderWidth: 2,
                    backgroundColor: '#ffffff'
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        };
    }

    // 1. 吞吐率折线图（有Y轴，显示百分比0-100%）
    initThroughputChart() {
        const ctx = document.getElementById('throughputChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(true);
        config.scales.y.min = 0;
        config.scales.y.max = 100;
        config.scales.y.ticks.callback = function(value) {
            return value + '%';
        };

        this.charts.throughput = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#007aff',
                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                    pointBackgroundColor: '#007aff',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 2. 本月非事务型交付需求数量折线图（无Y轴，数据显示在折线上）
    initDeliveredRequirementsChart() {
        const ctx = document.getElementById('deliveredRequirementsChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(false);
        config.plugins.datalabels = {
            display: true,
            align: 'top',
            color: '#007aff',
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                size: 14,
                weight: '600'
            }
        };

        this.charts.deliveredRequirements = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#30d158',
                    backgroundColor: 'rgba(48, 209, 88, 0.1)',
                    pointBackgroundColor: '#30d158',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 3. 本月新增交付需求数量折线图
    initNewRequirementsChart() {
        const ctx = document.getElementById('newRequirementsChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(false);
        config.plugins.datalabels = {
            display: true,
            align: 'top',
            color: '#ff9500',
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                size: 14,
                weight: '600'
            }
        };

        this.charts.newRequirements = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#ff9500',
                    backgroundColor: 'rgba(255, 149, 0, 0.1)',
                    pointBackgroundColor: '#ff9500',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 4. 需求交付周期P75分位折线图
    initDeliveryCycleChart() {
        const ctx = document.getElementById('deliveryCycleChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(false);
        config.plugins.datalabels = {
            display: true,
            align: 'top',
            color: '#007aff',
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                size: 14,
                weight: '600'
            },
            formatter: function(value) {
                return value + '天';
            }
        };

        this.charts.deliveryCycle = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#007aff',
                    backgroundColor: 'rgba(0, 122, 255, 0.1)',
                    pointBackgroundColor: '#007aff',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 5. 线上缺陷数折线图
    initOnlineDefectsChart() {
        const ctx = document.getElementById('onlineDefectsChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(false);
        config.plugins.datalabels = {
            display: true,
            align: 'top',
            color: '#ff3b30',
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                size: 14,
                weight: '600'
            }
        };

        this.charts.onlineDefects = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#ff3b30',
                    backgroundColor: 'rgba(255, 59, 48, 0.1)',
                    pointBackgroundColor: '#ff3b30',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 6. Reopen率折线图
    initReopenRateChart() {
        const ctx = document.getElementById('reopenRateChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(false);
        config.plugins.datalabels = {
            display: true,
            align: 'top',
            color: '#ff9500',
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                size: 14,
                weight: '600'
            },
            formatter: function(value) {
                return value + '%';
            }
        };

        this.charts.reopenRate = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#ff9500',
                    backgroundColor: 'rgba(255, 149, 0, 0.1)',
                    pointBackgroundColor: '#ff9500',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 7. 代码当量折线图
    initCodeEquivalentChart() {
        const ctx = document.getElementById('codeEquivalentChart');
        if (!ctx) return;

        const config = this.getAppleChartConfig(false);
        config.plugins.datalabels = {
            display: true,
            align: 'top',
            color: '#30d158',
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif',
                size: 14,
                weight: '600'
            }
        };

        this.charts.codeEquivalent = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.weekLabels,
                datasets: [{
                    data: [], // 空数据，等待后端提供
                    borderColor: '#30d158',
                    backgroundColor: 'rgba(48, 209, 88, 0.1)',
                    pointBackgroundColor: '#30d158',
                    pointBorderColor: '#ffffff',
                    fill: true
                }]
            },
            options: config
        });
    }

    // 更新图表数据的方法（供后端数据接入时使用）
    updateChartData(chartName, data) {
        if (this.charts[chartName] && data) {
            this.charts[chartName].data.datasets[0].data = data;
            this.charts[chartName].update('none');
        }
    }

    // 更新所有图表的主题（暗色/亮色模式切换时调用）
    updateChartsTheme() {
        Object.keys(this.charts).forEach(chartName => {
            const chart = this.charts[chartName];
            if (chart) {
                // 重新获取配置并更新
                const hasYAxis = chartName === 'throughput';
                const newConfig = this.getAppleChartConfig(hasYAxis);
                
                // 更新图表配置
                chart.options = { ...chart.options, ...newConfig };
                chart.update('none');
            }
        });
    }

    // 销毁所有图表
    destroyCharts() {
        Object.keys(this.charts).forEach(chartName => {
            if (this.charts[chartName]) {
                this.charts[chartName].destroy();
                delete this.charts[chartName];
            }
        });
    }
}

// 全局图表管理器实例
let chartsManager;

// 初始化图表管理器
document.addEventListener('DOMContentLoaded', () => {
    chartsManager = new ChartsManager();
});

// 主题切换时更新图表
document.addEventListener('themeChanged', () => {
    if (chartsManager) {
        setTimeout(() => {
            chartsManager.updateChartsTheme();
        }, 100);
    }
});

// 导出图表管理器供其他模块使用
window.ChartsManager = ChartsManager;