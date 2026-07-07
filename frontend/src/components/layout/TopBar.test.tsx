import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppProvider } from '../../context/AppContext';
import { TopBar } from './TopBar';

// Render TopBar inside the real AppProvider, with all backend fetches failing so
// the UI falls back to sample data (liveConnected = false).
function renderTopBar() {
  return render(
    <AppProvider>
      <TopBar setMobileOpen={() => {}} />
    </AppProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  // Every fetch fails -> offline/sample mode.
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })) as any);
});

afterEach(() => vi.unstubAllGlobals());

describe('TopBar', () => {
  it('shows Sample Data when the backend is offline', async () => {
    renderTopBar();
    await waitFor(() => expect(screen.getByText('Sample Data')).toBeInTheDocument());
  });

  it('defaults to Mock-Safe and toggles to Real Actions on click', async () => {
    const user = userEvent.setup();
    renderTopBar();
    // Default safety mode
    expect(screen.getByText('Mock-Safe')).toBeInTheDocument();
    // Clicking the badge flips it to Real Actions
    await user.click(screen.getByText('Mock-Safe'));
    await waitFor(() => expect(screen.getByText('Real Actions')).toBeInTheDocument());
    // And the choice persists to localStorage
    expect(JSON.parse(localStorage.getItem('evolveagent-safety') || '{}').mockSafe).toBe(false);
  });

  it('renders the command-palette trigger', () => {
    renderTopBar();
    expect(screen.getByText(/Search or/i)).toBeInTheDocument();
  });
});
