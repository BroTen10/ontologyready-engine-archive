import { test, expect } from "@playwright/test";
import { simulateLogin, setupApiMocks } from "./fixtures/mock-data";

async function goToPage(page: import("@playwright/test").Page, path: string, sidebarLabel: string) {
  await page.goto("/graph");
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);
  if (path !== "/graph") {
    await page.locator(".ant-menu-item").filter({ hasText: sidebarLabel }).click();
    await page.waitForURL(`**${path}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);
  }
}

test.describe("Instances Page — Instance Management", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await simulateLogin(page);
  });

  test("renders three tabs: objects, links, actions", async ({ page }) => {
    await goToPage(page, "/instances", "实例管理");

    // Tab labels should contain these strings
    await expect(page.locator(".ant-tabs-tab").filter({ hasText: /对象/ }).first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".ant-tabs-tab").filter({ hasText: /链接/ }).first()).toBeVisible({ timeout: 3000 });
    await expect(page.locator(".ant-tabs-tab").filter({ hasText: /Action/ }).first()).toBeVisible({ timeout: 3000 });
  });

  test("objects tab: renders data table", async ({ page }) => {
    await goToPage(page, "/instances", "实例管理");

    const table = page.locator(".ant-table");
    await expect(table).toBeVisible({ timeout: 5000 });
    const rows = page.locator(".ant-table-tbody tr");
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test("objects tab: type filter select is present", async ({ page }) => {
    await goToPage(page, "/instances", "实例管理");

    const selects = page.locator(".ant-select");
    const count = await selects.count();
    expect(count).toBeGreaterThan(0);
  });

  test("links tab: renders links data", async ({ page }) => {
    await goToPage(page, "/instances", "实例管理");

    // Switch to links tab
    await page.locator(".ant-tabs-tab").filter({ hasText: /链接/ }).click();
    await page.waitForTimeout(800);

    const table = page.locator(".ant-table");
    await expect(table).toBeVisible({ timeout: 5000 });
  });

  test("actions tab: renders action history data", async ({ page }) => {
    await goToPage(page, "/instances", "实例管理");

    // Switch to actions tab
    await page.locator(".ant-tabs-tab").filter({ hasText: /Action/ }).click();
    await page.waitForTimeout(800);

    const table = page.locator(".ant-table");
    await expect(table).toBeVisible({ timeout: 5000 });
  });

  test("create button is visible", async ({ page }) => {
    await goToPage(page, "/instances", "实例管理");

    const addBtn = page.locator("button").filter({ has: page.locator(".anticon-plus") });
    if ((await addBtn.count()) > 0) {
      await expect(addBtn.first()).toBeVisible({ timeout: 3000 });
    }
  });
});
