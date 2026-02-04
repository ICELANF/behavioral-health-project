import { Page } from '@playwright/test';

// ─── H5 App Mocks ───

export async function mockH5Api(page: Page) {
  await page.route('**/api/v1/dispatch', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        reply: '你好！我是行为健康助手，有什么可以帮助你的吗？',
        agent: 'coach',
      }),
    }),
  );

  await page.route('**/api/v1/decompose', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        tasks: [
          { id: '1', title: '每日步行30分钟', status: 'pending' },
          { id: '2', title: '记录饮食日志', status: 'pending' },
        ],
      }),
    }),
  );

  await page.route('**/api/v1/dashboard/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        efficacy_score: 72,
        trend: 'improving',
        recent_tasks: [],
        insights: [],
      }),
    }),
  );

  await page.route('**/api/v1/experts', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ experts: [] }),
    }),
  );

  await page.route('**/api/v1/reports/full**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ report: {} }),
    }),
  );
}

// ─── H5-Patient App Mocks ───

export async function mockPatientApi(page: Page) {
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-patient-token',
        token_type: 'bearer',
        user: {
          id: 'patient-001',
          username: 'testpatient',
          role: 'patient',
        },
      }),
    }),
  );

  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'patient-001',
        username: 'testpatient',
        role: 'patient',
      }),
    }),
  );

  await page.route('**/api/v1/auth/register', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'ok' }),
    }),
  );

  await page.route('**/api/v1/mp/llm/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'healthy' }),
    }),
  );

  await page.route('**/api/v1/mp/chat', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ reply: '你好', session_id: 'sess-1' }),
    }),
  );

  await page.route('**/api/v1/mp/chat/sessions', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ sessions: [] }),
    }),
  );

  await page.route('**/api/v1/mp/device/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ data: [] }),
    }),
  );

  await page.route('**/api/assessment/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ assessments: [], results: [] }),
    }),
  );
}

// ─── Admin Portal Mocks ───

export async function mockAdminApi(page: Page) {
  await page.route('**/auth/login', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        token: 'mock-admin-token',
        refresh_token: 'mock-admin-refresh',
        user: {
          user_id: 'admin-001',
          role: 'ADMIN',
          level: 99,
          certifications: [],
          status: 'active',
          permissions: ['course:read', 'course:write', 'student:read'],
        },
      }),
    }),
  );

  await page.route('**/auth/profile', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          user_id: 'admin-001',
          role: 'ADMIN',
          level: 99,
          certifications: [],
          status: 'active',
          permissions: ['course:read', 'course:write', 'student:read'],
        },
      }),
    }),
  );

  await page.route('**/auth/refresh', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        token: 'mock-admin-token-refreshed',
      }),
    }),
  );

  await page.route('**/api/v1/assessment/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: [] }),
    }),
  );

  // Course-related APIs
  await page.route('**/api/courses**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          items: [
            { id: 'c1', title: '行为健康基础', status: 'published' },
            { id: 'c2', title: '认知行为治疗入门', status: 'draft' },
          ],
          total: 2,
        },
      }),
    }),
  );
}
