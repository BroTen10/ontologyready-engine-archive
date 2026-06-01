# Task 15: 前端：类型定义页面

**状态:** pending | **优先级:** high | **依赖:** 12, 13, 5

## 描述

实现类型定义管理页面，展示所有 Object/Link/Action 类型。

## 详情

三个 Tab（ObjectType/LinkType/ActionType），每 Tab 内用卡片网格（Ant Design Card.Grid）展示。

每张卡片：彩色图标、中文名、英文 API Name、描述、属性数量、创建时间、成熟度标签。

操作：编辑（打开 TypeFormModal）、展开详情、删除（Confirm + 引用检查）。

TypeFormModal：基础信息区、属性表格（name/type 下拉/required 开关/description/删除行）、「JSON 编辑」按钮、「+ 添加属性」按钮。

## 测试策略

创建、编辑、删除类型，验证属性增删改，JSON 编辑模式。
