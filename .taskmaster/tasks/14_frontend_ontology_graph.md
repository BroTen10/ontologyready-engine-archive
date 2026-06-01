# Task 14: 前端：本体图谱页面（React Flow）

**状态:** pending | **优先级:** high | **依赖:** 12, 13, 8

## 描述

实现本体图谱可视化页面，支持类型级结构和实例级实体两种视图。

## 详情

使用 React Flow 渲染力导向图。节点=ObjectType（显示彩色图标+名称），边=LinkType。

功能：
- 布局切换（层次化 dagre/力导向 d3-force/径向）
- 缩放平移（minZoom/maxZoom）、全屏适应（fitView）
- Tab 切换：「结构图谱」（GET /graph/structure）和「实体图谱」（GET /graph/entities?dataset=xxx）

交互：
- 点击节点 → 跳转 `/types?name=xxx`
- 悬停连线 → Tooltip 显示 LinkType 名称
- 右键画布 → Dropdown（刷新/聚焦/导出 PNG）

## 测试策略

加载图谱数据、验证节点渲染、测试布局切换和交互。
