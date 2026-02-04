import { Page } from '@playwright/test';

/**
 * Inject authentication tokens for the h5-patient app.
 *
 * The patient app uses a storage wrapper that JSON.stringify's values before
 * writing to localStorage, so the stored value for a string "token" is
 * actually the JSON string '"token"'.
 */
export async function injectPatientAuth(page: Page) {
  await page.addInitScript(() => {
    // storage.set wraps with JSON.stringify, so we replicate that here
    localStorage.setItem(
      'behavioral_health_access_token',
      JSON.stringify('mock-patient-token'),
    );
    localStorage.setItem(
      'behavioral_health_user_info',
      JSON.stringify({
        id: 'patient-001',
        username: 'testpatient',
        role: 'patient',
      }),
    );
  });
}

/**
 * Inject authentication tokens for the admin portal.
 *
 * The admin portal stores tokens as plain strings (no JSON.stringify wrapper).
 */
export async function injectAdminAuth(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem('admin_token', 'mock-admin-token');
    localStorage.setItem('admin_refresh_token', 'mock-admin-refresh');
  });
}
