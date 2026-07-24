import React, { useState } from 'react';
import { Category, Expense } from '../types';
import { X, PlusCircle, DollarSign, Calendar, Tag, FileText } from 'lucide-react';

interface AddExpenseModalProps {
  categories: Category[];
  onClose: () => void;
  onSubmit: (payload: Omit<Expense, 'id' | 'user_id' | 'created_at'>) => Promise<void>;
}

export const AddExpenseModal: React.FC<AddExpenseModalProps> = ({ categories, onClose, onSubmit }) => {
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [type, setType] = useState<'income' | 'expense'>('expense');
  const [categoryId, setCategoryId] = useState<number | undefined>(categories[0]?.id);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await onSubmit({
        title,
        amount: parseFloat(amount),
        type,
        category_id: categoryId ? Number(categoryId) : undefined,
        date,
        description: description || undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to add transaction');
    } finally {
      setLoading(false);
    }
  };

  const filteredCategories = categories.filter(c => c.type === type);

  return (
    <div className="modal-overlay">
      <div className="glass-card modal-content" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PlusCircle size={22} color="var(--primary-accent)" />
            Add New Transaction
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '0.85rem',
            marginBottom: '16px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Type Toggle */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
            <button
              type="button"
              style={{
                padding: '10px',
                borderRadius: '8px',
                border: type === 'expense' ? '2px solid #ef4444' : '1px solid var(--border-color)',
                background: type === 'expense' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
                color: type === 'expense' ? '#f87171' : 'var(--text-muted)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              onClick={() => setType('expense')}
            >
              💸 Expense
            </button>
            <button
              type="button"
              style={{
                padding: '10px',
                borderRadius: '8px',
                border: type === 'income' ? '2px solid #10b981' : '1px solid var(--border-color)',
                background: type === 'income' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
                color: type === 'income' ? '#34d399' : 'var(--text-muted)',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              onClick={() => setType('income')}
            >
              💰 Income
            </button>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Title</label>
            <input
              type="text"
              required
              className="form-input"
              placeholder="e.g. Grocery Shopping, Monthly Salary"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label className="form-label">Amount ($)</label>
              <div style={{ position: 'relative' }}>
                <DollarSign size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
                <input
                  type="number"
                  step="0.01"
                  required
                  className="form-input"
                  style={{ paddingLeft: '34px' }}
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="form-label">Category</label>
              <select
                className="form-select"
                value={categoryId || ''}
                onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
              >
                <option value="">Uncategorized</option>
                {filteredCategories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Date</label>
            <div style={{ position: 'relative' }}>
              <Calendar size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
              <input
                type="date"
                required
                className="form-input"
                style={{ paddingLeft: '34px' }}
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label className="form-label">Description (Optional)</label>
            <input
              type="text"
              className="form-input"
              placeholder="Additional details..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Saving...' : 'Save Transaction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
