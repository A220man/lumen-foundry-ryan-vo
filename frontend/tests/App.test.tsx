import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../src/App';
import { useAuthStore } from '../src/stores/authStore';
import { apiClient } from '../src/api/client';

// Mock auth store with mutable state
let mockAuthState = {
  isAuthenticated: false,
  user: null,
  accessToken: null,
  login: vi.fn(),
  logout: vi.fn(),
  checkAuth: vi.fn().mockResolvedValue(undefined),
};

vi.mock('../src/stores/authStore', () => ({
  useAuthStore: () => mockAuthState,
}));

// Mock API client for Dashboard
vi.mock('../src/api/client', () => ({
  apiClient: {
    getGlobalStats: vi.fn(),
  },
}));

const mockApiClient = apiClient as unknown as { getGlobalStats: ReturnType<typeof vi.fn> };

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    // Reset mock auth state
    mockAuthState = {
      isAuthenticated: false,
      user: null,
      accessToken: null,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    };
    // Reset mock api client
    mockApiClient.getGlobalStats.mockResolvedValue({
      data: {
        total_requests: 100,
        total_tokens_generated: 50000,
        avg_latency_ms: 45.5,
        uptime_seconds: 3661,
      },
    });
  });

  it('redirects to login when not authenticated', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    // Wait for auth check to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Should show login page
    expect(screen.getByText('Lumen Foundry')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });

  it('shows dashboard when authenticated', async () => {
    const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QHRlc3QuY29tIiwibmFtZSI6IlRlc3QiLCJleHAiOjk5OTk5OTk5OTksInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ2aWV3ZXIiXX19.fake-signature';
    localStorage.setItem('access_token', mockToken);
    
    // Update mock auth state to authenticated
    mockAuthState = {
      isAuthenticated: true,
      user: { id: '1', email: 'test@test.com', name: 'Test', roles: ['viewer'] },
      accessToken: mockToken,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    };

    render(
      <BrowserRouter>
      <App />
      </BrowserRouter>
    );

    // The PrivateRoute shows "Loading..." first, then dashboard
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
    expect(screen.getByText('Models')).toBeInTheDocument();
    expect(screen.getByText('Inference')).toBeInTheDocument();
  });
});