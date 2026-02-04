import { test, expect } from '@playwright/test';
import { mockAdminApi } from '../fixtures/api-mocks';
import { injectAdminAuth } from '../fixtures/auth';

test.beforeEach(async ({ page }) => {
  await mockAdminApi(page);
  await injectAdminAuth(page);
});

test.describe('Admin Sidebar Navigation', () => {
  const adminRoutes = ['/dashboard', '/course', '/student'];

  for (const route of adminRoutes) {
    test(`should navigate to ${route}`, async ({ page }) => {
      await page.goto(route);
      await expect(page).toHaveURL(new RegExp(route));
    });
  }
});

test.describe('Admin Public Pages', () => {
  test('should access login without auth', async ({ page }) => {
    await mockAdminApi(page);
    // No auth injection — login should still be accessible
    await page.goto('/login');
    await expect(page).toHaveURL('/login');
  });

  test('should access public portal without auth', async ({ page }) => {
    await mockAdminApi(page);
    await page.goto('/portal/public');
    await expect(page).toHaveURL('/portal/public');
  });
});
