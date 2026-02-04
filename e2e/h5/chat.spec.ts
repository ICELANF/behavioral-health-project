import { test, expect } from '@playwright/test';
import { mockH5Api } from '../fixtures/api-mocks';

test.beforeEach(async ({ page }) => {
  await mockH5Api(page);
});

test.describe('H5 Chat Page', () => {
  test('should load the chat page', async ({ page }) => {
    await page.goto('/chat');
    await expect(page).toHaveURL('/chat');
  });

  test('should have a message input area', async ({ page }) => {
    await page.goto('/chat');
    const input = page.locator('input, textarea, [contenteditable]').first();
    await expect(input).toBeVisible();
  });

  test('should send a message', async ({ page }) => {
    await page.goto('/chat');
    const input = page.locator('input, textarea, [contenteditable]').first();
    await input.fill('你好');
    // Look for a send button or submit action
    const sendButton = page.locator('button').filter({ hasText: /发送|send/i }).first();
    if (await sendButton.isVisible()) {
      await sendButton.click();
    } else {
      await input.press('Enter');
    }
    // Wait for a response to appear on the page
    await page.waitForTimeout(500);
  });
});
