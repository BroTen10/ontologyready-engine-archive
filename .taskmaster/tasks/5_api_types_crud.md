# Task 5: API：类型定义 CRUD

**状态:** pending | **优先级:** high | **依赖:** 1, 2

## 描述

实现类型定义的完整 CRUD API：列表、创建、详情、更新、删除、属性编辑。

## 详情

端点：
- `GET /api/v1/types` — 支持 `?type=OBJECT|LINK|ACTION` 过滤
- `POST /api/v1/types` — 验证 config JSONB schema
- `GET /api/v1/types/:apiName` — 类型详情
- `PUT /api/v1/types/:apiName` — 更新类型
- `DELETE /api/v1/types/:apiName` — 检查是否被实例引用，有引用返回 BUSINESS_RULE_ERROR
- `PATCH /api/v1/types/:apiName/properties` — 编辑属性

config 校验规则参见 PRD 4.1.1。

## 测试策略

CRUD 全流程测试 + 重复 api_name 冲突测试 + 删除被引用类型测试。
