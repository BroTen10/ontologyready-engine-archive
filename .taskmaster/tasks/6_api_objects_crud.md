# Task 6: API：对象实例 CRUD + 搜索

**状态:** pending | **优先级:** high | **依赖:** 1, 2

## 描述

实现对象实例 CRUD + 搜索 API：分页列表、创建、详情、更新、删除、全文搜索。

## 详情

端点：
- `GET /api/v1/objects` — `?type=xxx&dataset=xxx&page=1&size=20`
- `POST /api/v1/objects` — 验证 object_type 存在，properties 存入 JSONB
- `GET /api/v1/objects/:id` — 对象详情
- `PUT /api/v1/objects/:id` — 检查 readOnly 配置
- `DELETE /api/v1/objects/:id` — 级联删除关联链接
- `GET /api/v1/objects/search?q=xxx` — 使用 GIN 索引搜索 JSONB

## 测试策略

CRUD + 分页 + 搜索 + readOnly 保护测试。
