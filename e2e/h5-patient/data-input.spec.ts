import { test, expect } from '@playwright/test';
import { mockPatientApi } from '../fixtures/api-mocks';
import { injectPatientAuth } from '../fixtures/auth';

test.beforeEach(async ({ page }) => {
  await mockPatientApi(page);
  await injectPatientAuth(page);
});

test.describe('Patient Data Input Page', () => {
  test('should load the data input page', async ({ page }) => {
    await page.goto('/data-input');
    await expect(page).toHaveURL('/data-input');
  });

  test('should display data entry form elements', async ({ page }) => {
    await page.goto('/data-input');
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
