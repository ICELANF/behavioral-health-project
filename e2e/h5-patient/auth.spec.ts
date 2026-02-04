import { test, expect } from '@playwright/test';
import { mockPatientApi } from '../fixtures/api-mocks';

test.beforeEach(async ({ page }) => {
  await mockPatientApi(page);
});

test.describe('Patient Auth', () => {
  test('should display the login form', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveURL('/login');
    // Login form should have username/password inputs
    const inputs = page.locator('input');
    await expect(inputs.first()).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');
    const registerLink = page.locator('a, button').filter({ hasText: /注册|register/i }).first();
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL(/\/register/);
    }
  });

  test('should redirect unauthenticated user to login', async ({ page }) => {
    // Try to access a protected route without auth
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should preserve redirect path in query param', async ({ page }) => {
    await page.goto('/data-input');
    await expect(page).toHaveURL(/\/login\?redirect/);
  });
});
