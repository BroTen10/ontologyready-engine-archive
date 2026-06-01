# Task 9: API：动作执行 + 历史日志

**状态:** pending | **优先级:** medium | **依赖:** 5, 6

## 描述

实现动作执行和历史审计 API。

## 详情

- `POST /api/v1/actions/:actionName`：读取 action_type config，验证必填参数，原子执行（一个 PG 事务），记录 before_snapshot 和 after_snapshot 到 ontology_actions_log
- `GET /api/v1/actions/history`：分页查询，按 executed_at DESC 排序

## 测试策略

执行成功和失败动作，验证日志记录和 before/after snapshot。
