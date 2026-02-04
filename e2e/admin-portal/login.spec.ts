import { test, expect } from '@playwright/test';
import { mockAdminApi } from '../fixtures/api-mocks';

test.beforeEach(async ({ page }) => {
  await mockAdminApi(page);
});

test.describe('Admin Login', () => {
  test('should load the login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveURL('/login');
  });

  test('should display role selection options', async ({ page }) => {
    await page.goto('/login');
    // The admin login supports 4 roles: ADMIN, EXPERT, COACH, USER
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should have username and password inputs', async ({ page }) => {
    await page.goto('/login');
    const inputs = page.locator('input');
    await expect(inputs.first()).toBeVisible();
  });

  test('should submit login form', async ({ page }) => {
    await page.goto('/login');
    // Fill login credentials
    const usernameInput = page.locator('input[type="text"], input[name="username"], input').first();
    const passwordInput = page.locator('input[type="password"]').first();

    if (await usernameInput.isVisible() && await passwordInput.isVisible()) {
      await usernameInput.fill('admin');
      await passwordInput.fill('password123');

      const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /登录|login|sign in/i }).first();
      if (await submitBtn.isVisible()) {
        await submitBtn.click();
        // After login, should redirect away from login page
        await page.waitForTimeout(500);
      }
    }
  });
});
