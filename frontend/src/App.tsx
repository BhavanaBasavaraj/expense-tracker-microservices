import React, { useState, useEffect } from 'react';
import { User, Expense, Category, AnalyticsSummary, CategoryBreakdown, MonthlyBreakdown } from './types';
import {
  getProfile,
  getExpenses,
  createExpense,
  deleteExpense,
  getCategories,
  createCategory,
  getAnalyticsSummary,
  getCategoryBreakdown,
  getMonthlyBreakdown
} from './api';
import { AuthModal } from './components/AuthModal';
import { Dashboard } from './components/Dashboard';
import { AddExpenseModal } from './components/AddExpenseModal';
import { AddCategoryModal } from './components/AddCategoryModal';
import { Shield, LogOut, Wallet, User as UserIcon } from 'lucide-react';

export const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [user, setUser] = useState<User | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [categoryBreakdown, setCategoryBreakdown] = useState<CategoryBreakdown>({});
  const [monthlyBreakdown, setMonthlyBreakdown] = useState<MonthlyBreakdown>({});
  
  const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false);
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchAllData = async (currentToken: string) => {
    setLoading(true);
    try {
      const [u, exp, cat, summary, catBreakdown, monthBreakdown] = await Promise.all([
        getProfile(currentToken),
        getExpenses(currentToken),
        getCategories(currentToken),
        getAnalyticsSummary(currentToken),
        getCategoryBreakdown(currentToken),
        getMonthlyBreakdown(currentToken)
      ]);
      setUser(u);
      setExpenses(exp);
      setCategories(cat);
      setAnalytics(summary);
      setCategoryBreakdown(catBreakdown);
      setMonthlyBreakdown(monthBreakdown);
    } catch (err) {
      console.error('Data fetch error:', err);
      // Logout on auth failure
      handleLogout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchAllData(token);
    }
  }, [token]);

  const handleAuthSuccess = (newToken: string) => {
    localStorage.setItem('access_token', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
    setExpenses([]);
    setCategories([]);
    setAnalytics(null);
  };

  const handleCreateExpense = async (payload: Omit<Expense, 'id' | 'user_id' | 'created_at'>) => {
    if (!token) return;
    await createExpense(token, payload);
    await fetchAllData(token);
  };

  const handleDeleteExpense = async (id: number) => {
    if (!token) return;
    await deleteExpense(token, id);
    await fetchAllData(token);
  };

  const handleCreateCategory = async (payload: { name: string; type: 'income' | 'expense' }) => {
    if (!token) return;
    await createCategory(token, payload);
    await fetchAllData(token);
  };

  if (!token) {
    return <AuthModal onSuccess={handleAuthSuccess} />;
  }

  return (
    <div style={{ minHeight: '100vh' }}>
      
      {/* Top Navbar */}
      <header style={{
        background: 'rgba(15, 23, 42, 0.8)',
        borderBottom: '1px solid var(--border-color)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '16px 24px'
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              background: 'var(--primary-gradient)',
              borderRadius: '10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)'
            }}>
              <Wallet size={22} color="#fff" />
            </div>
            <div>
              <span style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.3px' }}>ExpenseTracker</span>
              <span style={{ fontSize: '0.75rem', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', padding: '2px 8px', borderRadius: '12px', marginLeft: '8px', fontWeight: 600 }}>
                MICROSERVICES
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            {user && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                <UserIcon size={16} />
                <span>{user.first_name} {user.last_name}</span>
              </div>
            )}
            <button className="btn-secondary" onClick={handleLogout} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Dashboard view */}
      <Dashboard
        expenses={expenses}
        categories={categories}
        analytics={analytics}
        categoryBreakdown={categoryBreakdown}
        monthlyBreakdown={monthlyBreakdown}
        onAddExpenseClick={() => setIsAddExpenseOpen(true)}
        onAddCategoryClick={() => setIsAddCategoryOpen(true)}
        onDeleteExpense={handleDeleteExpense}
      />

      {/* Modals */}
      {isAddExpenseOpen && (
        <AddExpenseModal
          categories={categories}
          onClose={() => setIsAddExpenseOpen(false)}
          onSubmit={handleCreateExpense}
        />
      )}

      {isAddCategoryOpen && (
        <AddCategoryModal
          onClose={() => setIsAddCategoryOpen(false)}
          onSubmit={handleCreateCategory}
        />
      )}

    </div>
  );
};
