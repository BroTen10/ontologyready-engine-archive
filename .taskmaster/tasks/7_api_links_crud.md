# Task 7: API：链接 CRUD

**状态:** pending | **优先级:** high | **依赖:** 1, 2

## 描述

实现链接管理 API：列表（支持 dataset 过滤）、创建、删除。

## 详情

端点：
- `GET /api/v1/links` — `?dataset=xxx` 过滤
- `POST /api/v1/links` — 验证 source_id 和 target_id 存在、link_type 有效
- `DELETE /api/v1/links/:id`

创建时校验 link_type config 中的 sourceType/targetType 约束。

## 测试策略

创建链接、验证外键约束、删除链接。
