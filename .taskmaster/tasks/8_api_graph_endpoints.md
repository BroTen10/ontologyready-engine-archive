# Task 8: API：图谱端点（结构图谱 + 实体图谱）

**状态:** pending | **优先级:** high | **依赖:** 5, 6, 7

## 描述

实现图谱 API：类型级结构图谱和实例级实体图谱（含递归 CTE 图遍历）。

## 详情

- `GET /api/v1/graph/structure`：返回 `{nodes: [{id, label, apiName, type, color, propertyCount}], edges: [{id, source, target, label, relationship}]}`
- `GET /api/v1/graph/entities`：支持 `?dataset=xxx`，使用递归 CTE 实现 2-3 跳图遍历

## 测试策略

验证图谱节点和边数量，测试不同层级遍历。
