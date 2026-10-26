import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../src/components/Dashboard';
import { apiClient } from '../src/api/client';

vi.mock('../src/api/client', () => ({
  apiClient: {
    getGlobalStats: vi.fn(),
  },
}));

const mockApiClient = apiClient as any;

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiClient.getGlobalStats.mockImplementation(() => new Promise(() => {}));
    render(<Dashboard />);
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('renders stats when loaded', async () => {
    mockApiClient.getGlobalStats.mockResolvedValue({
      data: {
        total_requests: 100,
        total_tokens_generated: 50000,
        avg_latency_ms: 45.5,
        uptime_seconds: 3661,
      },
    });

    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument(); // total_requests
      expect(screen.getByText('50,000')).toBeInTheDocument(); // total_tokens_generated
      expect(screen.getByText('45.5 ms')).toBeInTheDocument(); // avg_latency_ms
      expect(screen.getByText('1h 1m 1s')).toBeInTheDocument(); // uptime
    });
  });

  it('renders error on failure', async () => {
    mockApiClient.getGlobalStats.mockRejectedValue(new Error('Failed'));
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load statistics')).toBeInTheDocument();
    });
  });
});
