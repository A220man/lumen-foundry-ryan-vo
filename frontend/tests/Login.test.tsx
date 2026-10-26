import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../src/components/Login';
import { useAuthStore } from '../src/stores/authStore';

vi.mock('../src/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('../src/api/client', () => ({
  apiClient: {
    listModels: vi.fn().mockResolvedValue({ data: { items: [] } }),
  },
}));

const mockUseAuthStore = useAuthStore as vi.Mock;

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      login: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    });
  });

  it('renders login form', () => {
    renderWithRouter(<Login />);
    expect(screen.getByText('Lumen Foundry')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByText(/Continue as Demo User/)).toBeInTheDocument();
  });

  it('shows error on failed login', async () => {
    const mockLogin = vi.fn().mockImplementation(() => {
      throw new Error('Failed');
    });
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      login: mockLogin,
      logout: vi.fn(),
      checkAuth: vi.fn().mockResolvedValue(undefined),
    });

    renderWithRouter(<Login />);
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByText('Sign In'));

    await waitFor(() => {
      expect(screen.getByText('Login failed. Please try again.')).toBeInTheDocument();
    });
  });
});
