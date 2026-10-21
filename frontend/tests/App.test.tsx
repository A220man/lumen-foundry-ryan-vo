import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../src/App';
import { useAuthStore } from '../src/stores/authStore';

// Mock auth store
vi.mock('../src/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockUseAuthStore = useAuthStore as vi.Mock;

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('redirects to login when not authenticated', () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText('Lumen Foundry')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });

  it('shows dashboard when authenticated', async () => {
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', email: 'test@test.com', name: 'Test', roles: ['viewer'] },
      accessToken: 'token',
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
    expect(screen.getByText('Models')).toBeInTheDocument();
    expect(screen.getByText('Inference')).toBeInTheDocument();
  });
});
