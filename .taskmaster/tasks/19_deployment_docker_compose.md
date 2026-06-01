# Task 19: 部署：Docker Compose 一键部署

**状态:** pending | **优先级:** high | **依赖:** 1, 2, 12

## 描述

编写 Docker Compose 配置（3 容器）和快速启动文档。

## 详情

**docker-compose.yml**：
- `services.postgres`：pgvector/pgvector:pg16，环境变量 POSTGRES_DB/USER/PASSWORD，volumes pgdata + ./init.sql，healthcheck pg_isready
- `services.api`：build ./api，port 8000，环境变量 DATABASE_URL + API_KEY，depends_on postgres healthy
- `services.console`：build ./console，port 3000，环境变量 VITE_API_URL + VITE_API_KEY，depends_on api
- `volumes.pgdata`

还需要：`.env.example`（API_KEY 占位）、`Dockerfile.api`（多阶段构建）、`Dockerfile.console`（nginx 或 vite preview）。

## 测试策略

docker-compose up -d，验证 3 容器启动成功，访问 localhost:3000。
