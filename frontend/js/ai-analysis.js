// AI分析相关功能

// 初始化AI分析模块
function initAIAnalysis() {
    loadDefaultAnalysis();
    setupFileUpload();
}

// 加载默认分析（基于当前数据）
async function loadDefaultAnalysis() {
    try {
        const department = getCurrentDepartment();
        const date = getCurrentDate();
        
        const response = await fetch(`/api/ai-analysis?department=${department}&date=${date}`);
        const data = await response.json();
        
        const analysisText = document.getElementById('default-analysis-text');
        if (analysisText) {
            analysisText.innerHTML = data.analysis;
        }
    } catch (error) {
        console.error('加载AI分析失败:', error);
        const analysisText = document.getElementById('default-analysis-text');
        if (analysisText) {
            analysisText.innerHTML = '<p style="color: #ff6b6b;">加载分析结果失败，请稍后重试</p>';
        }
    }
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
            handleFileUpload(files[0]);
        }
    });
    
    // 点击上传
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

// 处理文件上传
async function handleFileUpload(file) {
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const analysisResults = document.getElementById('analysis-results');
    
    // 显示进度条
    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = '准备上传...';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        // 模拟上传进度
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
            progressText.textContent = `上传中... ${Math.round(progress)}%`;
        }, 200);
        
        const response = await fetch('/api/ai-analysis/upload', {
            method: 'POST',
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressText.textContent = '分析中...';
        
        const result = await response.json();
        
        // 隐藏进度条
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 1000);
        
        if (result.success) {
            displayAnalysisResult(result.analysis);
        } else {
            throw new Error(result.error || '分析失败');
        }
        
    } catch (error) {
        console.error('文件上传失败:', error);
        progressContainer.style.display = 'none';
        
        // 显示错误信息
        const analysisContent = document.getElementById('analysis-content');
        if (analysisContent) {
            analysisContent.innerHTML = `
                <div class="error-message">
                    <h3>分析失败</h3>
                    <p style="color: #ff6b6b;">${error.message}</p>
                    <button onclick="loadDefaultAnalysis()" class="retry-btn">重新加载默认分析</button>
                </div>
            `;
        }
    }
}

// 显示分析结果
function displayAnalysisResult(analysis) {
    const analysisContent = document.getElementById('analysis-content');
    if (!analysisContent) return;
    
    analysisContent.innerHTML = `
        <div class="file-analysis-result">
            <h3>文件分析结果</h3>
            
            <div class="file-info">
                <h4>文件信息</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">文件名:</span>
                        <span class="info-value">${analysis.file_info.name}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">文件大小:</span>
                        <span class="info-value">${formatFileSize(analysis.file_info.size)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">行数:</span>
                        <span class="info-value">${analysis.file_info.lines}</span>
                    </div>
                </div>
            </div>
            
            <div class="analysis-summary">
                <h4>分析摘要</h4>
                <p>${analysis.summary}</p>
            </div>
            
            <div class="analysis-insights">
                <h4>关键洞察</h4>
                <ul>
                    ${analysis.insights.map(insight => `<li>${insight}</li>`).join('')}
                </ul>
            </div>
            
            <div class="analysis-recommendations">
                <h4>改进建议</h4>
                <ul>
                    ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
            
            <div class="analysis-actions">
                <button onclick="loadDefaultAnalysis()" class="action-btn secondary">返回默认分析</button>
                <button onclick="document.getElementById('file-input').click()" class="action-btn primary">分析其他文件</button>
            </div>
        </div>
    `;
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 获取当前部门（从dashboard模块获取）
function getCurrentDepartment() {
    const departmentFilter = document.getElementById('department-filter');
    return departmentFilter ? departmentFilter.value : '全部部门';
}

// 获取当前日期（从dashboard模块获取）
function getCurrentDate() {
    const dateFilter = document.getElementById('date-filter');
    return dateFilter ? dateFilter.value : new Date().toISOString().slice(0, 7);
}

// 当页面加载完成时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保DOM完全加载
    setTimeout(initAIAnalysis, 100);
});