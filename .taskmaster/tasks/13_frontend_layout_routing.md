# Task 13: 前端：整体布局 + 路由 + 导航

**状态:** pending | **优先级:** high | **依赖:** 12

## 描述

实现整体布局框架、侧边栏导航、顶部栏、路由配置。

## 详情

使用 Ant Design Layout 组件：
- **Sider**：Logo + 4 项导航菜单（本体图谱/类型定义/实例管理/行业建模）
- **Header**：数据集选择器 Dropdown + 用户头像 Dropdown
- **Content**：面包屑 + 路由出口
- **Footer**：版权

路由：`/` → redirect `/graph`, `/graph`, `/types`, `/instances`, `/modeling`。

数据集选择器切换后通过 React Query 全局状态触发数据刷新。

## 测试策略

点击导航切换页面，数据集选择器切换触发全局状态更新。
