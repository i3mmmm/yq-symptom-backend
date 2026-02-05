# 医疗症状收集与分析系统 - 后端服务

## 概述
基于Flask的医疗症状收集与分析系统后端API服务，提供客户管理、症状提交、智能整理、对比分析和PDF报告导出等功能。

## 功能特性
- **管理员认证**: JWT token认证，支持登录、刷新、登出
- **客户管理**: 客户CRUD操作，支持分页搜索筛选
- **症状提交**: 前端症状勾选提交，包含性别验证逻辑（男性禁用妇科症状）
- **症状管理**: 症状列表查询，按区域筛选
- **智能整理**: 症状分析报告生成（开发中）
- **对比分析**: 两次记录对比功能（开发中）
- **PDF报告**: 健康报告导出功能（开发中）

## 技术栈
- **框架**: Flask 2.3.3
- **数据库**: SQLite 3.35+
- **ORM**: Flask-SQLAlchemy 3.0.5
- **认证**: Flask-JWT-Extended 4.5.2
- **CORS**: Flask-CORS 4.0.0

## 项目结构
```
app/
├── __init__.py
├── app.py              # 应用入口
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── routes/             # API路由
│   ├── __init__.py
│   ├── auth.py         # 认证相关
│   ├── customers.py    # 客户管理
│   ├── records.py      # 症状记录
│   ├── symptoms.py     # 症状查询
│   ├── analysis.py     # 智能整理（开发中）
│   ├── compare.py      # 对比分析（开发中）
│   ├── reports.py      # PDF报告（开发中）
│   └── admin.py        # 系统管理（开发中）
├── requirements.txt    # 依赖列表
└── README.md           # 说明文档
scripts/
├── init_database.py    # 数据库初始化脚本
tests/
└── test_api.py         # API测试用例
```

## 快速开始

### 1. 环境准备
确保已安装Python 3.8+和pip。

### 2. 安装依赖
```bash
cd app
pip install -r requirements.txt
```

### 3. 初始化数据库
```bash
# 使用默认配置（开发环境）
python scripts/init_database.py

# 或指定配置环境
python scripts/init_database.py development  # 开发环境
python scripts/init_database.py production   # 生产环境
```

### 4. 启动服务
```bash
# 开发环境
python app/app.py

# 生产环境
python app/app.py production
```

服务默认运行在 `http://localhost:5000`

## API文档

### 基础信息
- **基础URL**: `http://localhost:5000/api/v1/`
- **数据格式**: JSON
- **认证方式**: JWT Bearer Token

### 主要接口

#### 1. 管理员认证
- `POST /auth/login` - 管理员登录
- `POST /auth/refresh` - 刷新token
- `POST /auth/logout` - 登出
- `GET /auth/me` - 获取当前管理员信息

**默认管理员账户**:
- 用户名: `931`
- 密码: `z123456`

#### 2. 客户管理
- `POST /customers` - 创建客户（前端症状提交接口）
- `GET /customers` - 获取客户列表（支持分页、搜索、筛选）
- `GET /customers/{id}` - 获取客户详情
- `PUT /customers/{id}` - 更新客户信息
- `DELETE /customers/{id}` - 删除客户（级联删除相关记录）

#### 3. 症状管理
- `GET /symptoms` - 获取所有症状列表（前端症状勾选页面使用）
- `GET /symptoms/{id}` - 获取单个症状详情

#### 4. 症状记录
- `POST /records` - 提交症状记录（前端用户使用）
- `GET /records/{id}` - 获取记录详情（管理员使用）
- `DELETE /records/{id}` - 删除记录（管理员使用）

### 请求示例

#### 管理员登录
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"931","password":"z123456"}'
```

#### 提交症状记录
```bash
curl -X POST http://localhost:5000/api/v1/records \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "gender": "male",
    "age": 35,
    "contact": "13800138000",
    "selected_symptoms": [1, 5, 23, 56, 110],
    "note": "最近一周感觉疲劳"
  }'
```

#### 获取客户列表（需要认证）
```bash
curl -X GET http://localhost:5000/api/v1/customers \
  -H "Authorization: Bearer <your_jwt_token>"
```

## 配置说明

### 配置文件位置
`app/config.py`

### 环境配置
- **development**: 开发环境，启用调试模式
- **testing**: 测试环境，使用测试数据库
- **production**: 生产环境，使用持久化存储路径

### 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_PATH | 数据库文件路径 | health_system.db |
| JWT_SECRET_KEY | JWT加密密钥 | 开发环境默认值 |
| ENCRYPTION_KEY | 数据加密密钥 | 开发环境默认值 |
| BACKUP_PATH | 备份文件路径 | backups |

## 测试

### 运行测试用例
```bash
cd app
pytest tests/test_api.py -v
```

### 测试覆盖功能
1. 健康检查端点
2. 管理员登录认证
3. 客户创建与症状提交
4. 性别验证逻辑（男性禁用妇科症状）
5. 客户列表查询
6. 客户详情查看

## 部署到Zeabur

### 准备工作
1. 在Zeabur.com创建新项目
2. 选择Python运行环境

### 部署步骤
1. **上传代码**: 将整个项目上传到Zeabur的Git仓库
2. **配置环境变量**:
   ```
   DATABASE_PATH=/data/health_system.db
   JWT_SECRET_KEY=<your_secure_jwt_secret>
   ENCRYPTION_KEY=<32_bytes_secure_key>
   ```
3. **安装依赖**: Zeabur会自动执行 `pip install -r requirements.txt`
4. **初始化数据库**: 通过Zeabur的终端执行初始化脚本
5. **启动服务**: Zeabur会自动启动 `python app/app.py production`

### 持久化存储
- Zeabur的 `/data` 目录提供持久化存储
- 将数据库文件存储在 `/data` 目录下
- 备份文件也应存储在 `/data/backups` 目录

## 开发指南

### 数据库模型修改
1. 修改 `app/models.py` 中的模型定义
2. 运行数据库迁移或重新初始化

### 添加新API
1. 在 `app/routes/` 目录下创建新的路由文件
2. 在 `app/app.py` 中注册蓝图
3. 编写相应的业务逻辑

### 错误处理
所有API都遵循统一的错误响应格式：
```json
{
  "code": 400,
  "message": "错误描述",
  "data": null,
  "timestamp": "2026-02-05T10:30:00Z"
}
```

## 注意事项

### 性别验证逻辑
- 男性用户不能选择症状ID 260-300（妇科症状）
- 验证在症状提交接口自动执行

### 数据安全
- 客户联系方式建议加密存储
- 管理员密码使用bcrypt哈希存储
- 生产环境务必更换默认密钥

### 性能优化
- 大量数据查询时使用分页
- 频繁查询的字段建立索引
- 考虑使用数据库连接池

## 故障排除

### 常见问题
1. **数据库连接失败**: 检查文件权限和路径
2. **JWT认证失败**: 验证token有效期和密钥
3. **CORS错误**: 检查前端请求头设置
4. **API响应慢**: 检查数据库索引和查询优化

### 日志查看
- 应用日志输出到控制台
- 详细日志可配置输出到文件

## 版本历史
- v1.0.0 (2026-02-05): 初始版本，包含核心API功能

## 许可证
版权所有 © 2026 医疗症状收集与分析系统开发团队