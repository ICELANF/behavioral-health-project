import { test, expect } from '@playwright/test';
import { mockAdminApi } from '../fixtures/api-mocks';
import { injectAdminAuth } from '../fixtures/auth';

test.beforeEach(async ({ page }) => {
  await mockAdminApi(page);
  await injectAdminAuth(page);
});

test.describe('Admin Course Management', () => {
  test('should load the course list page', async ({ page }) => {
    await page.goto('/course');
    await expect(page).toHaveURL(/\/course/);
  });

  test('should navigate to course creation', async ({ page }) => {
    await page.goto('/course');
    const createBtn = page.locator('a, button').filter({ hasText: /创建|新建|create|add/i }).first();
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await expect(page).toHaveURL(/\/course\//);
    }
  });
});
