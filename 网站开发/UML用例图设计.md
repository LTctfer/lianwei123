# UML用例图设计文档

## 1. 系统整体用例图

```plantuml
@startuml 系统整体用例图
left to right direction

actor "访客" as Guest
actor "注册用户" as User
actor "管理员" as Admin
actor "支付系统" as PaymentSystem

rectangle "网站系统" {
  usecase "浏览产品" as UC1
  usecase "搜索产品" as UC2
  usecase "用户注册" as UC3
  usecase "用户登录" as UC4
  usecase "添加购物车" as UC5
  usecase "下单购买" as UC6
  usecase "支付订单" as UC7
  usecase "查看订单" as UC8
  usecase "发表评论" as UC9
  usecase "参与社区" as UC10
  usecase "管理用户" as UC11
  usecase "管理产品" as UC12
  usecase "管理订单" as UC13
  usecase "内容管理" as UC14
  usecase "数据分析" as UC15
}

Guest --> UC1
Guest --> UC2
Guest --> UC3
Guest --> UC4

User --> UC1
User --> UC2
User --> UC5
User --> UC6
User --> UC7
User --> UC8
User --> UC9
User --> UC10

Admin --> UC11
Admin --> UC12
Admin --> UC13
Admin --> UC14
Admin --> UC15

PaymentSystem --> UC7

UC6 ..> UC5 : <<include>>
UC7 ..> UC6 : <<include>>
UC9 ..> UC4 : <<include>>
UC10 ..> UC4 : <<include>>

@enduml
```

## 2. 用户认证系统用例图

```plantuml
@startuml 用户认证系统
left to right direction

actor "访客" as Guest
actor "注册用户" as User
actor "邮件系统" as EmailSystem

rectangle "用户认证系统" {
  usecase "用户注册" as Register
  usecase "邮箱验证" as EmailVerify
  usecase "用户登录" as Login
  usecase "忘记密码" as ForgotPassword
  usecase "重置密码" as ResetPassword
  usecase "修改密码" as ChangePassword
  usecase "退出登录" as Logout
  usecase "查看个人信息" as ViewProfile
  usecase "修改个人信息" as EditProfile
}

Guest --> Register
Guest --> Login
Guest --> ForgotPassword

User --> Login
User --> ChangePassword
User --> Logout
User --> ViewProfile
User --> EditProfile

EmailSystem --> EmailVerify
EmailSystem --> ResetPassword

Register ..> EmailVerify : <<include>>
ForgotPassword ..> ResetPassword : <<include>>
EditProfile ..> Login : <<include>>

@enduml
```

## 3. 电商购物系统用例图

```plantuml
@startuml 电商购物系统
left to right direction

actor "用户" as User
actor "支付系统" as PaymentSystem
actor "物流系统" as LogisticsSystem

rectangle "电商购物系统" {
  usecase "浏览产品目录" as BrowseProducts
  usecase "搜索产品" as SearchProducts
  usecase "查看产品详情" as ViewProductDetail
  usecase "添加到购物车" as AddToCart
  usecase "管理购物车" as ManageCart
  usecase "创建订单" as CreateOrder
  usecase "选择支付方式" as SelectPayment
  usecase "支付订单" as PayOrder
  usecase "查看订单状态" as ViewOrderStatus
  usecase "申请退款" as RequestRefund
  usecase "确认收货" as ConfirmDelivery
}

User --> BrowseProducts
User --> SearchProducts
User --> ViewProductDetail
User --> AddToCart
User --> ManageCart
User --> CreateOrder
User --> SelectPayment
User --> ViewOrderStatus
User --> RequestRefund
User --> ConfirmDelivery

PaymentSystem --> PayOrder
LogisticsSystem --> ViewOrderStatus

CreateOrder ..> ManageCart : <<include>>
PayOrder ..> SelectPayment : <<include>>
ViewOrderStatus ..> CreateOrder : <<include>>

@enduml
```

## 4. 内容管理系统用例图

```plantuml
@startuml 内容管理系统
left to right direction

actor "管理员" as Admin
actor "编辑" as Editor
actor "用户" as User

rectangle "内容管理系统" {
  usecase "创建文章" as CreateArticle
  usecase "编辑文章" as EditArticle
  usecase "发布文章" as PublishArticle
  usecase "删除文章" as DeleteArticle
  usecase "管理分类" as ManageCategory
  usecase "管理标签" as ManageTag
  usecase "上传媒体文件" as UploadMedia
  usecase "管理媒体库" as ManageMedia
  usecase "设置SEO" as SetSEO
  usecase "审核内容" as ReviewContent
  usecase "查看文章" as ViewArticle
  usecase "搜索文章" as SearchArticle
}

Admin --> CreateArticle
Admin --> EditArticle
Admin --> PublishArticle
Admin --> DeleteArticle
Admin --> ManageCategory
Admin --> ManageTag
Admin --> UploadMedia
Admin --> ManageMedia
Admin --> SetSEO
Admin --> ReviewContent

Editor --> CreateArticle
Editor --> EditArticle
Editor --> UploadMedia

User --> ViewArticle
User --> SearchArticle

PublishArticle ..> ReviewContent : <<include>>
CreateArticle ..> UploadMedia : <<extend>>
EditArticle ..> UploadMedia : <<extend>>

@enduml
```

## 5. 用户社区系统用例图

```plantuml
@startuml 用户社区系统
left to right direction

actor "用户" as User
actor "版主" as Moderator
actor "管理员" as Admin

rectangle "用户社区系统" {
  usecase "发表帖子" as CreatePost
  usecase "回复帖子" as ReplyPost
  usecase "点赞/点踩" as VotePost
  usecase "收藏帖子" as BookmarkPost
  usecase "举报内容" as ReportContent
  usecase "搜索帖子" as SearchPost
  usecase "关注用户" as FollowUser
  usecase "私信用户" as SendMessage
  usecase "管理帖子" as ManagePost
  usecase "处理举报" as HandleReport
  usecase "封禁用户" as BanUser
}

User --> CreatePost
User --> ReplyPost
User --> VotePost
User --> BookmarkPost
User --> ReportContent
User --> SearchPost
User --> FollowUser
User --> SendMessage

Moderator --> ManagePost
Moderator --> HandleReport

Admin --> ManagePost
Admin --> HandleReport
Admin --> BanUser

HandleReport ..> ReportContent : <<include>>
ManagePost ..> CreatePost : <<extend>>

@enduml
```

## 6. 数据分析系统用例图

```plantuml
@startuml 数据分析系统
left to right direction

actor "管理员" as Admin
actor "数据分析师" as Analyst
actor "系统" as System

rectangle "数据分析系统" {
  usecase "收集用户行为数据" as CollectUserData
  usecase "收集销售数据" as CollectSalesData
  usecase "收集系统性能数据" as CollectSystemData
  usecase "生成用户分析报告" as GenerateUserReport
  usecase "生成销售分析报告" as GenerateSalesReport
  usecase "生成系统性能报告" as GenerateSystemReport
  usecase "创建自定义仪表板" as CreateDashboard
  usecase "设置数据告警" as SetAlert
  usecase "导出分析数据" as ExportData
  usecase "查看实时数据" as ViewRealTimeData
}

Admin --> GenerateUserReport
Admin --> GenerateSalesReport
Admin --> GenerateSystemReport
Admin --> CreateDashboard
Admin --> SetAlert
Admin --> ViewRealTimeData

Analyst --> GenerateUserReport
Analyst --> GenerateSalesReport
Analyst --> CreateDashboard
Analyst --> ExportData

System --> CollectUserData
System --> CollectSalesData
System --> CollectSystemData

GenerateUserReport ..> CollectUserData : <<include>>
GenerateSalesReport ..> CollectSalesData : <<include>>
GenerateSystemReport ..> CollectSystemData : <<include>>

@enduml
```

## 7. 用例详细描述

### 7.1 用户注册用例

**用例名称**: 用户注册
**参与者**: 访客、邮件系统
**前置条件**: 用户未注册账号
**后置条件**: 用户成功注册并激活账号

**主要流程**:
1. 访客点击注册按钮
2. 系统显示注册表单
3. 访客填写注册信息（用户名、邮箱、密码等）
4. 系统验证信息格式和唯一性
5. 系统发送验证邮件
6. 用户点击邮件中的验证链接
7. 系统激活用户账号
8. 注册完成

**异常流程**:
- 用户名或邮箱已存在：提示用户修改
- 密码强度不够：提示密码要求
- 邮件发送失败：提供重新发送选项
- 验证链接过期：提供重新发送验证邮件

### 7.2 产品搜索用例

**用例名称**: 产品搜索
**参与者**: 用户（访客或注册用户）
**前置条件**: 系统中存在产品数据
**后置条件**: 显示搜索结果

**主要流程**:
1. 用户在搜索框输入关键词
2. 用户选择搜索条件（分类、价格范围等）
3. 用户点击搜索按钮
4. 系统执行搜索算法
5. 系统返回匹配的产品列表
6. 用户可以进一步筛选和排序结果

**异常流程**:
- 搜索无结果：显示"未找到相关产品"
- 搜索关键词为空：提示输入搜索内容
- 系统响应超时：显示错误信息并建议重试

### 7.3 订单支付用例

**用例名称**: 订单支付
**参与者**: 注册用户、支付系统
**前置条件**: 用户已创建订单
**后置条件**: 订单支付完成或失败

**主要流程**:
1. 用户选择支付方式
2. 系统生成支付订单
3. 跳转到第三方支付页面
4. 用户完成支付操作
5. 支付系统返回支付结果
6. 系统更新订单状态
7. 发送支付确认通知

**异常流程**:
- 支付失败：显示失败原因，提供重新支付选项
- 支付超时：取消支付，恢复库存
- 网络异常：提示网络错误，建议稍后重试
- 余额不足：提示充值或更换支付方式

## 8. 用例关系说明

### 8.1 包含关系 (Include)
- 下单购买包含添加购物车
- 支付订单包含创建订单
- 发表评论包含用户登录

### 8.2 扩展关系 (Extend)
- 创建文章可扩展上传媒体文件
- 编辑文章可扩展上传媒体文件
- 管理帖子可扩展创建帖子

### 8.3 泛化关系 (Generalization)
- 管理员和编辑都是内容管理者
- 访客和注册用户都是系统用户

## 9. 用例优先级

### 9.1 高优先级用例
1. 用户注册/登录
2. 产品浏览/搜索
3. 购物车管理
4. 订单创建/支付
5. 基础内容管理

### 9.2 中优先级用例
1. 用户评论系统
2. 社区功能
3. 高级搜索功能
4. 数据分析基础功能

### 9.3 低优先级用例
1. 高级数据分析
2. 复杂的社区管理
3. 个性化推荐系统
4. 多语言支持
5. 第三方集成功能

## 10. 用例实现建议

### 10.1 开发阶段划分
**第一阶段（核心功能）**
- 用户认证系统
- 产品展示和搜索
- 购物车和订单管理
- 基础支付功能

**第二阶段（扩展功能）**
- 用户评论和社区
- 内容管理系统
- 基础数据分析

**第三阶段（高级功能）**
- 高级数据分析和可视化
- 个性化推荐
- 移动端适配

### 10.2 测试用例设计
每个用例都需要对应的测试用例，包括：
- 正常流程测试
- 异常流程测试
- 边界条件测试
- 性能压力测试

### 10.3 用例追踪矩阵
建立用例与需求、设计、代码、测试之间的追踪关系，确保需求完整实现。
