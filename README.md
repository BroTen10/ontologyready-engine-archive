# OntologyReady

企业级本体管理平台 — 通过 4 张 PostgreSQL 表 + 1 个 REST API + 1 个管理控制台，提供本体建模、图谱可视化、实例管理和行业模板能力。

**一句话定位：** 一个 Docker Compose 命令启动的企业本体管理平台。

## 技术栈

| 层级 | 技术 |
|------|------|
| 数据库 | PostgreSQL 16 + pgvector |
| 后端 | Python FastAPI |
| 前端 | React 18 + Ant Design + React Flow |
| 部署 | Docker Compose |

## 快速开始

```bash
# 配置 API Key
cp .env.example .env
# 编辑 .env 填入密钥

# 一键启动
docker compose up -d

# 打开浏览器
open http://localhost:3000
```

## 项目结构

```
api/          # FastAPI 后端
console/      # React 前端
init.sql      # 数据库初始化脚本
```

## 许可证

MIT
