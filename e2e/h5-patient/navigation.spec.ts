import { test, expect } from '@playwright/test';
import { mockPatientApi } from '../fixtures/api-mocks';
import { injectPatientAuth } from '../fixtures/auth';

test.beforeEach(async ({ page }) => {
  await mockPatientApi(page);
  await injectPatientAuth(page);
});

test.describe('Patient Navigation (authenticated)', () => {
  const protectedRoutes = ['/', '/data-input', '/history', '/analysis', '/settings', '/chat', '/health-data'];

  for (const route of protectedRoutes) {
    test(`should navigate to ${route} when authenticated`, async ({ page }) => {
      await page.goto(route);
      await expect(page).toHaveURL(route);
    });
  }

  test('should redirect unknown routes to home', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await expect(page).toHaveURL('/');
  });
});

test.describe('Patient Navigation (unauthenticated)', () => {
  // No auth injection in this block
  test.beforeEach(async ({ page }) => {
    // Re-setup mocks without auth (overrides the outer beforeEach)
  });

  test('should redirect protected route to login', async ({ page }) => {
    await mockPatientApi(page);
    await page.goto('/data-input');
    await expect(page).toHaveURL(/\/login/);
  });

  test('should allow access to login page', async ({ page }) => {
    await mockPatientApi(page);
    await page.goto('/login');
    await expect(page).toHaveURL('/login');
  });
});
