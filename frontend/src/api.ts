import { User, Category, Expense, AnalyticsSummary, CategoryBreakdown, MonthlyBreakdown } from './types';

const API_BASE_URL = 'http://localhost:8000';

function getAuthHeaders(token: string | null): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function registerUser(payload: { email: string; first_name: string; last_name: string; password: string }): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Registration failed');
  }
  return response.json();
}

export async function loginUser(email: string, password: string): Promise<{ access_token: string }> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Login failed');
  }
  return response.json();
}

export async function getProfile(token: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/me?token=${token}`, {
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch profile');
  }
  return response.json();
}

export async function getExpenses(token: string): Promise<Expense[]> {
  const response = await fetch(`${API_BASE_URL}/expenses/`, {
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch expenses');
  }
  return response.json();
}

export async function createExpense(token: string, payload: Omit<Expense, 'id' | 'user_id' | 'created_at'>): Promise<Expense> {
  const response = await fetch(`${API_BASE_URL}/expenses/`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create expense');
  }
  return response.json();
}

export async function deleteExpense(token: string, id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/expenses/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to delete expense');
  }
}

export async function getCategories(token: string): Promise<Category[]> {
  const response = await fetch(`${API_BASE_URL}/categories/`, {
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch categories');
  }
  return response.json();
}

export async function createCategory(token: string, payload: { name: string; type: 'income' | 'expense' }): Promise<Category> {
  const response = await fetch(`${API_BASE_URL}/categories/`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || 'Failed to create category');
  }
  return response.json();
}

export async function getAnalyticsSummary(token: string): Promise<AnalyticsSummary> {
  const response = await fetch(`${API_BASE_URL}/analytics/dashboard`, {
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch analytics summary');
  }
  return response.json();
}

export async function getCategoryBreakdown(token: string): Promise<CategoryBreakdown> {
  const response = await fetch(`${API_BASE_URL}/analytics/by-category`, {
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch category breakdown');
  }
  return response.json();
}

export async function getMonthlyBreakdown(token: string): Promise<MonthlyBreakdown> {
  const response = await fetch(`${API_BASE_URL}/analytics/monthly`, {
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch monthly breakdown');
  }
  return response.json();
}
