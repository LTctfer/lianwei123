// 污染源溯源系统主要JavaScript文件

// 页面加载完成后执行
$(document).ready(function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 添加页面加载动画
    $('body').addClass('fade-in');
    
    // 自动隐藏警告消息
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
});

// 通用工具函数
const Utils = {
    // 显示加载状态
    showLoading: function(element, text = '处理中...') {
        const originalText = element.innerHTML;
        element.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
        element.disabled = true;
        return originalText;
    },
    
    // 隐藏加载状态
    hideLoading: function(element, originalText) {
        element.innerHTML = originalText;
        element.disabled = false;
    },
    
    // 显示成功消息
    showSuccess: function(message) {
        this.showAlert(message, 'success');
    },
    
    // 显示错误消息
    showError: function(message) {
        this.showAlert(message, 'danger');
    },
    
    // 显示警告消息
    showWarning: function(message) {
        this.showAlert(message, 'warning');
    },
    
    // 显示信息消息
    showInfo: function(message) {
        this.showAlert(message, 'info');
    },
    
    // 通用警告框显示
    showAlert: function(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // 移除现有的警告框
        $('.alert').remove();
        
        // 添加新的警告框
        $('main.container').prepend(alertHtml);
        
        // 自动隐藏
        setTimeout(function() {
            $('.alert').fadeOut('slow');
        }, 5000);
    },
    
    // 格式化数字
    formatNumber: function(num, decimals = 2) {
        return parseFloat(num).toFixed(decimals);
    },
    
    // 验证表单
    validateForm: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        const inputs = form.querySelectorAll('input[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });
        
        return isValid;
    },
    
    // 下载文件
    downloadFile: function(data, filename, type = 'text/plain') {
        const blob = new Blob([data], { type: type });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
};

// 文件上传处理
const FileUpload = {
    // 验证文件类型
    validateFile: function(file, allowedTypes = ['csv', 'json', 'txt']) {
        if (!file) return false;
        
        const extension = file.name.split('.').pop().toLowerCase();
        return allowedTypes.includes(extension);
    },
    
    // 验证文件大小
    validateSize: function(file, maxSizeMB = 16) {
        if (!file) return false;
        
        const maxSizeBytes = maxSizeMB * 1024 * 1024;
        return file.size <= maxSizeBytes;
    },
    
    // 读取文件内容
    readFile: function(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                resolve(e.target.result);
            };
            reader.onerror = function(e) {
                reject(e);
            };
            reader.readAsText(file);
        });
    }
};

// 数据处理
const DataProcessor = {
    // 处理CSV数据
    parseCSV: function(csvText) {
        const lines = csvText.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];
        
        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim()) {
                const values = lines[i].split(',').map(v => v.trim());
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index];
                });
                data.push(row);
            }
        }
        
        return data;
    },
    
    // 处理JSON数据
    parseJSON: function(jsonText) {
        try {
            return JSON.parse(jsonText);
        } catch (e) {
            throw new Error('无效的JSON格式');
        }
    },
    
    // 验证监测数据格式
    validateMonitoringData: function(data) {
        const requiredFields = ['station_id', 'x', 'y', 'z', 'concentration'];
        
        if (!Array.isArray(data)) {
            throw new Error('监测数据必须是数组格式');
        }
        
        data.forEach((item, index) => {
            requiredFields.forEach(field => {
                if (!(field in item)) {
                    throw new Error(`第${index + 1}行缺少必需字段: ${field}`);
                }
            });
            
            // 验证数值字段
            ['x', 'y', 'z', 'concentration'].forEach(field => {
                if (isNaN(parseFloat(item[field]))) {
                    throw new Error(`第${index + 1}行${field}字段必须是数值`);
                }
            });
        });
        
        return true;
    },
    
    // 验证气象数据格式
    validateMeteorologicalData: function(data) {
        const requiredFields = ['wind_speed', 'wind_direction', 'temperature', 'pressure', 'humidity', 'stability_class'];
        
        requiredFields.forEach(field => {
            if (!(field in data)) {
                throw new Error(`缺少必需字段: ${field}`);
            }
        });
        
        // 验证数值字段
        ['wind_speed', 'wind_direction', 'temperature', 'pressure', 'humidity'].forEach(field => {
            if (isNaN(parseFloat(data[field]))) {
                throw new Error(`${field}字段必须是数值`);
            }
        });
        
        // 验证稳定度等级
        const validStabilityClasses = ['A', 'B', 'C', 'D', 'E', 'F'];
        if (!validStabilityClasses.includes(data.stability_class)) {
            throw new Error('大气稳定度必须是A-F中的一个');
        }
        
        return true;
    }
};

// 结果可视化
const ResultsVisualization = {
    // 创建结果表格
    createResultsTable: function(data, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let tableHtml = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>站点ID</th>
                            <th>实际观测值</th>
                            <th>模型预测值</th>
                            <th>绝对误差</th>
                            <th>相对误差</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        data.forEach(item => {
            tableHtml += `
                <tr>
                    <td>${item.station_id}</td>
                    <td>${Utils.formatNumber(item.observed, 1)} 微克/立方米</td>
                    <td>${Utils.formatNumber(item.predicted, 1)} 微克/立方米</td>
                    <td>${Utils.formatNumber(item.absolute_error, 1)} 微克/立方米</td>
                    <td>${Utils.formatNumber(item.relative_error, 1)}%</td>
                </tr>
            `;
        });
        
        tableHtml += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHtml;
    },
    
    // 创建统计信息卡片
    createStatsCard: function(stats, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const cardHtml = `
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0"><i class="fas fa-chart-line"></i> 验证统计</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>平均绝对误差：</strong><br>
                               <span class="h5 text-primary">${Utils.formatNumber(stats.mean_absolute_error)} 微克/立方米</span></p>
                            <p><strong>最大绝对误差：</strong><br>
                               <span class="h5 text-warning">${Utils.formatNumber(stats.max_absolute_error)} 微克/立方米</span></p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>均方根误差：</strong><br>
                               <span class="h5 text-info">${Utils.formatNumber(stats.rmse)} 微克/立方米</span></p>
                            <p><strong>相关系数：</strong><br>
                               <span class="h5 text-success">${Utils.formatNumber(stats.correlation, 3)}</span></p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = cardHtml;
    }
};

// 导出全局对象
window.Utils = Utils;
window.FileUpload = FileUpload;
window.DataProcessor = DataProcessor;
window.ResultsVisualization = ResultsVisualization;
