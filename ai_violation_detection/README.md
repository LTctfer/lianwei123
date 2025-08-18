# AI违规行为识别系统

## 🎯 项目概述

基于深度学习的智能违规行为识别系统，能够实时检测和识别多种违规行为，包括工地监控、环境保护、安全管理等场景。

### 🏗️ 工地违规行为
- 🌪️ 工地扬尘检测
- 🏔️ 裸土未覆盖识别
- 💧 土方作业未降尘检测
- 🌙 夜间违规施工监控

### 🌍 环境污染事件
- 🔥 露天烧烤识别
- 🔥 垃圾焚烧检测
- 🚛 渣土车未覆盖识别

### 🛡️ 安全管理
- ⛑️ 未戴安全帽检测
- ⚠️ 不安全操作识别
- 🚫 禁入区域监控

## 🚀 功能特点

- **实时检测**: 支持图片和视频流实时分析
- **高精度识别**: 基于YOLO v8和自定义训练模型
- **智能报警**: 自动检测违规行为并生成多级别报警
- **可视化结果**: 框选违规区域，显示置信度和详细信息
- **Web界面**: 现代化、响应式的Web操作界面
- **报警管理**: 完整的报警记录、统计和通知系统

## 📁 项目结构

```
ai_violation_detection/
├── models/                 # AI模型文件
│   ├── yolo_violation.py   # YOLO违规检测模型
│   ├── dust_detector.py    # 扬尘检测专用模型
│   └── weights/            # 自定义训练权重文件
├── yolo-model/             # YOLO预训练模型目录
│   ├── yolov8n.pt         # YOLOv8 Nano模型
│   └── yolov8s.pt         # YOLOv8 Small模型
├── web/                    # Web应用
│   ├── app.py             # Flask主应用
│   ├── static/            # 静态资源(CSS/JS/图片)
│   └── templates/         # HTML模板文件
├── utils/                  # 工具函数
│   ├── image_processor.py  # 图像处理工具
│   └── alert_system.py     # 智能报警系统
├── data/                   # 数据和配置
│   ├── classes.yaml        # 检测类别配置
│   ├── config.py          # 系统配置文件
│   └── alerts.db          # 报警数据库
├── logs/                   # 日志文件
├── run.py                  # 主启动脚本
├── install.py              # 自动安装脚本
└── README.md              # 项目说明文档
```

## 🛠️ 技术栈

- **AI框架**: PyTorch 2.0+, Ultralytics YOLO v8
- **Web框架**: Flask 2.0+, Bootstrap 5
- **图像处理**: OpenCV 4.5+, PIL/Pillow
- **前端技术**: HTML5, CSS3, JavaScript (ES6+)
- **数据库**: SQLite (支持扩展到PostgreSQL/MySQL)
- **部署**: 支持Docker容器化部署

## 📦 系统要求

### 最低要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8 或更高版本
- **内存**: 4GB RAM (推荐 8GB+)
- **存储**: 2GB 可用空间
- **网络**: 用于下载模型和依赖包

### 推荐配置
- **CPU**: Intel i5/AMD Ryzen 5 或更高
- **GPU**: NVIDIA GTX 1060 或更高 (支持CUDA)
- **内存**: 16GB RAM
- **存储**: SSD 硬盘

## 🚀 快速安装

### 方法一：自动安装（推荐）

1. **下载项目**
   ```bash
   git clone https://github.com/your-repo/ai_violation_detection.git
   cd ai_violation_detection
   ```

2. **运行自动安装脚本**
   ```bash
   python install.py
   ```

   安装脚本会自动：
   - 检查Python版本和系统环境
   - 安装所有必需的依赖包
   - 下载预训练模型
   - 创建必要的目录结构
   - 生成配置文件

3. **启动系统**
   ```bash
   # 推荐方式：自动检查和下载模型
   python start.py

   # 或者使用完整启动脚本
   python run.py --mode web
   ```

   或者直接运行启动脚本：
   - Windows: 双击 `start.bat`
   - Linux/Mac: `./start.sh`

### 方法二：手动安装

1. **安装Python依赖**
   ```bash
   pip install torch torchvision ultralytics opencv-python flask pillow numpy requests pyyaml matplotlib seaborn
   ```

2. **创建目录结构**
   ```bash
   mkdir -p data models/weights web/static/{uploads,results} logs
   ```

3. **下载预训练模型**
   ```bash
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
   ```

4. **启动系统**
   ```bash
   python run.py --mode web
   ```

## 🎮 使用指南

### 1. 启动系统

访问 `http://localhost:5000` 打开Web界面

### 2. 图像检测

#### 上传图片检测
1. 在主页点击"选择图片"或直接拖拽图片到上传区域
2. 调整检测参数：
   - **置信度阈值**: 0.1-0.9 (默认0.5)
   - **扬尘专项检测**: 启用/禁用
3. 点击"开始检测"按钮
4. 查看检测结果：
   - 原图与结果图对比
   - 违规行为列表和置信度
   - 生成的报警信息
   - 处理时间统计

#### 实时摄像头检测
1. 点击"启动摄像头"按钮
2. 允许浏览器访问摄像头
3. 系统会每3秒自动检测一次
4. 点击"拍照检测"进行单次详细检测
5. 点击"停止检测"结束实时监控

### 3. 报警管理

访问 `/alerts` 页面查看和管理报警：
- 查看所有报警记录
- 按状态筛选报警
- 更新报警处理状态
- 查看报警详细信息

### 4. 统计分析

访问 `/statistics` 页面查看统计数据：
- 违规行为趋势图
- 报警级别分布
- 每日统计数据
- 处理效率分析

## ⚙️ 配置说明

### 基础配置

编辑 `data/config.py` 文件进行系统配置：

```python
# 模型配置
MODEL_CONFIG = {
    'confidence_threshold': 0.5,  # 检测置信度阈值
    'iou_threshold': 0.45,        # NMS IoU阈值
    'device': 'auto'              # 'cpu', 'cuda', 'auto'
}

# Web应用配置
WEB_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}
```

### 环境变量配置

复制 `.env.example` 为 `.env` 并修改：

```bash
# Web服务配置
WEB_HOST=0.0.0.0
WEB_PORT=5000
SECRET_KEY=your-secret-key-change-in-production

# 邮件通知配置
EMAIL_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# 模型配置
MODEL_CONFIDENCE=0.5
DUST_DETECTION_ENABLED=true
```

### 报警通知配置

#### 邮件通知
```python
NOTIFICATION_CONFIG = {
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your-email@gmail.com',
        'password': 'your-app-password',
        'recipients': ['admin@company.com']
    }
}
```

#### Webhook通知
```python
NOTIFICATION_CONFIG = {
    'webhook': {
        'enabled': True,
        'url': 'https://your-webhook-url.com/alerts',
        'headers': {'Authorization': 'Bearer your-token'}
    }
}
```

## 📡 API接口文档

### 图像检测接口

**POST** `/upload`

上传图片进行违规检测

**请求参数**:
- `file`: 图片文件 (multipart/form-data)
- `confidence`: 置信度阈值 (0.1-0.9)
- `dust_detection`: 是否启用扬尘检测 (true/false)

**响应示例**:
```json
{
  "success": true,
  "original_image": "/static/uploads/image.jpg",
  "result_image": "/static/results/result_image.jpg",
  "detection_result": {
    "detections": [
      {
        "class_name": "dust_emission",
        "confidence": 0.85,
        "bbox": {"x1": 100, "y1": 50, "x2": 200, "y2": 150},
        "alert_level": "high"
      }
    ],
    "total_violations": 1,
    "processing_time": 1.23
  },
  "alerts": [
    {
      "alert_id": "alert_123456",
      "violation_type": "dust_emission",
      "message": "检测到工地扬尘！置信度: 85.0%",
      "alert_level": "high",
      "timestamp": "2024-01-15 14:30:25"
    }
  ]
}
```

### 实时检测接口

**POST** `/detect_realtime`

实时检测接口（用于摄像头或视频流）

**请求参数**:
```json
{
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
}
```

### 报警管理接口

**GET** `/api/alerts`

获取报警列表

**查询参数**:
- `limit`: 返回数量限制 (默认50)
- `status`: 报警状态筛选 (active/resolved/ignored)

**PUT** `/api/alerts/{alert_id}/status`

更新报警状态

**请求体**:
```json
{
  "status": "resolved"
}
```

### 统计数据接口

**GET** `/api/statistics`

获取统计数据

**查询参数**:
- `days`: 统计天数 (默认7天)

## 🔧 故障排除

### 常见问题

#### 1. 依赖包安装失败

**问题**: `pip install` 时出现错误

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple torch torchvision ultralytics

# 如果是网络问题，可以离线安装
pip install --find-links ./wheels torch torchvision
```

#### 2. CUDA相关错误

**问题**: GPU检测失败或CUDA版本不匹配

**解决方案**:
```bash
# 检查CUDA版本
nvidia-smi

# 安装对应版本的PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 强制使用CPU
export CUDA_VISIBLE_DEVICES=""
```

#### 3. 模型加载失败

**问题**: 无法加载预训练模型

**解决方案**:
```bash
# 检查模型文件是否存在
ls yolo-model/

# 手动下载模型到正确目录
mkdir -p yolo-model
cd yolo-model
wget https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt

# 或者重新运行安装脚本
python install.py

# 使用启动脚本自动检查和下载
python start.py
```

#### 4. 端口占用问题

**问题**: 端口5000已被占用

**解决方案**:
```bash
# 使用其他端口
python run.py --mode web --port 8080

# 或者杀死占用进程
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

#### 5. 摄像头访问失败

**问题**: 无法访问摄像头

**解决方案**:
- 检查浏览器权限设置
- 确保摄像头未被其他应用占用
- 使用HTTPS访问（某些浏览器要求）
- 尝试不同的浏览器

### 性能优化

#### 1. GPU加速
```python
# 在 config.py 中设置
MODEL_CONFIG = {
    'device': 'cuda',  # 强制使用GPU
    'gpu_memory_fraction': 0.8
}
```

#### 2. 批处理优化
```python
PERFORMANCE_CONFIG = {
    'batch_size': 4,  # 增加批处理大小
    'num_workers': 8,  # 增加工作线程
    'cache_enabled': True
}
```

#### 3. 模型优化
```bash
# 使用更小的模型
python run.py --model yolov8n.pt  # nano版本，速度更快

# 使用更大的模型
python run.py --model yolov8x.pt  # extra large版本，精度更高
```

### 日志调试

#### 启用详细日志
```python
# 在 config.py 中设置
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'file_path': 'logs/debug.log'
}
```

#### 查看日志
```bash
# 实时查看日志
tail -f logs/system.log

# 查看错误日志
grep ERROR logs/system.log
```

## 🚀 部署指南

### 开发环境部署

```bash
# 启动开发服务器
python run.py --mode web --debug

# 访问地址
http://localhost:5000
```

### 生产环境部署

#### 使用Gunicorn (推荐)

```bash
# 安装Gunicorn
pip install gunicorn

# 启动生产服务器
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app

# 使用配置文件
gunicorn -c gunicorn.conf.py web.app:app
```

#### 使用Docker

1. **创建Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run.py", "--mode", "web", "--host", "0.0.0.0"]
```

2. **构建和运行**:
```bash
# 构建镜像
docker build -t ai-violation-detection .

# 运行容器
docker run -p 5000:5000 ai-violation-detection
```

#### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /static {
        alias /path/to/ai_violation_detection/web/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 🔨 开发指南

### 项目结构说明

```
ai_violation_detection/
├── models/                 # AI模型模块
│   ├── __init__.py
│   ├── yolo_violation.py   # 主检测模型
│   ├── dust_detector.py    # 扬尘检测模型
│   └── weights/            # 模型权重文件
├── web/                    # Web应用模块
│   ├── __init__.py
│   ├── app.py             # Flask应用主文件
│   ├── static/            # 静态资源
│   │   ├── css/           # 样式文件
│   │   ├── js/            # JavaScript文件
│   │   ├── uploads/       # 上传文件目录
│   │   └── results/       # 结果文件目录
│   └── templates/         # HTML模板
│       ├── base.html      # 基础模板
│       ├── index.html     # 主页
│       ├── alerts.html    # 报警页面
│       └── statistics.html # 统计页面
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── image_processor.py  # 图像处理工具
│   └── alert_system.py     # 报警系统
├── data/                   # 数据和配置
│   ├── config.py          # 系统配置
│   ├── classes.yaml       # 检测类别配置
│   └── alerts.db          # SQLite数据库
└── tests/                  # 测试文件
    ├── test_models.py
    ├── test_web.py
    └── test_utils.py
```

### 添加新的检测类别

1. **更新类别配置** (`data/classes.yaml`):
```yaml
names:
  10: new_violation_type    # 添加新类别

class_details:
  new_violation_type:
    chinese_name: "新违规类型"
    category: "safety"
    priority: "medium"
    description: "新的违规行为描述"
```

2. **更新模型配置** (`data/config.py`):
```python
VIOLATION_CLASSES = {
    10: {
        'name': 'new_violation_type',
        'chinese_name': '新违规类型',
        'category': 'safety',
        'alert_level': 'medium',
        'icon': 'fas fa-exclamation'
    }
}
```

3. **重新训练模型**:
```bash
python run.py --mode train --config data/classes.yaml
```

### 自定义报警规则

编辑 `utils/alert_system.py`:

```python
def _get_alert_level(self, detection):
    """自定义报警级别逻辑"""
    confidence = detection['confidence']
    violation_type = detection['class_name']

    # 自定义规则
    if violation_type == 'garbage_burning':
        return 'critical'  # 垃圾焚烧总是严重报警
    elif confidence > 0.8:
        return 'high'
    elif confidence > 0.6:
        return 'medium'
    else:
        return 'low'
```

### 扩展通知方式

在 `utils/alert_system.py` 中添加新的通知方法：

```python
def _send_sms_notification(self, alert):
    """发送短信通知"""
    # 实现短信发送逻辑
    pass

def _send_wechat_notification(self, alert):
    """发送微信通知"""
    # 实现微信通知逻辑
    pass
```

## 📊 模型训练

### 准备训练数据

1. **数据格式**: YOLO格式
```
datasets/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

2. **标注格式**: 每个图片对应一个txt文件
```
# class_id center_x center_y width height (归一化坐标)
0 0.5 0.5 0.3 0.4
1 0.2 0.3 0.1 0.2
```

### 开始训练

```bash
# 使用默认配置训练
python run.py --mode train

# 使用自定义配置
python run.py --mode train --config custom_config.yaml

# 指定训练参数
python -c "
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.train(
    data='data/classes.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='violation_detection'
)
"
```

### 模型评估

```bash
# 评估模型性能
python run.py --mode eval --model models/weights/best.pt --data data/classes.yaml

# 在测试集上推理
python run.py --mode infer --model models/weights/best.pt --source datasets/test/images
```

## 🤝 贡献指南

### 提交代码

1. Fork项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交Pull Request

### 代码规范

- 使用Python PEP 8编码规范
- 添加适当的注释和文档字符串
- 编写单元测试
- 确保代码通过所有测试

### 报告问题

请在GitHub Issues中报告问题，包含：
- 详细的问题描述
- 复现步骤
- 系统环境信息
- 错误日志

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - 提供优秀的目标检测框架
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [Bootstrap](https://getbootstrap.com/) - 前端UI框架

## 📞 联系我们

- 项目主页: https://github.com/your-repo/ai_violation_detection
- 问题反馈: https://github.com/your-repo/ai_violation_detection/issues
- 邮箱: support@your-domain.com

---

**🎯 开始使用AI违规检测系统，让智能监控为您的安全保驾护航！**
