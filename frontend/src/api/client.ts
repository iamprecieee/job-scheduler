const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || 'supersecret-dev-token';

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function fetchWrapper<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Admin-Token': ADMIN_TOKEN,
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = 'An error occurred while fetching data.';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // If response is not JSON, fall back to default message
    }
    throw new ApiError(response.status, errorMessage);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit) => 
    fetchWrapper<T>(endpoint, { ...options, method: 'GET' }),
    
  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) => 
    fetchWrapper<T>(endpoint, { 
      ...options, 
      method: 'POST', 
      body: body ? JSON.stringify(body) : undefined 
    }),
    
  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) => 
    fetchWrapper<T>(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: body ? JSON.stringify(body) : undefined 
    }),
    
  delete: <T>(endpoint: string, options?: RequestInit) => 
    fetchWrapper<T>(endpoint, { ...options, method: 'DELETE' }),
};

// Types for the API responses
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface Job {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  result?: Record<string, unknown>;
  priority: number;
  status: JobStatus;
  retry_count: number;
  scheduled_at: string | null;
  recurring_interval: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export interface DeadLetterEntry {
  id: string;
  job_id: string;
  failure_reason: string;
  entered_at: string;
  retry_attempted_at: string | null;
}

export interface DLQListResponse {
  entries: DeadLetterEntry[];
  total: number;
}

export interface CreateJobRequest {
  type: string;
  payload: Record<string, unknown>;
  priority?: number;
  scheduled_at?: string;
  recurring_interval?: string;
  dependencies?: string[];
}

export interface SentEmail {
  id: string;
  job_id: string;
  recipient: string;
  subject: string;
  body: string;
  sent_at: string;
}

export interface SentEmailListResponse {
  emails: SentEmail[];
  total: number;
}

