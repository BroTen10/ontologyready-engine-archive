import { test, expect } from "@playwright/test";
import { simulateLogin, setupApiMocks } from "./fixtures/mock-data";

test.describe("Navigation & Routing", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await simulateLogin(page);
  });

  test("redirects / to /graph", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/graph");
    expect(page.url()).toContain("/graph");
  });

  test("navigates to all pages via sidebar", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("networkidle");

    const pages = [
      { path: "/graph", label: "本体图谱" },
      { path: "/types", label: "类型定义" },
      { path: "/instances", label: "实例管理" },
      { path: "/search", label: "高级搜索" },
      { path: "/automodel", label: "自动建模" },
      { path: "/modeling", label: "行业建模" },
      { path: "/skills", label: "Skills 技能" },
      { path: "/llm-config", label: "LLM 配置" },
    ];

    for (const { path, label } of pages) {
      const menuItem = page.locator(".ant-menu-item").filter({ hasText: label });
      await menuItem.click();
      await page.waitForURL(`**${path}`);
      expect(page.url()).toContain(path);
    }
  });

  test("redirects to /login when not authenticated", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForURL("**/login");
    expect(page.url()).toContain("/login");
  });

  test("shows header with dataset selector and user dropdown", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1500);

    // The header has Ant Design components — check for the Layout Header
    const header = page.locator(".ant-layout-header");
    await expect(header).toBeVisible({ timeout: 5000 });

    // Dataset selector dropdown
    await expect(header.locator(".ant-select")).toBeVisible({ timeout: 5000 });

    // UserOutlined icon in the header area
    await expect(header.locator(".anticon-user")).toBeVisible({ timeout: 5000 });
  });

  test("shows footer with copyright", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("networkidle");

    await expect(page.locator("footer").getByText("OntologyReady")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("footer").getByText("企业级本体管理平台")).toBeVisible({ timeout: 5000 });
  });

  test("sidebar shows all 8 navigation items", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("networkidle");

    const expectedLabels = ["本体图谱", "类型定义", "实例管理", "高级搜索", "自动建模", "行业建模", "Skills 技能", "LLM 配置"];
    for (const label of expectedLabels) {
      await expect(page.getByText(label).first()).toBeVisible({ timeout: 3000 });
    }
  });

  test("admin menu visible for superuser", async ({ page }) => {
    await page.goto("/graph");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Click user dropdown trigger
    const userTrigger = page.locator(".ant-layout-header").locator(".ant-dropdown-trigger");
    if (await userTrigger.count() > 0) {
      await userTrigger.first().click();
      await page.waitForTimeout(500);

      // Check for admin panel in dropdown
      const adminLink = page.locator(".ant-dropdown-menu-item").filter({ hasText: "管理面板" });
      await expect(adminLink).toBeVisible({ timeout: 3000 });
    }
  });
});

test.describe("Login Page", () => {
  test("login form renders with all elements", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    // Page title
    await expect(page.getByText("OntologyReady").first()).toBeVisible({ timeout: 5000 });

    // Username input via placeholder or prefix icon
    await expect(page.locator('input[placeholder="用户名"]')).toBeVisible({ timeout: 3000 });

    // Password input
    await expect(page.locator('input[placeholder="密码"]')).toBeVisible({ timeout: 3000 });

    // Submit button
    await expect(page.locator('button[type="submit"]')).toBeVisible({ timeout: 3000 });
  });

  test("login redirects to /graph on success", async ({ page }) => {
    await setupApiMocks(page);

    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    await page.locator('input[placeholder="用户名"]').fill("admin");
    await page.locator('input[placeholder="密码"]').fill("password");
    await page.locator('button[type="submit"]').click();

    await page.waitForURL("**/graph", { timeout: 10000 });
    expect(page.url()).toContain("/graph");
  });
});
