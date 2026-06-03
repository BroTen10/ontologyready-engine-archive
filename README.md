# OntologyReady

企业级本体管理平台 — 4 张 PostgreSQL 表 + 1 个 REST API + 1 个管理控制台，提供本体建模、图谱可视化、实例管理和行业模板能力。

**一句话定位：** `docker compose up -d`，三容器一键启动。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 数据库 | PostgreSQL 16 + pgvector |
| 后端 | Python 3.12 + FastAPI + asyncpg |
| 前端 | React 19 + TypeScript + Ant Design 6 + React Flow (@xyflow) |
| 部署 | Docker Compose（3 容器） |

---

## 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 API_KEY

# 2. 一键启动（PostgreSQL + API + Console）
docker compose up -d

# 3. 导入行业模板（可选）
curl -X POST http://localhost:8000/api/v1/templates/supply-chain-atp/apply \
  -H "X-API-Key: <your-api-key>"

# 4. 打开浏览器
open http://localhost:3000
```

本地开发：

```bash
# 后端
cd api && pip install -r requirements.txt && uvicorn app.main:app --reload

# 前端
cd console && pnpm install && pnpm dev
```

---

## 项目结构

```
├── api/                        # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口 + 生命周期
│   │   ├── config.py           # pydantic-settings 配置
│   │   ├── database.py         # asyncpg 连接池
│   │   ├── auth.py             # API Key 中间件
│   │   ├── errors.py           # 统一错误响应（RFC 9457）
│   │   ├── schemas.py          # Pydantic 数据模型
│   │   └── routers/
│   │       ├── types.py        # 类型定义 CRUD
│   │       ├── objects.py      # 对象实例 CRUD + 搜索
│   │       ├── links.py        # 链接 CRUD
│   │       ├── graph.py        # 结构图谱 + 实体图谱
│   │       ├── actions.py      # 动作执行 + 历史日志
│   │       ├── templates.py    # 行业模板（列表/详情/导入）
│   │       └── datasets.py     # 数据集管理 + 系统统计
│   └── data/templates/         # 行业模板 JSON
│       ├── supply-chain-atp.json
│       └── crm.json
├── console/                    # React 前端
│   └── src/
│       ├── api/                # API 客户端 + 端点定义
│       ├── layouts/            # MainLayout 布局
│       ├── pages/
│       │   ├── GraphPage.tsx   # 本体图谱（React Flow）
│       │   ├── TypesPage.tsx   # 类型定义管理
│       │   ├── InstancesPage.tsx # 实例管理（3 Tab）
│       │   └── ModelingPage.tsx  # 行业建模（4 步向导）
│       └── hooks/              # useDataset 全局状态
├── init.sql                    # 数据库 DDL（4 张核心表）
├── docker-compose.yml          # 三容器编排
└── .env.example                # 环境变量模板
```

---

## 核心数据模型

四张 PostgreSQL 表，覆盖本体建模 100% 需求：

| 表 | 职责 | 核心字段 |
|----|------|---------|
| `ontology_types` | 类型定义 | api_name PK, type CHECK, config JSONB, maturity |
| `ontology_objects` | 对象实例 | UUID PK, object_type FK, properties JSONB, display_name GENERATED |
| `ontology_links` | 对象间链接 | UUID PK, link_type FK, source_id FK, target_id FK, confidence |
| `ontology_actions_log` | 审计日志 | UUID PK, action_type, status CHECK, before/after_snapshot JSONB |

---

## API 端点

> 在线浏览：启动 API 后访问 <http://localhost:8000/docs>（自动生成 Swagger UI）

### 认证

所有 `/api/v1/*` 端点需 `X-API-Key` 请求头。无 Key 或错误返回 `401`。

### 类型定义

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/types?type=OBJECT` | 类型列表（可过滤 OBJECT/LINK/ACTION） |
| `POST` | `/api/v1/types` | 创建类型 |
| `GET` | `/api/v1/types/:apiName` | 类型详情 |
| `PUT` | `/api/v1/types/:apiName` | 更新类型 |
| `DELETE` | `/api/v1/types/:apiName` | 删除类型（有实例引用时拒绝） |

### 对象实例

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/objects?type=xxx&dataset=xxx&page=1&size=20` | 分页列表 |
| `POST` | `/api/v1/objects` | 创建对象 |
| `GET` | `/api/v1/objects/:id` | 对象详情 |
| `PUT` | `/api/v1/objects/:id` | 更新对象 |
| `DELETE` | `/api/v1/objects/:id` | 删除对象（级联删除关联链接） |
| `GET` | `/api/v1/objects/search?q=xxx` | 全文搜索（GIN 索引） |

### 链接

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/links?dataset=xxx` | 链接列表 |
| `POST` | `/api/v1/links` | 创建链接（校验 sourceType/targetType） |
| `DELETE` | `/api/v1/links/:id` | 删除链接 |

### 图谱

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/graph/structure` | 类型级结构图谱（nodes + edges） |
| `GET` | `/api/v1/graph/entities?dataset=xxx` | 实例级实体图谱 |

### 动作

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/actions/:actionName` | 执行动作（记录 before/after 快照） |
| `GET` | `/api/v1/actions/history?page=1&size=20` | 动作历史 |

### 模板

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/templates` | 模板列表 |
| `GET` | `/api/v1/templates/:id` | 模板详情（含类型定义） |
| `POST` | `/api/v1/templates/:id/analyze` | LLM 映射分析（Phase 2） |
| `POST` | `/api/v1/templates/:id/apply` | 导入模板（幂等） |

### 数据集 & 统计

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/datasets` | 数据集列表 |
| `POST` | `/api/v1/datasets` | 注册数据集 |
| `GET` | `/api/v1/stats` | 系统统计（计数概览） |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 服务健康 + 数据库连通性 |

---

## 错误码

遵循 RFC 9457 规范，统一返回格式：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "详细错误描述",
    "details": [{"field": "api_name", "code": "REQUIRED"}],
    "request_id": "uuid-xxxx"
  }
}
```

| 错误码 | HTTP | 说明 |
|--------|------|------|
| `VALIDATION_ERROR` | 400 | 参数校验失败 |
| `INVALID_JSON` | 400 | JSON 格式错误 |
| `UNAUTHORIZED` | 401 | API Key 无效 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突（如重复 api_name） |
| `BUSINESS_RULE_ERROR` | 422 | 业务规则冲突 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## 配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `API_KEY` | API 认证密钥 | 自动生成 UUID |
| `DATABASE_URL` | PostgreSQL 连接 | `postgresql://ontologyready:ontologyready@postgres:5432/ontologyready` |
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | 监听端口 | `8000` |

前端配置：

| 环境变量 | 说明 |
|----------|------|
| `VITE_API_KEY` | 前端注入的 API Key |

---

## 许可证

MIT
