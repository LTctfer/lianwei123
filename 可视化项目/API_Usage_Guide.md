# 吸附曲线预警系统 HTTP API 使用指南

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动API服务
```bash
cd 可视化项目
python adsorption_http_api.py
```
服务将在 `http://localhost:5000` 启动

### 3. 测试API
```bash
# 健康检查
curl http://localhost:5000/api/health

# 查看API信息
curl http://localhost:5000/
```

## API接口详细说明

### 基础信息
- **服务地址**: `http://localhost:5000`
- **支持格式**: CSV, XLSX, XLS
- **最大文件**: 16MB
- **响应格式**: JSON

### 接口列表

#### 1. GET `/` - API信息
获取API基本信息和接口列表

**响应示例**:
```json
{
  "message": "吸附曲线预警系统 HTTP API",
  "version": "1.0.0",
  "endpoints": {...},
  "supported_formats": ["CSV", "XLSX", "XLS"]
}
```

#### 2. GET `/api/health` - 健康检查
检查API服务状态

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "service": "吸附曲线预警系统"
}
```

#### 3. POST `/api/analyze/warning` - 预警系统分析（推荐）
上传文件进行预警系统分析，返回绘图数据点和预警点信息

**请求**:
- Content-Type: `multipart/form-data`
- 参数: `file` (文件)

**curl示例**:
```bash
curl -X POST \
  -F "file=@7.24.csv" \
  http://localhost:5000/api/analyze/warning
```

**Python示例**:
```python
import requests

with open('7.24.csv', 'rb') as f:
    files = {'file': ('7.24.csv', f)}
    response = requests.post('http://localhost:5000/api/analyze/warning', files=files)
    result = response.json()
```

**响应示例**:
```json
{
  "success": true,
  "data_points": [
    {
      "x": 0.5,
      "y": 12.3,
      "label": "t=0.50h: 进口=1.23, 出口=0.15, 穿透率=12.3%, 效率=87.7%"
    }
  ],
  "warning_point": {
    "time": 5.75,
    "breakthrough_rate": 80.1,
    "description": "预警点(穿透率: 80.1%)"
  },
  "statistics": {
    "total_data_points": 36,
    "has_warning_point": true,
    "time_range": {"min": 0.0, "max": 12.0},
    "breakthrough_range": {"min": 3.2, "max": 85.4}
  },
  "timestamp": "2025-01-01T12:00:00"
}
```

#### 4. POST `/api/analyze/complete` - 完整数据分析
上传文件进行完整数据分析，返回所有数据点和预警点信息

**请求格式**: 同预警系统分析接口

**响应示例**:
```json
{
  "success": true,
  "all_data_points": [
    {
      "x": 0.5,
      "y": 12.3,
      "label": "t=0.50h: 进口=1.23, 出口=0.15, 穿透率=12.3%, 效率=87.7%",
      "type": "时间段穿透率",
      "data_category": "breakthrough"
    }
  ],
  "warning_points": [
    {
      "x": 5.75,
      "y": 80.1,
      "warning_level": "预警点",
      "reason": "预警点(穿透率: 80.1%)",
      "recommendation": "超过预警点，请关注更换周期",
      "color_code": "#FFA500"
    }
  ],
  "statistics": {...},
  "data_summary": {
    "total_points": 36,
    "warning_count": 1,
    "data_types": ["时间段穿透率"],
    "time_range": {"min": 0.0, "max": 12.0}
  },
  "timestamp": "2025-01-01T12:00:00"
}
```

#### 5. POST `/api/analyze/file` - 文件路径分析
通过服务器端文件路径进行分析（无需上传）

**请求**:
- Content-Type: `application/json`
- 参数:
  ```json
  {
    "file_path": "path/to/data/file.csv",
    "analysis_type": "warning"  // 可选: "warning" 或 "complete"
  }
  ```

**curl示例**:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"file_path": "可视化项目/7.24.csv", "analysis_type": "warning"}' \
  http://localhost:5000/api/analyze/file
```

## 错误处理

### 常见错误码
- **400**: 请求参数错误
- **413**: 文件过大（超过16MB）
- **404**: 接口不存在
- **500**: 服务器内部错误

### 错误响应格式
```json
{
  "success": false,
  "error": "错误描述",
  "timestamp": "2025-01-01T12:00:00"
}
```

## Python客户端使用

### 安装依赖
```bash
pip install requests
```

### 使用示例
```python
from example_client import AdsorptionAPIClient

# 创建客户端
client = AdsorptionAPIClient("http://localhost:5000")

# 健康检查
health = client.health_check()
print(health)

# 文件上传分析
result = client.analyze_warning_upload("data.csv")
if result['success']:
    print(f"数据点数量: {len(result['data_points'])}")
    print(f"预警点: {result['warning_point']}")
else:
    print(f"分析失败: {result['error']}")

# 服务器端文件分析
result = client.analyze_file_path("/path/to/server/file.csv", "warning")
```

## JavaScript/前端调用示例

### 文件上传
```javascript
async function analyzeFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('http://localhost:5000/api/analyze/warning', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('数据点:', result.data_points);
            console.log('预警点:', result.warning_point);
            console.log('统计:', result.statistics);
        } else {
            console.error('分析失败:', result.error);
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
}
```

### JSON请求
```javascript
async function analyzeFilePath(filePath) {
    try {
        const response = await fetch('http://localhost:5000/api/analyze/file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath,
                analysis_type: 'warning'
            })
        });
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('请求失败:', error);
        return { success: false, error: error.message };
    }
}
```

## 部署说明

### 开发环境
```bash
python adsorption_http_api.py
```

### 生产环境（使用Gunicorn）
```bash
# 安装gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 adsorption_http_api:app
```

### Docker部署
```dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "adsorption_http_api:app"]
```

## 注意事项

1. **文件安全**: 上传的文件会临时保存并在处理完成后自动删除
2. **内存管理**: 大文件处理可能消耗较多内存，建议监控服务器资源
3. **并发处理**: 当前版本支持多用户并发访问
4. **数据格式**: 确保上传的数据文件包含必要的列（时间、进口浓度、出口浓度等）
5. **网络超时**: 大文件分析可能需要较长时间，建议设置合适的超时时间

## 故障排除

### 常见问题
1. **连接拒绝**: 确保API服务已启动
2. **文件格式错误**: 检查文件扩展名和内容格式
3. **分析失败**: 检查数据文件是否包含必要列
4. **内存不足**: 减小文件大小或增加服务器内存

### 日志查看
API服务会在控制台输出详细的处理日志，可用于调试问题。
