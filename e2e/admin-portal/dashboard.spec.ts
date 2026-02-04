import { test, expect } from '@playwright/test';
import { mockAdminApi } from '../fixtures/api-mocks';
import { injectAdminAuth } from '../fixtures/auth';

test.beforeEach(async ({ page }) => {
  await mockAdminApi(page);
  await injectAdminAuth(page);
});

test.describe('Admin Dashboard', () => {
  test('should load the dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should display dashboard content', async ({ page }) => {
    await page.goto('/dashboard');
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
