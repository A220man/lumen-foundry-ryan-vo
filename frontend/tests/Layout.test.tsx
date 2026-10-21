import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Layout from '../src/components/Layout';
import { useAuthStore } from '../src/stores/authStore';

vi.mock('../src/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockUseAuthStore = useAuthStore as vi.Mock;

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', email: 'test@test.com', name: 'Test User', roles: ['viewer'] },
      accessToken: 'token',
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    });
  });

  it('renders header with brand and navigation', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    );
    expect(screen.getByText('Lumen Foundry')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Models')).toBeInTheDocument();
    expect(screen.getByText('Inference')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });
});
