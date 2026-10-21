import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Health
  async healthCheck() {
    return this.client.get('/health');
  }

  async readinessCheck() {
    return this.client.get('/health/ready');
  }

  // Models
  async listModels(params?: { page?: number; page_size?: number; active_only?: boolean }) {
    return this.client.get('/models', { params });
  }

  async getModel(id: number) {
    return this.client.get(`/models/${id}`);
  }

  async createModel(data: {
    name: string;
    model_id: string;
    description?: string;
    max_model_len?: number;
    default_temperature?: number;
    default_max_tokens?: number;
    is_active?: boolean;
  }) {
    return this.client.post('/models', data);
  }

  async updateModel(id: number, data: Partial<{
    name: string;
    description: string;
    max_model_len: number;
    default_temperature: number;
    default_max_tokens: number;
    is_active: boolean;
  }>) {
    return this.client.patch(`/models/${id}`, data);
  }

  async deleteModel(id: number) {
    return this.client.delete(`/models/${id}`);
  }

  // Inference
  async runInference(data: {
    model_id: number;
    prompt: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
    top_p?: number;
    top_k?: number;
    stop?: string[];
    presence_penalty?: number;
    frequency_penalty?: number;
  }) {
    return this.client.post('/inference', data);
  }

  async streamInference(
    data: {
      model_id: number;
      prompt: string;
      temperature?: number;
      max_tokens?: number;
      top_p?: number;
      top_k?: number;
      stop?: string[];
      presence_penalty?: number;
      frequency_penalty?: number;
    },
    onToken: (token: string, tokenCount: number) => void,
    onDone: (data: { finish_reason: string; usage: any; latency_ms: number }) => void,
    onError: (error: Error) => void
  ) {
    try {
      const response = await fetch(`${API_BASE_URL}/inference`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ ...data, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('event: token')) {
              const dataLine = line.split('\n').find(l => l.startsWith('data: '));
              if (dataLine) {
                const parsed = JSON.parse(dataLine.slice(6));
                onToken(parsed.token, parsed.token_count);
              }
            } else if (line.startsWith('event: done')) {
              const dataLine = line.split('\n').find(l => l.startsWith('data: '));
              if (dataLine) {
                const parsed = JSON.parse(dataLine.slice(6));
                onDone(parsed);
              }
            }
          }
        }
      }
    } catch (error) {
      onError(error as Error);
    }
  }

  async getModelMetrics(modelId: number) {
    return this.client.get(`/inference/models/${modelId}/metrics`);
  }

  async getGlobalStats() {
    return this.client.get('/inference/stats');
  }
}

export const apiClient = new ApiClient();
