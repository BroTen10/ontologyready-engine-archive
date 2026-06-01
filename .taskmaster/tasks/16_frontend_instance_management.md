# Task 16: 前端：实例管理页面

**状态:** pending | **优先级:** high | **依赖:** 12, 13, 6, 7, 9

## 描述

实现实例管理页面，包含对象实例、链接实例、Action 历史三个 Tab。

## 详情

三个 Tab（对象实例/链接实例/Action 历史）：

- **对象实例 Tab**：类型筛选器 + 搜索框 + 表格（ID/Type/display_name/Properties 预览/Action 删除，分页 20/页）
- **链接实例 Tab**：表格（Source→Target/LinkType/Properties/删除）
- **Action 历史 Tab**：表格（ActionType/Status/ExecutedBy/ExecutedAt/详情展开）

URL 参数支持：`?type=Customer` 预设类型筛选。

## 测试策略

筛选、搜索、分页操作，删除对象/链接/查看 Action 历史。
