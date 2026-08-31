import { beforeEach, describe, expect, test, vi } from 'vitest';

const posthogMock = vi.hoisted(() => ({
  init: vi.fn(),
}));

const renderMock = vi.hoisted(() => vi.fn());

vi.mock('posthog-js', () => ({
  default: posthogMock,
}));

vi.mock('@sentry/react', () => ({
  init: vi.fn(),
}));

vi.mock('react-dom/client', () => ({
  createRoot: vi.fn(() => ({
    render: renderMock,
  })),
}));

vi.mock('./app/App.tsx', () => ({
  default: function MockApp() {
    return null;
  },
}));

describe('PostHog initialization', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubEnv('VITE_POSTHOG_KEY', 'test-posthog-key');
    document.body.innerHTML = '<div id="root"></div>';
    posthogMock.init.mockClear();
    renderMock.mockClear();
  });

  test('configures PostHog for manual product analytics without automatic DOM or performance capture', async () => {
    await import('./main');

    expect(posthogMock.init).toHaveBeenCalledWith('test-posthog-key', {
      api_host: 'https://us.i.posthog.com',
      person_profiles: 'identified_only',
      capture_pageview: false,
      autocapture: false,
      rageclick: false,
      capture_performance: false,
    });
  });
});
