# Task 18: 数据：2 个内置行业模板

**状态:** pending | **优先级:** medium | **依赖:** 1

## 描述

创建供应链 ATP 和客户管理 CRM 两个预设模板的 JSON 数据文件。

## 详情

**模板 1 - 供应链 ATP**：
- 12 个对象类型（Customer, Product, SalesOrder, ATPCommitment, ProductionOrder, Inventory, Supplier, PurchaseOrder, Material, Warehouse, LogisticsOrder, BOM）
- 19 个关系类型（belongs_to, contains, triggers, governed_by, supplied_by, sourced_from, stored_in, fulfills, produces, ships_to 等）
- 12 个动作类型（ApproveCommitment, CreateOrder, UpdateInventory 等）

**模板 2 - CRM**：
- 8 个对象类型（Customer, Lead, Opportunity, Contact, Activity, Order, Product, User）
- 对应关系和动作

所有类型含完整 Description（面向 LLM）、config（颜色/图标/分组）。数据存储为 JSON 文件，在 init.sql 或 seed 脚本中导入。

## 测试策略

验证模板 JSON 结构完整性，导入后检查类型数量。
