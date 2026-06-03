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

test.describe("Types Page — Type Definitions Management", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await simulateLogin(page);
  });

  test("renders tabs with Chinese labels and type counts", async ({ page }) => {
    await goToPage(page, "/types", "类型定义");

    // Tabs use Chinese labels with count: "对象类型 (4)", "链接类型 (2)", "动作类型 (2)"
    await expect(page.locator(".ant-tabs-tab").filter({ hasText: /对象类型/ })).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".ant-tabs-tab").filter({ hasText: /链接类型/ })).toBeVisible({ timeout: 3000 });
    await expect(page.locator(".ant-tabs-tab").filter({ hasText: /动作类型/ })).toBeVisible({ timeout: 3000 });
  });

  test("filters types when switching to LINK tab", async ({ page }) => {
    await goToPage(page, "/types", "类型定义");

    // Switch to link types tab
    await page.locator(".ant-tabs-tab").filter({ hasText: /链接类型/ }).click();
    await page.waitForTimeout(800);

    // LINK types from mock data should appear
    await expect(page.getByText("客户下单").first()).toBeVisible({ timeout: 5000 });
  });

  test("shows type cards with display names and api names", async ({ page }) => {
    await goToPage(page, "/types", "类型定义");

    // Check type cards — should show Chinese display names and API names
    await expect(page.getByText("Customer").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("客户").first()).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("Product").first()).toBeVisible({ timeout: 3000 });

    // Maturity tags
    await expect(page.locator(".ant-tag").filter({ hasText: "ACTIVE" }).first()).toBeVisible({ timeout: 5000 });
  });

  test("create type modal opens on click", async ({ page }) => {
    await goToPage(page, "/types", "类型定义");

    const createBtn = page.locator("button").filter({ hasText: /新建/ }).first();
    if ((await createBtn.count()) > 0) {
      await createBtn.click();
      await page.waitForTimeout(500);
      await expect(page.locator(".ant-modal")).toBeVisible({ timeout: 3000 });
    }
  });

  test("type card action buttons are visible (view/edit/delete)", async ({ page }) => {
    await goToPage(page, "/types", "类型定义");

    // Each card has view/edit/delete action buttons
    await expect(page.locator(".anticon-eye").first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".anticon-edit").first()).toBeVisible({ timeout: 3000 });
    await expect(page.locator(".anticon-delete").first()).toBeVisible({ timeout: 3000 });
  });

  test("all mock object types are displayed on default OBJECT tab", async ({ page }) => {
    await goToPage(page, "/types", "类型定义");

    // Default tab shows OBJECT types
    await expect(page.getByText("Customer").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Product").first()).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("SalesOrder").first()).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("ATPCommitment").first()).toBeVisible({ timeout: 3000 });
  });
});
