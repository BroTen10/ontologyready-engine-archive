// Shared mock data for E2E tests

export const mockUser = {
  id: "u-001",
  username: "admin",
  email: "admin@ontologyready.io",
  full_name: "管理员",
  is_active: true,
  is_superuser: true,
};

export const mockTokens = {
  access_token: "mock-access-token-for-e2e",
  refresh_token: "mock-refresh-token-for-e2e",
  token_type: "bearer",
};

export const mockTypes = [
  { api_name: "Customer", type: "OBJECT", display_name: "客户", description: "采购方企业实体", config: { color: "#1890ff" }, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "Product", type: "OBJECT", display_name: "产品", description: "成品 SKU", config: { color: "#52c41a" }, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "SalesOrder", type: "OBJECT", display_name: "销售订单", description: "客户采购订单", config: { color: "#722ed1" }, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "ATPCommitment", type: "OBJECT", display_name: "交期承诺", description: "ATP 承诺", config: { color: "#fa8c16" }, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "customer_places_order", type: "LINK", display_name: "客户下单", description: "Customer -> SalesOrder", config: {}, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "order_contains_product", type: "LINK", display_name: "订单包含产品", description: "SalesOrder -> Product", config: {}, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "ApproveCommitment", type: "ACTION", display_name: "审批交期承诺", description: "审批 ATP 承诺", config: {}, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
  { api_name: "CreateSalesOrder", type: "ACTION", display_name: "创建销售订单", description: "创建新销售订单", config: {}, maturity: "ACTIVE", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
];

export const mockObjects = {
  data: [
    { id: "obj-001", object_type: "Customer", external_id: "CUST-001", dataset_id: "default", display_name: "华东电子集团", properties: { name: "华东电子集团", region: "华东", industry: "电子制造" }, created_at: "2024-01-15T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
    { id: "obj-002", object_type: "Customer", external_id: "CUST-002", dataset_id: "default", display_name: "华南智造科技", properties: { name: "华南智造科技", region: "华南", industry: "智能制造" }, created_at: "2024-01-20T00:00:00Z", updated_at: "2024-01-20T00:00:00Z" },
    { id: "obj-003", object_type: "Product", external_id: "SKU-001", dataset_id: "default", display_name: "工业控制器 X1000", properties: { name: "工业控制器 X1000", category: "控制器", unit_price: 2800 }, created_at: "2024-02-01T00:00:00Z", updated_at: "2024-02-01T00:00:00Z" },
    { id: "obj-004", object_type: "Product", external_id: "SKU-002", dataset_id: "default", display_name: "伺服电机 M200", properties: { name: "伺服电机 M200", category: "电机", unit_price: 4200 }, created_at: "2024-02-01T00:00:00Z", updated_at: "2024-02-01T00:00:00Z" },
    { id: "obj-005", object_type: "SalesOrder", external_id: "SO-2024-001", dataset_id: "default", display_name: "SO-2024-001", properties: { name: "SO-2024-001", status: "已确认", total_amount: 56000 }, created_at: "2024-03-01T00:00:00Z", updated_at: "2024-03-01T00:00:00Z" },
  ],
  total: 5,
  page: 1,
  size: 20,
};

export const mockStructureGraph = {
  nodes: [
    { id: "Customer", label: "客户", apiName: "Customer", type: "OBJECT", color: "#1890ff" },
    { id: "Product", label: "产品", apiName: "Product", type: "OBJECT", color: "#52c41a" },
    { id: "SalesOrder", label: "销售订单", apiName: "SalesOrder", type: "OBJECT", color: "#722ed1" },
  ],
  edges: [
    { id: "e-001", source: "Customer", target: "SalesOrder", label: "客户下单" },
    { id: "e-002", source: "SalesOrder", target: "Product", label: "订单包含产品" },
  ],
};

export const mockEntityGraph = {
  nodes: [
    { id: "obj-001", label: "华东电子集团", type: "OBJECT", color: "#1890ff", objectType: "Customer" },
    { id: "obj-002", label: "华南智造科技", type: "OBJECT", color: "#1890ff", objectType: "Customer" },
    { id: "obj-003", label: "工业控制器 X1000", type: "OBJECT", color: "#52c41a", objectType: "Product" },
    { id: "obj-005", label: "SO-2024-001", type: "OBJECT", color: "#722ed1", objectType: "SalesOrder" },
  ],
  edges: [
    { id: "le-001", source: "obj-001", target: "obj-005", label: "客户下单" },
    { id: "le-002", source: "obj-005", target: "obj-003", label: "订单包含产品" },
  ],
};

export const mockStats = { objectCount: 130, linkCount: 210, typeCount: 47, datasetCount: 2, actionsToday: 15 };

export const mockDatasets = [
  { value: "default", label: "默认数据集 (供应链ATP)" },
  { value: "crm", label: "CRM 数据" },
];

export const mockTemplates = [
  {
    id: "supply-chain-atp",
    name: "供应链 ATP",
    description: "涵盖客户、订单、物料、库存、交期承诺等核心供应链实体",
    tags: ["supply-chain", "atp"],
    stats: { objectTypes: 12, linkTypes: 19, actionTypes: 12 },
  },
  {
    id: "crm",
    name: "客户管理 CRM",
    description: "涵盖客户、线索、商机、联系人、活动等核心 CRM 实体",
    tags: ["crm", "sales"],
    stats: { objectTypes: 8, linkTypes: 10, actionTypes: 6 },
  },
];

export const mockLinks = [
  { id: "link-001", link_type: "customer_places_order", source_id: "obj-001", target_id: "obj-005", dataset_id: "default", properties: {}, confidence: 1.0, created_at: "2024-03-01T00:00:00Z" },
];

export const mockActionHistory = {
  data: [
    { id: "act-001", action_type: "CreateSalesOrder", status: "SUCCESS", executed_by: "admin", executed_at: "2024-06-01T10:00:00Z" },
    { id: "act-002", action_type: "ApproveCommitment", status: "SUCCESS", executed_by: "admin", executed_at: "2024-06-01T09:00:00Z" },
  ],
  total: 2,
  page: 1,
  size: 20,
};

// Set up all API mocks on a page
export async function setupApiMocks(page: import("@playwright/test").Page) {
  // Bypass /login API calls
  await page.route("**/api/v1/auth/login", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockTokens) })
  );
  await page.route("**/api/v1/auth/profile", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockUser) })
  );
  await page.route("**/api/v1/auth/refresh", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockTokens) })
  );

  // Types
  await page.route("**/api/v1/types**", (route) => {
    const method = route.request().method();
    const url = route.request().url();
    if (method === "GET") {
      if (url.includes("/types/") && !url.endsWith("/types")) {
        const apiName = url.split("/types/")[1].split("?")[0];
        const found = mockTypes.find((t) => t.api_name === apiName);
        return route.fulfill({ status: found ? 200 : 404, contentType: "application/json", body: JSON.stringify(found || { error: { message: "Not found" } }) });
      }
      const typeParam = new URL(url).searchParams.get("type");
      const filtered = typeParam ? mockTypes.filter((t) => t.type === typeParam) : mockTypes;
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(filtered) });
    }
    if (method === "POST") return route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(mockTypes[0]) });
    return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  // Objects
  await page.route("**/api/v1/objects/search**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockObjects.data.slice(0, 2)) })
  );
  await page.route("**/api/v1/objects**", (route) => {
    const method = route.request().method();
    if (method === "GET") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockObjects) });
    if (method === "POST") return route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(mockObjects.data[0]) });
    return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  // Graph
  await page.route("**/api/v1/graph/structure", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockStructureGraph) })
  );
  await page.route("**/api/v1/graph/entities**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockEntityGraph) })
  );

  // Stats
  await page.route("**/api/v1/stats", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockStats) })
  );

  // Datasets
  await page.route("**/api/v1/datasets", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockDatasets) })
  );

  // Links
  await page.route("**/api/v1/links**", (route) => {
    if (route.request().method() === "GET")
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockLinks) });
    return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
  });

  // Actions history
  await page.route("**/api/v1/actions/history**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockActionHistory) })
  );

  // Templates
  await page.route("**/api/v1/templates**", (route) => {
    const url = route.request().url();
    if (url.includes("/apply")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "success", message: "已导入 5 个类型定义", created: { objects: 3, links: 1, actions: 1 } }) });
    if (url.includes("/analyze")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "not_implemented" }) });
    if (url.endsWith("/templates")) return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(mockTemplates) });
    const templateId = url.split("/templates/")[1]?.split("?")[0];
    const found = mockTemplates.find((t) => t.id === templateId);
    return route.fulfill({ status: found ? 200 : 404, contentType: "application/json", body: JSON.stringify(found || {}) });
  });
}

// Set localStorage to simulate logged-in state without going through login page.
// Uses addInitScript so localStorage is available before the React app initializes.
export async function simulateLogin(page: import("@playwright/test").Page) {
  await page.addInitScript(() => {
    localStorage.setItem("access_token", "mock-access-token-for-e2e");
    localStorage.setItem("refresh_token", "mock-refresh-token-for-e2e");
    localStorage.setItem("user", JSON.stringify({ id: "u-001", username: "admin", full_name: "管理员", is_superuser: true }));
  });
}
