export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  created_at?: string;
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  type: 'income' | 'expense';
  created_at?: string;
}

export interface Expense {
  id: number;
  user_id: number;
  category_id?: number;
  title: string;
  amount: number;
  type: 'income' | 'expense';
  date: string;
  description?: string;
  created_at?: string;
}

export interface AnalyticsSummary {
  total_income: number;
  total_expenses: number;
  net_balance: number;
  total_transactions: number;
}

export interface CategoryBreakdownItem {
  total: number;
  count: number;
}

export type CategoryBreakdown = Record<string, CategoryBreakdownItem>;

export interface MonthlyBreakdownItem {
  income: number;
  expenses: number;
}

export type MonthlyBreakdown = Record<string, MonthlyBreakdownItem>;
