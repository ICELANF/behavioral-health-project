import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { open: 'never' }]],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'h5',
      testDir: './e2e/h5',
      use: {
        baseURL: 'http://localhost:5173',
        ...devices['iPhone 12'],
      },
    },
    {
      name: 'h5-patient',
      testDir: './e2e/h5-patient',
      use: {
        baseURL: 'http://localhost:5175',
        ...devices['iPhone 12'],
      },
    },
    {
      name: 'admin-portal',
      testDir: './e2e/admin-portal',
      use: {
        baseURL: 'http://localhost:5174',
        ...devices['Desktop Chrome'],
      },
    },
  ],

  /* Uncomment to auto-start dev servers before tests:
  webServer: [
    {
      command: 'npm run dev',
      cwd: './h5',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev',
      cwd: './admin-portal',
      url: 'http://localhost:5174',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev',
      cwd: './h5-patient-app',
      url: 'http://localhost:5175',
      reuseExistingServer: !process.env.CI,
    },
  ],
  */
});
