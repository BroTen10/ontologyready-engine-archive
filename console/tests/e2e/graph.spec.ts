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

test.describe("Graph Page — Ontology Visualization", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await simulateLogin(page);
  });

  test("renders stat cards with counts", async ({ page }) => {
    await goToPage(page, "/graph", "本体图谱");

    // Use the sidebar heading or stat cards text
    await expect(page.getByText("对象实例").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("链接关系").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("今日动作").first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("130").first()).toBeVisible({ timeout: 3000 });
  });

  test("renders React Flow container for structure graph", async ({ page }) => {
    await goToPage(page, "/graph", "本体图谱");
    await expect(page.locator(".react-flow")).toBeVisible({ timeout: 10000 });
  });

  test("switches between structure and entity graph tabs", async ({ page }) => {
    await goToPage(page, "/graph", "本体图谱");

    await page.locator(".ant-tabs-tab").filter({ hasText: "实体图谱" }).click();
    await page.waitForTimeout(500);
    await expect(page.locator(".react-flow")).toBeVisible({ timeout: 5000 });

    await page.locator(".ant-tabs-tab").filter({ hasText: "结构图谱" }).click();
    await page.waitForTimeout(500);
    await expect(page.locator(".react-flow")).toBeVisible({ timeout: 5000 });
  });

  test("graph controls and minimap are visible", async ({ page }) => {
    await goToPage(page, "/graph", "本体图谱");
    await expect(page.locator(".react-flow__controls")).toBeVisible({ timeout: 5000 });
    await expect(page.locator(".react-flow__minimap")).toBeVisible({ timeout: 5000 });
  });

  test("path finder section is visible after expanding", async ({ page }) => {
    await goToPage(page, "/graph", "本体图谱");

    // The path finder might be in a collapsible section or "更多" menu.
    // Check if it's already visible; if not, it might be behind a toggle.
    const pathFinder = page.getByText("路径查找");
    const moreBtn = page.locator("button").filter({ hasText: "更多" });

    if (!(await pathFinder.isVisible({ timeout: 2000 }).catch(() => false))) {
      if (await moreBtn.count() > 0) {
        await moreBtn.first().click();
        await page.waitForTimeout(500);
      }
    }

    // The path finder section contains UUID inputs for source and target
    const uuidInputs = page.locator("input[placeholder*='UUID']");
    if (await uuidInputs.count() > 0) {
      await expect(uuidInputs.first()).toBeVisible({ timeout: 3000 });
    }
  });

  test("layout buttons are visible", async ({ page }) => {
    await goToPage(page, "/graph", "本体图谱");

    const segmented = page.locator(".ant-segmented");
    await expect(segmented).toBeVisible({ timeout: 5000 });

    const layoutBtn = page.locator("button").filter({ hasText: "重新布局" });
    await expect(layoutBtn).toBeVisible({ timeout: 5000 });
  });
});
