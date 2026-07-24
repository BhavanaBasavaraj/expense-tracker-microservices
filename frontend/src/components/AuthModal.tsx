import React, { useState } from 'react';
import { loginUser, registerUser } from '../api';
import { Lock, Mail, User as UserIcon, ArrowRight, ShieldCheck } from 'lucide-react';

interface AuthModalProps {
  onSuccess: (token: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        const res = await loginUser(email, password);
        onSuccess(res.access_token);
      } else {
        await registerUser({
          email,
          first_name: firstName,
          last_name: lastName,
          password,
        });
        // Auto login after registration
        const res = await loginUser(email, password);
        onSuccess(res.access_token);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="glass-card modal-content" style={{ padding: '32px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'var(--primary-gradient)',
            borderRadius: '12px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '12px',
            boxShadow: '0 4px 16px rgba(99, 102, 241, 0.4)'
          }}>
            <ShieldCheck size={26} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 700 }}>Expense Tracker Microservices</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>
            {isLogin ? 'Sign in to access your financial dashboard' : 'Create an account to track your wealth'}
          </p>
        </div>

        {/* Tab Toggle */}
        <div style={{
          display: 'flex',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '10px',
          padding: '4px',
          marginBottom: '20px'
        }}>
          <button
            type="button"
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '8px',
              border: 'none',
              background: isLogin ? 'var(--primary-gradient)' : 'transparent',
              color: isLogin ? '#fff' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onClick={() => { setIsLogin(true); setError(null); }}
          >
            Sign In
          </button>
          <button
            type="button"
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: '8px',
              border: 'none',
              background: !isLogin ? 'var(--primary-gradient)' : 'transparent',
              color: !isLogin ? '#fff' : 'var(--text-muted)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onClick={() => { setIsLogin(false); setError(null); }}
          >
            Register
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
          {!isLogin && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div>
                <label className="form-label">First Name</label>
                <div style={{ position: 'relative' }}>
                  <UserIcon size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
                  <input
                    type="text"
                    required
                    className="form-input"
                    style={{ paddingLeft: '36px' }}
                    placeholder="John"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="form-label">Last Name</label>
                <div style={{ position: 'relative' }}>
                  <UserIcon size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
                  <input
                    type="text"
                    required
                    className="form-input"
                    style={{ paddingLeft: '36px' }}
                    placeholder="Doe"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          <div style={{ marginBottom: '16px' }}>
            <label className="form-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
              <input
                type="email"
                required
                className="form-input"
                style={{ paddingLeft: '36px' }}
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-subtle)' }} />
              <input
                type="password"
                required
                className="form-input"
                style={{ paddingLeft: '36px' }}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
          >
            {loading ? 'Processing...' : isLogin ? 'Sign In to Account' : 'Create Account'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
};
