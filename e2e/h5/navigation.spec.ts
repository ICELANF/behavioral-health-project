import { test, expect } from '@playwright/test';
import { mockH5Api } from '../fixtures/api-mocks';

test.beforeEach(async ({ page }) => {
  await mockH5Api(page);
});

test.describe('H5 Navigation', () => {
  const routes = ['/', '/chat', '/tasks', '/dashboard', '/profile'];

  for (const route of routes) {
    test(`should navigate to ${route}`, async ({ page }) => {
      await page.goto(route);
      await expect(page).toHaveURL(route);
    });
  }

  test('should redirect unknown routes to home', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await expect(page).toHaveURL('/');
  });
});
