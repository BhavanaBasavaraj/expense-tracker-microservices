import React, { useState } from 'react';
import { Expense, Category, AnalyticsSummary, CategoryBreakdown, MonthlyBreakdown } from '../types';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart as PieIcon,
  BarChart3,
  Plus,
  Trash2,
  Download,
  Search,
  Filter,
  Layers,
  Calendar
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend
} from 'recharts';

interface DashboardProps {
  expenses: Expense[];
  categories: Category[];
  analytics: AnalyticsSummary | null;
  categoryBreakdown: CategoryBreakdown;
  monthlyBreakdown: MonthlyBreakdown;
  onAddExpenseClick: () => void;
  onAddCategoryClick: () => void;
  onDeleteExpense: (id: number) => Promise<void>;
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6', '#06b6d4', '#14b8a6'];

export const Dashboard: React.FC<DashboardProps> = ({
  expenses,
  categories,
  analytics,
  categoryBreakdown,
  monthlyBreakdown,
  onAddExpenseClick,
  onAddCategoryClick,
  onDeleteExpense
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<'all' | 'income' | 'expense'>('all');

  // Prepare Pie Chart data
  const pieData = Object.entries(categoryBreakdown).map(([catId, data]) => {
    const catName = categories.find(c => String(c.id) === catId)?.name || `Category ${catId}`;
    return { name: catName, value: data.total };
  });

  // Prepare Bar Chart data
  const barData = Object.entries(monthlyBreakdown).map(([month, data]) => ({
    month,
    Income: data.income,
    Expenses: data.expenses,
  }));

  // Filter expenses
  const filteredExpenses = expenses.filter(exp => {
    const matchesSearch = exp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (exp.description && exp.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedTypeFilter === 'all' || exp.type === selectedTypeFilter;
    return matchesSearch && matchesType;
  });

  // Export to CSV
  const handleExportCSV = () => {
    const headers = ['ID', 'Title', 'Type', 'Amount ($)', 'Date', 'Description'];
    const rows = filteredExpenses.map(e => [
      e.id,
      `"${e.title.replace(/"/g, '""')}"`,
      e.type,
      e.amount,
      e.date,
      `"${(e.description || '').replace(/"/g, '""')}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `expense_report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 20px' }}>
      
      {/* Top Header Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.5px' }}>Financial Overview</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Real-time microservices expense & income telemetry</p>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button className="btn-secondary" onClick={handleExportCSV}>
            <Download size={18} />
            Export CSV
          </button>
          <button className="btn-secondary" onClick={onAddCategoryClick}>
            <Layers size={18} />
            New Category
          </button>
          <button className="btn-primary" onClick={onAddExpenseClick}>
            <Plus size={18} />
            Add Transaction
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>TOTAL INCOME</span>
            <div style={{ padding: '8px', background: 'rgba(16, 185, 129, 0.15)', borderRadius: '10px' }}>
              <TrendingUp size={20} color="#10b981" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#34d399' }}>
            {formatCurrency(analytics?.total_income || 0)}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>TOTAL EXPENSES</span>
            <div style={{ padding: '8px', background: 'rgba(239, 68, 68, 0.15)', borderRadius: '10px' }}>
              <TrendingDown size={20} color="#ef4444" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#f87171' }}>
            {formatCurrency(analytics?.total_expenses || 0)}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>NET BALANCE</span>
            <div style={{ padding: '8px', background: 'rgba(99, 102, 241, 0.15)', borderRadius: '10px' }}>
              <DollarSign size={20} color="#6366f1" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: (analytics?.net_balance || 0) >= 0 ? '#818cf8' : '#f87171' }}>
            {formatCurrency(analytics?.net_balance || 0)}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600 }}>TOTAL TRANSACTIONS</span>
            <div style={{ padding: '8px', background: 'rgba(245, 158, 11, 0.15)', borderRadius: '10px' }}>
              <BarChart3 size={20} color="#f59e0b" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#fbbf24' }}>
            {analytics?.total_transactions || 0}
          </div>
        </div>
      </div>

      {/* Visual Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '36px' }}>
        
        {/* Category Pie Chart */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PieIcon size={20} color="var(--primary-accent)" />
            Category Spending Distribution
          </h3>
          {pieData.length > 0 ? (
            <div style={{ height: '280px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    formatter={(value: any) => formatCurrency(Number(value))}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-subtle)' }}>
              No category data available yet
            </div>
          )}
        </div>

        {/* Monthly Bar Chart */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={20} color="var(--primary-accent)" />
            Monthly Income vs Expenses
          </h3>
          {barData.length > 0 ? (
            <div style={{ height: '280px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="month" stroke="var(--text-subtle)" />
                  <YAxis stroke="var(--text-subtle)" />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                  <Legend />
                  <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Expenses" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-subtle)' }}>
              No monthly activity recorded yet
            </div>
          )}
        </div>
      </div>

      {/* Transactions Table Section */}
      <div className="glass-card" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Transaction History</h3>

          {/* Search & Filter controls */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', width: '100%', maxWidth: '500px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '36px' }}
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div style={{ width: '140px' }}>
              <select
                className="form-select"
                value={selectedTypeFilter}
                onChange={(e) => setSelectedTypeFilter(e.target.value as any)}
              >
                <option value="all">All Types</option>
                <option value="expense">Expenses</option>
                <option value="income">Income</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                <th style={{ padding: '12px 16px' }}>TRANSACTION</th>
                <th style={{ padding: '12px 16px' }}>TYPE</th>
                <th style={{ padding: '12px 16px' }}>CATEGORY</th>
                <th style={{ padding: '12px 16px' }}>DATE</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>AMOUNT</th>
                <th style={{ padding: '12px 16px', textAlign: 'center' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {filteredExpenses.length > 0 ? (
                filteredExpenses.map((exp) => {
                  const categoryName = categories.find(c => c.id === exp.category_id)?.name || 'Uncategorized';
                  return (
                    <tr key={exp.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', transition: 'background 0.2s' }}>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ fontWeight: 600 }}>{exp.title}</div>
                        {exp.description && (
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>{exp.description}</div>
                        )}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span className={`badge ${exp.type === 'income' ? 'badge-income' : 'badge-expense'}`}>
                          {exp.type}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        {categoryName}
                      </td>
                      <td style={{ padding: '14px 16px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        {exp.date}
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right', fontWeight: 700, color: exp.type === 'income' ? '#34d399' : '#f87171' }}>
                        {exp.type === 'income' ? '+' : '-'}{formatCurrency(exp.amount)}
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                        <button
                          className="btn-danger"
                          onClick={() => onDeleteExpense(exp.id)}
                          title="Delete transaction"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-subtle)' }}>
                    No transactions match your search filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
