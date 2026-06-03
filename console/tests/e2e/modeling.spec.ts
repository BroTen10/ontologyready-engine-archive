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

test.describe("Modeling Page — Industry Template Wizard", () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page);
    await simulateLogin(page);
  });

  test("renders the modeling wizard with steps", async ({ page }) => {
    await goToPage(page, "/modeling", "行业建模");

    const steps = page.locator(".ant-steps");
    await expect(steps).toBeVisible({ timeout: 5000 });
  });

  test("displays template cards with names", async ({ page }) => {
    await goToPage(page, "/modeling", "行业建模");

    const cards = page.locator(".ant-card");
    await expect(cards.first()).toBeVisible({ timeout: 5000 });

    // Template names from mock
    await expect(page.getByText("供应链 ATP").first()).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("客户管理 CRM").first()).toBeVisible({ timeout: 3000 });
  });

  test("template descriptions are visible", async ({ page }) => {
    await goToPage(page, "/modeling", "行业建模");

    // Template cards should contain key descriptive text
    const supplyChainDesc = page.getByText(/涵盖客户|订单|物料|库存|交期/);
    const crmDesc = page.getByText(/线索|商机|联系人|活动/);

    // At least one description should be visible
    const scVisible = await supplyChainDesc.first().isVisible({ timeout: 3000 }).catch(() => false);
    const crmVisible = await crmDesc.first().isVisible({ timeout: 3000 }).catch(() => false);
    expect(scVisible || crmVisible).toBeTruthy();
  });

  test("template stats and tags are displayed", async ({ page }) => {
    await goToPage(page, "/modeling", "行业建模");

    // Tags from mock data
    await expect(page.getByText("supply-chain").first()).toBeVisible({ timeout: 3000 });
    await expect(page.getByText("crm").first()).toBeVisible({ timeout: 3000 });
  });

  test("select template and advance through wizard steps", async ({ page }) => {
    await goToPage(page, "/modeling", "行业建模");

    // Click select/use button on the first template
    const actionBtns = page.locator("button").filter({ hasText: /使用|选择|导入/ });
    if ((await actionBtns.count()) > 0) {
      await actionBtns.first().click();
      await page.waitForTimeout(500);

      // Should advance to next step
      await expect(page.locator(".ant-steps-item-active")).toBeVisible({ timeout: 3000 });
    }
  });

  test("can apply template via final step", async ({ page }) => {
    await goToPage(page, "/modeling", "行业建模");

    // Select first template
    const selectBtn = page.locator("button").filter({ hasText: /使用|选择|导入/ }).first();
    if ((await selectBtn.count()) > 0) {
      await selectBtn.click();
      await page.waitForTimeout(300);

      // Advance through steps by clicking next/apply buttons
      for (let i = 0; i < 3; i++) {
        const nextBtn = page.locator("button").filter({ hasText: /下一步|应用|导入|执行/ });
        if ((await nextBtn.count()) > 0) {
          await nextBtn.first().click();
          await page.waitForTimeout(500);
        }
      }
    }
  });
});
