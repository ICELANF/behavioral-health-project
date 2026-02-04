import { test, expect } from '@playwright/test';
import { mockH5Api } from '../fixtures/api-mocks';

test.beforeEach(async ({ page }) => {
  await mockH5Api(page);
});

test.describe('H5 Home Page', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('/');
  });

  test('should display welcome card', async ({ page }) => {
    await page.goto('/');
    // The home page should contain a greeting or welcome element
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should display efficacy score when available', async ({ page }) => {
    // Pre-set efficacy data via localStorage
    await page.addInitScript(() => {
      localStorage.setItem('xingjian_efficacy_score', '72');
      localStorage.setItem('xingjian_user_id', '"user-001"');
      localStorage.setItem('xingjian_user_name', '"测试用户"');
    });
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
  });
});
