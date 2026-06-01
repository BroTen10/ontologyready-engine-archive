# Task 11: API：数据集管理 + 系统统计

**状态:** pending | **优先级:** medium | **依赖:** 1, 2

## 描述

实现数据集 API 和系统统计概览 API。

## 详情

- `GET /api/v1/datasets`：查询所有不重复的 dataset_id
- `POST /api/v1/datasets`：注册新 dataset（body: {id, label}）
- `GET /api/v1/stats`：返回 `{objectCount, linkCount, typeCount, datasetCount, actionsToday}`

## 测试策略

创建数据集、查询列表、验证统计数据准确性。
