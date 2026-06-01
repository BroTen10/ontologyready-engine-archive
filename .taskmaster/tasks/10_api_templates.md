# Task 10: API：行业模板（列表/详情/分析/导入）

**状态:** pending | **优先级:** medium | **依赖:** 5

## 描述

实现行业模板 API：模板列表、详情、LLM 映射分析入口（MVP 预留）、导入执行。

## 详情

- `GET /api/v1/templates`：返回模板列表 `[{id, name, description, tags, stats}]`
- `GET /api/v1/templates/:id`：返回模板完整定义（objectTypes, linkTypes, actionTypes）
- `POST /api/v1/templates/:id/analyze`：LLM 映射分析入口，MVP 阶段返回空（Phase 2 对接 OpenAI/通义千问）
- `POST /api/v1/templates/:id/apply`：批量创建类型定义和属性

## 测试策略

模板列表、详情、导入流程测试。
