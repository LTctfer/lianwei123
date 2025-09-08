# 预警规则API功能实现说明

## 概述
本次修改为RTO/RCO预警系统添加了完整的API接口功能，支持通过REST API动态修改预警规则的阈值和状态，无需重启系统即可生效。

## 主要功能

### 1. 规则配置持久化
- 规则配置自动保存到 `warning_rules.json` 文件
- 系统启动时自动加载保存的配置
- 支持动态修改并实时保存

### 2. REST API接口
- **GET** `/api/rules` - 获取所有规则列表
- **GET** `/api/rules/{rule_id}` - 获取单个规则详情
- **POST** `/api/rules/update-threshold` - 更新规则阈值
- **POST** `/api/rules/toggle-status` - 切换规则启用/禁用状态
- **PUT** `/api/rules/{rule_id}` - 更新规则完整信息

### 3. 前端管理界面
- 在监控大屏中新增"规则管理"模块
- 可视化显示所有规则信息
- 支持在线修改阈值和切换状态
- 实时更新规则配置

## 代码修改详情

### 1. WarningRuleEngine类增强
```python
# 新增方法：
- _load_rules_from_file()      # 从文件加载规则
- _save_rules_to_file()        # 保存规则到文件
- update_rule_threshold()      # 更新规则阈值
- toggle_rule_status()         # 切换规则状态
- get_all_rules()              # 获取所有规则
- get_rule_by_id()             # 根据ID获取规则
```

### 2. HTTP服务器增强
```python
# 新增API处理方法：
- send_rules_list()            # 发送规则列表
- send_rule_detail()           # 发送规则详情
- update_rule_threshold()      # 处理阈值更新请求
- toggle_rule_status()         # 处理状态切换请求
- update_rule()                # 处理规则更新请求
```

### 3. 前端界面增强
```javascript
// 新增JavaScript函数：
- updateRulesDetail()          # 更新规则详情显示
- displayRules()               # 显示规则列表
- updateRuleThreshold()        # 更新规则阈值
- toggleRuleStatus()           # 切换规则状态
```

## 使用方法

### 1. 启动系统
```bash
python warning_system.py
# 选择模式 2 (启动实时监控大屏)
```

### 2. 访问管理界面
- 浏览器访问: `http://localhost:8090`
- 点击"规则管理"模块
- 在线修改规则阈值和状态

### 3. 使用API接口
```python
import requests

# 获取所有规则
response = requests.get('http://localhost:8090/api/rules')
rules = response.json()

# 更新规则阈值
update_data = {"rule_id": "R001", "threshold": 780}
response = requests.post(
    'http://localhost:8090/api/rules/update-threshold',
    json=update_data
)
```

### 4. 运行测试
```bash
python test_api.py
```

## 技术特点

### 1. 实时生效
- 规则修改后立即生效，无需重启系统
- 支持热更新，不影响系统运行

### 2. 数据持久化
- 所有配置自动保存到JSON文件
- 系统重启后自动恢复配置

### 3. 错误处理
- 完善的错误处理机制
- 统一的API响应格式
- 详细的错误信息提示

### 4. 用户友好
- 直观的前端管理界面
- 实时反馈操作结果
- 支持批量操作

## 文件结构

```
RTO/RCO/
├── warning_system.py          # 主程序文件（已修改）
├── warning_rules.json         # 规则配置文件（自动生成）
├── API使用说明.md             # API使用文档
├── test_api.py               # API测试脚本
└── 预警规则API功能说明.md     # 功能说明文档
```

## 安全考虑

1. **输入验证**: 所有API输入都进行严格验证
2. **错误处理**: 完善的异常处理，避免系统崩溃
3. **数据备份**: 规则配置自动保存，防止数据丢失
4. **权限控制**: 可根据需要添加用户认证机制

## 扩展性

1. **规则类型**: 可轻松添加新的规则类型
2. **API接口**: 可扩展更多管理功能
3. **前端界面**: 可添加更多可视化功能
4. **集成能力**: 支持与其他系统集成

## 注意事项

1. 确保服务器正常运行后再进行API调用
2. 修改规则前建议备份原始配置
3. 阈值修改应符合实际工艺要求
4. 定期检查规则配置的有效性

## 总结

本次修改成功实现了预警规则的动态管理功能，提供了完整的API接口和用户友好的管理界面。系统现在支持：

- ✅ 动态修改预警规则阈值
- ✅ 实时启用/禁用规则
- ✅ 规则配置持久化存储
- ✅ 完整的REST API接口
- ✅ 直观的前端管理界面
- ✅ 完善的错误处理机制

这些功能大大提升了系统的灵活性和可维护性，使得预警规则的管理更加便捷和高效。
