// AI分析模块 - 完整功能实现

// 全局变量
let currentFile = null;
let currentAnalysisId = null;
let currentPage = 1;
let totalPages = 1;

// 初始化AI分析模块
function initAIAnalysis() {
    setupTabs();
    setupFileUpload();
    loadAIConfig();
    loadUsageStats();
    
    // 如果当前在AI分析页面，加载历史记录
    if (document.getElementById('ai-analysis').classList.contains('active')) {
        loadAnalysisHistory();
    }
}

// 设置标签页切换
function setupTabs() {
    const tabBtns = document.querySelectorAll('.ai-tab-btn');
    const tabContents = document.querySelectorAll('.ai-tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-ai-tab');
            
            // 更新按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 更新内容显示
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            
            // 根据targetTab找到对应的内容元素
            let targetContent;
            if (targetTab === 'settings') {
                targetContent = document.getElementById('ai-settings');
            } else {
                targetContent = document.getElementById(targetTab);
            }
            
            if (targetContent) {
                targetContent.classList.add('active');
                
                // 根据标签页加载相应内容
                if (targetTab === 'history') {
                    loadAnalysisHistory();
                } else if (targetTab === 'settings') {
                    loadAIConfig();
                    loadUsageStats();
                }
            }
        });
    });
}

// 设置文件上传功能
function setupFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    if (!uploadArea || !fileInput) return;
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            selectFile(files[0]);
        }
    });
    
    // 点击上传
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectFile(e.target.files[0]);
        }
    });
}

// 选择文件
function selectFile(file) {
    // 使用改进的验证函数
    const errors = validateFile(file);
    
    if (errors.length > 0) {
        errors.forEach(error => showError(error));
        return;
    }
    
    currentFile = file;
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    // 显示文件信息
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    document.getElementById('file-type').textContent = fileExtension.toUpperCase();
    
    // 显示文件信息和操作按钮
    document.getElementById('file-info').style.display = 'flex';
    document.getElementById('upload-actions').style.display = 'flex';
    
    // 隐藏上传区域
    document.getElementById('upload-area').style.display = 'none';
    
    showSuccess(`文件 "${file.name}" 已选择，可以开始分析`);
}

// 清除选择的文件
function clearFile() {
    currentFile = null;
    
    // 隐藏文件信息和操作按钮
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('upload-actions').style.display = 'none';
    document.getElementById('upload-progress').style.display = 'none';
    document.getElementById('analysis-results').style.display = 'none';
    
    // 显示上传区域
    document.getElementById('upload-area').style.display = 'block';
    
    // 清空文件输入
    document.getElementById('file-input').value = '';
}

// 开始分析
async function startAnalysis() {
    if (!currentFile) {
        showError('请先选择文件');
        return;
    }
    
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // 禁用分析按钮
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '分析中...';
    
    // 显示进度条
    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = '准备上传...';
    
    try {
        const formData = new FormData();
        formData.append('file', currentFile);
        
        // 获取自定义提示词
        const customPrompt = document.getElementById('custom-prompt').value.trim();
        if (customPrompt) {
            formData.append('custom_prompt', customPrompt);
        }
        
        // 模拟上传进度
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 70) progress = 70;
            progressFill.style.width = progress + '%';
            progressText.textContent = `上传中... ${Math.round(progress)}%`;
        }, 500);
        
        // 添加超时提示
        const timeoutWarning = setTimeout(() => {
            progressText.textContent = 'AI分析中，请耐心等待...（大文件可能需要1-2分钟）';
        }, 30000); // 30秒后显示提示
        
        // 设置前端超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 150000); // 150秒超时
        
        const response = await fetch('/api/ai-analysis/upload', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        clearTimeout(timeoutWarning);
        
        clearInterval(progressInterval);
        progressFill.style.width = '90%';
        progressText.textContent = 'AI分析中...';
        
        const result = await response.json();
        
        // 完成进度
        progressFill.style.width = '100%';
        progressText.textContent = '分析完成';
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 1000);
        
        if (result.success) {
            currentAnalysisId = result.analysis_id;
            displayAnalysisResult(result.report);
        } else {
            throw new Error(result.error || '分析失败');
        }
        
    } catch (error) {
        console.error('分析失败:', error);
        progressContainer.style.display = 'none';
        showError('分析失败: ' + error.message);
    } finally {
        // 恢复分析按钮
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '开始分析';
    }
}

// 显示分析结果
function displayAnalysisResult(report) {
    const analysisResults = document.getElementById('analysis-results');
    const analysisContent = document.getElementById('analysis-content');
    
    if (!report || !report.analysis) {
        showError('分析结果格式错误');
        return;
    }
    
    const fileInfo = report.file_info;
    const analysis = report.analysis;
    
    analysisContent.innerHTML = `
        <div class="analysis-report">
            <div class="report-header">
                <div class="file-summary">
                    <h4>文件信息</h4>
                    <div class="file-meta">
                        <span><strong>文件名:</strong> ${fileInfo.filename}</span>
                        <span><strong>格式:</strong> ${fileInfo.file_type.toUpperCase()}</span>
                        <span><strong>大小:</strong> ${formatFileSize(fileInfo.file_size)}</span>
                        <span><strong>分析时间:</strong> ${new Date(analysis.created_at).toLocaleString()}</span>
                    </div>
                </div>
                
                <div class="analysis-meta">
                    <span class="processing-time">处理时间: ${analysis.processing_time?.toFixed(2) || 0}秒</span>
                    <span class="model-used">模型: ${analysis.model_used || '未知'}</span>
                </div>
            </div>
            
            <div class="analysis-content-body">
                <h4>分析结果</h4>
                <div class="analysis-text">
                    ${analysis.content.replace(/\n/g, '<br>')}
                </div>
            </div>
        </div>
    `;
    
    analysisResults.style.display = 'block';
}

// 导出报告
async function exportReport(format) {
    if (!currentAnalysisId) {
        showError('没有可导出的分析结果');
        return;
    }
    
    try {
        const response = await fetch(`/api/ai-analysis/export/${currentAnalysisId}?format=${format}`);
        
        if (!response.ok) {
            throw new Error('导出失败');
        }
        
        // 创建下载链接
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_report_${currentAnalysisId}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showSuccess('报告导出成功');
    } catch (error) {
        console.error('导出失败:', error);
        showError('导出失败: ' + error.message);
    }
}

// 清除结果
function clearResults() {
    currentAnalysisId = null;
    document.getElementById('analysis-results').style.display = 'none';
}

// 加载分析历史
async function loadAnalysisHistory(page = 1) {
    try {
        const response = await fetch(`/api/ai-analysis/history?page=${page}&per_page=10`);
        const data = await response.json();
        
        const historyList = document.getElementById('history-list');
        const pagination = document.getElementById('history-pagination');
        
        if (data.items && data.items.length > 0) {
            historyList.innerHTML = data.items.map(item => `
                <div class="history-item">
                    <div class="history-info">
                        <div class="history-filename">${item.filename}</div>
                        <div class="history-meta">
                            <span class="file-type">${item.file_type.toUpperCase()}</span>
                            <span class="file-size">${formatFileSize(item.file_size)}</span>
                            <span class="analysis-time">${new Date(item.created_at).toLocaleString()}</span>
                            <span class="processing-time">${item.processing_time?.toFixed(2) || 0}s</span>
                        </div>
                    </div>
                    <div class="history-actions">
                        <button class="btn-secondary" onclick="viewAnalysisResult('${item.id}')">查看结果</button>
                        <button class="btn-secondary" onclick="exportReport('html', '${item.id}')">导出</button>
                        <button class="btn-danger" onclick="deleteAnalysisResult('${item.id}')">删除</button>
                    </div>
                </div>
            `).join('');
            
            // 更新分页
            currentPage = data.pagination.page;
            totalPages = data.pagination.pages;
            
            document.getElementById('page-info').textContent = 
                `第 ${currentPage} 页，共 ${totalPages} 页`;
            
            document.getElementById('prev-page').disabled = currentPage <= 1;
            document.getElementById('next-page').disabled = currentPage >= totalPages;
            
            pagination.style.display = 'flex';
        } else {
            historyList.innerHTML = '<div class="empty-state">暂无分析历史</div>';
            pagination.style.display = 'none';
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        document.getElementById('history-list').innerHTML = 
            '<div class="error-state">加载历史记录失败</div>';
    }
}

// 加载历史页面
function loadHistoryPage(page) {
    if (page >= 1 && page <= totalPages) {
        loadAnalysisHistory(page);
    }
}

// 刷新历史记录
function refreshHistory() {
    loadAnalysisHistory(currentPage);
}

// 查看分析结果
async function viewAnalysisResult(analysisId) {
    try {
        const response = await fetch(`/api/ai-analysis/results/${analysisId}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 切换到上传标签页并显示结果
        document.querySelector('[data-ai-tab="upload"]').click();
        
        currentAnalysisId = analysisId;
        displayAnalysisResult(data);
        
    } catch (error) {
        console.error('查看结果失败:', error);
        showError('查看结果失败: ' + error.message);
    }
}

// 删除分析结果
async function deleteAnalysisResult(analysisId) {
    if (!confirm('确定要删除这个分析结果吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/ai-analysis/results/${analysisId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('删除成功');
            refreshHistory();
        } else {
            throw new Error(result.error || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        showError('删除失败: ' + error.message);
    }
}

// 加载AI配置
async function loadAIConfig() {
    try {
        const response = await fetch('/api/ai-analysis/config');
        const data = await response.json();
        
        if (data.success) {
            const config = data.config;
            
            // 更新默认提示词设置
            document.getElementById('default-prompt-setting').value = 
                config.prompts.custom || config.prompts.default;
            
            // 更新系统信息
            document.getElementById('ai-model').textContent = config.siliconflow.model;
        }
        
        // 测试连接状态
        testConnection();
        
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

// 测试连接
async function testConnection() {
    const statusIndicator = document.getElementById('connection-status');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    
    statusText.textContent = '测试中...';
    statusDot.className = 'status-dot testing';
    
    try {
        const response = await fetch('/api/ai-analysis/config/test', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusText.textContent = '连接正常';
            statusDot.className = 'status-dot connected';
        } else {
            statusText.textContent = '连接失败';
            statusDot.className = 'status-dot disconnected';
        }
    } catch (error) {
        statusText.textContent = '连接错误';
        statusDot.className = 'status-dot disconnected';
    }
}

// 保存默认提示词
async function saveDefaultPrompt() {
    const prompt = document.getElementById('default-prompt-setting').value.trim();
    
    try {
        const response = await fetch('/api/ai-analysis/config/prompt', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('提示词设置已保存');
        } else {
            throw new Error(result.error || '保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        showError('保存失败: ' + error.message);
    }
}

// 重置默认提示词
function resetDefaultPrompt() {
    document.getElementById('default-prompt-setting').value = 
        '请分析以下文档内容，提供详细的分析报告，包括主要内容总结、关键信息提取和建议。';
}

// 加载使用统计
async function loadUsageStats() {
    try {
        const response = await fetch('/api/ai-analysis/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            
            document.getElementById('total-files').textContent = stats.total_files;
            document.getElementById('total-analyses').textContent = stats.total_analyses;
            document.getElementById('avg-time').textContent = stats.average_processing_time;
            document.getElementById('success-rate').textContent = stats.success_rate;
        }
    } catch (error) {
        console.error('加载统计信息失败:', error);
    }
}

// 提示词相关功能
function loadDefaultPrompt() {
    document.getElementById('custom-prompt').value = 
        '请分析以下文档内容，提供详细的分析报告，包括主要内容总结、关键信息提取和建议。';
}

function clearPrompt() {
    document.getElementById('custom-prompt').value = '';
}

// 工具函数
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 通知系统
function createNotification(message, type = 'info', duration = 5000) {
    // 创建通知容器（如果不存在）
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // 添加图标
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icons[type] || icons.info}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="closeNotification(this.parentElement.parentElement)">×</button>
        </div>
    `;
    
    // 添加到容器
    container.appendChild(notification);
    
    // 显示动画
    setTimeout(() => notification.classList.add('show'), 100);
    
    // 自动关闭
    if (duration > 0) {
        setTimeout(() => closeNotification(notification), duration);
    }
    
    return notification;
}

function closeNotification(notification) {
    notification.classList.remove('show');
    setTimeout(() => {
        if (notification.parentElement) {
            notification.parentElement.removeChild(notification);
        }
    }, 300);
}

function showError(message) {
    createNotification(message, 'error', 8000);
}

function showSuccess(message) {
    createNotification(message, 'success', 4000);
}

function showWarning(message) {
    createNotification(message, 'warning', 6000);
}

function showInfo(message) {
    createNotification(message, 'info', 4000);
}

// 加载状态管理
function showLoading(element, message = '加载中...') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (!element) return;
    
    const loadingHTML = `
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;
    
    element.style.position = 'relative';
    element.insertAdjacentHTML('beforeend', loadingHTML);
}

function hideLoading(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (!element) return;
    
    const loadingOverlay = element.querySelector('.loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// 表单验证
function validateFile(file) {
    const errors = [];
    
    if (!file) {
        errors.push('请选择文件');
        return errors;
    }
    
    // 检查文件格式
    const allowedTypes = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.md', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        errors.push(`不支持的文件格式 "${fileExtension}"。支持的格式：${allowedTypes.join(', ')}`);
    }
    
    // 检查文件大小
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        errors.push(`文件大小 (${formatFileSize(file.size)}) 超过最大限制 (5MB)`);
    }
    
    if (file.size === 0) {
        errors.push('文件为空，请选择有效的文件');
    }
    
    return errors;
}

// 网络错误处理
function handleNetworkError(error, operation = '操作') {
    console.error(`${operation}失败:`, error);
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        showError(`网络连接失败，请检查网络连接后重试`);
    } else if (error.message.includes('timeout')) {
        showError(`${operation}超时，请稍后重试`);
    } else if (error.message.includes('401')) {
        showError('认证失败，请检查API配置');
    } else if (error.message.includes('403')) {
        showError('权限不足，请联系管理员');
    } else if (error.message.includes('404')) {
        showError('请求的资源不存在');
    } else if (error.message.includes('500')) {
        showError('服务器内部错误，请稍后重试');
    } else {
        showError(`${operation}失败: ${error.message || '未知错误'}`);
    }
}

// 重试机制
async function retryOperation(operation, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await operation();
        } catch (error) {
            if (i === maxRetries - 1) {
                throw error;
            }
            
            showWarning(`操作失败，正在重试... (${i + 1}/${maxRetries})`);
            await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
        }
    }
}

// 当页面加载完成时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保DOM完全加载
    setTimeout(initAIAnalysis, 100);
});