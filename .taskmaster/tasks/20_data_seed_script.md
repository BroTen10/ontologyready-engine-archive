# Task 20: 数据：种子数据脚本

**状态:** pending | **优先级:** medium | **依赖:** 18, 6

## 描述

编写种子数据脚本，用于演示图谱可视化和实例管理功能。

## 详情

创建 seed.sql 或 seed.ts 脚本，插入供应链 ATP 模板的示例数据：
- 5-10 个 Customer、10-15 个 Product、15-20 个 SalesOrder
- 10-15 个 ATPCommitment、5-8 个 Supplier
- 对应的链接关系

数据应有业务语义（如客户「华东电子」的订单和交期承诺）。脚本支持幂等（INSERT ... ON CONFLICT 或先 TRUNCATE）。

## 测试策略

运行种子脚本后，通过 API 和前端验证数据展示。
