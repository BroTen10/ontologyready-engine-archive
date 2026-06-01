# Task 2: API：项目框架搭建 + 健康检查

**状态:** pending | **优先级:** high | **依赖:** 1

## 描述

搭建后端框架（Node.js Fastify 或 Python FastAPI），配置数据库连接，实现健康检查端点 GET /health。

## 详情

建议 FastAPI（Python）或 Fastify（Node.js）。数据库连接池配置（pgbouncer 可选）。健康检查返回 `{status: 'ok', timestamp, db: 'connected'}`。

## 测试策略

启动服务后 curl /health 返回 200。
