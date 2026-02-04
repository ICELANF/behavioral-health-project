import { test, expect } from '@playwright/test';
import { mockPatientApi } from '../fixtures/api-mocks';
import { injectPatientAuth } from '../fixtures/auth';

test.beforeEach(async ({ page }) => {
  await mockPatientApi(page);
  await injectPatientAuth(page);
});

test.describe('Patient Home Page', () => {
  test('should load the home page when authenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('/');
  });

  test('should not redirect authenticated user to login', async ({ page }) => {
    await page.goto('/');
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('should display page content', async ({ page }) => {
    await page.goto('/');
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
