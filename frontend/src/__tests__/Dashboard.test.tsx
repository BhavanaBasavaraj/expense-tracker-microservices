import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Dashboard } from '../components/Dashboard';
import { Expense, Category, AnalyticsSummary } from '../types';

// Mock Recharts ResponsiveContainer to avoid SVG dimensions error in jsdom
vi.mock('recharts', async () => {
  const original = await vi.importActual('recharts');
  return {
    ...original as any,
    ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  };
});

describe('Dashboard Component', () => {
  const mockExpenses: Expense[] = [
    { id: 1, user_id: 1, title: 'Salary', amount: 5000, type: 'income', date: '2026-07-01', category_id: 1 },
    { id: 2, user_id: 1, title: 'Rent', amount: 1500, type: 'expense', date: '2026-07-02', category_id: 2 },
  ];

  const mockCategories: Category[] = [
    { id: 1, user_id: 1, name: 'Paycheck', type: 'income' },
    { id: 2, user_id: 1, name: 'Housing', type: 'expense' },
  ];

  const mockAnalytics: AnalyticsSummary = {
    total_income: 5000,
    total_expenses: 1500,
    net_balance: 3500,
    total_transactions: 2,
  };

  it('renders KPI cards and transaction history correctly', () => {
    render(
      <Dashboard
        expenses={mockExpenses}
        categories={mockCategories}
        analytics={mockAnalytics}
        categoryBreakdown={{ '2': { total: 1500, count: 1 } }}
        monthlyBreakdown={{ '2026-07': { income: 5000, expenses: 1500 } }}
        onAddExpenseClick={vi.fn()}
        onAddCategoryClick={vi.fn()}
        onDeleteExpense={vi.fn()}
      />
    );

    expect(screen.getByText('Financial Overview')).toBeTruthy();
    expect(screen.getByText('$5,000.00')).toBeTruthy();
    expect(screen.getByText('$1,500.00')).toBeTruthy();
    expect(screen.getByText('$3,500.00')).toBeTruthy();
    expect(screen.getByText('Salary')).toBeTruthy();
    expect(screen.getByText('Rent')).toBeTruthy();
  });
});
