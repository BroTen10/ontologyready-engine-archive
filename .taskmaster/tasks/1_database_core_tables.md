# Task 1: 数据库：4 张核心表 DDL + init.sql

**状态:** pending | **优先级:** high | **依赖:** 无

## 描述

创建 4 张核心表 DDL（ontology_types, ontology_objects, ontology_links, ontology_actions_log），包含所有索引、生成列、外键约束、CHECK 约束和 JSONB COMPRESSION。同时编写 init.sql 初始化脚本。

## 详情

参考 PRD 4.1 节完整 DDL：
- `ontology_types`：api_name PK, type CHECK, config JSONB, maturity
- `ontology_objects`：UUID PK, object_type FK, external_id, dataset_id, display_name GENERATED ALWAYS, properties JSONB LZ4, embedding VECTOR
- `ontology_links`：UUID PK, link_type FK, source_id FK, target_id FK, dataset_id, properties JSONB LZ4, confidence
- `ontology_actions_log`：UUID PK, action_type, parameters, status CHECK, before/after_snapshot, executed_by, executed_at

所有索引：GIN on properties, B-tree on foreign keys, composite on dataset_id+type。

## 测试策略

运行 init.sql 验证所有表创建成功，检查索引和约束。
