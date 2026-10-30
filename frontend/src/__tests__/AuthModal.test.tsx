import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AuthModal } from '../components/AuthModal';

describe('AuthModal Component', () => {
  it('renders Sign In tab by default', () => {
    const handleSuccess = vi.fn();
    render(<AuthModal onSuccess={handleSuccess} />);

    expect(screen.getByText('Expense Tracker Microservices')).toBeTruthy();
    expect(screen.getByPlaceholderText('you@example.com')).toBeTruthy();
    expect(screen.getByPlaceholderText('••••••••')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Sign In to Account/i })).toBeTruthy();
  });

  it('switches to Register tab when Register button is clicked', () => {
    const handleSuccess = vi.fn();
    render(<AuthModal onSuccess={handleSuccess} />);

    const registerTab = screen.getByRole('button', { name: 'Register' });
    fireEvent.click(registerTab);

    expect(screen.getByPlaceholderText('John')).toBeTruthy();
    expect(screen.getByPlaceholderText('Doe')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeTruthy();
  });

  it('asks for at least 8 characters only when registering', () => {
    render(<AuthModal onSuccess={vi.fn()} />);
    const loginPassword = screen.getByPlaceholderText('••••••••') as HTMLInputElement;
    expect(loginPassword.minLength).toBeLessThanOrEqual(0); // sign in: do not block existing users

    fireEvent.click(screen.getByRole('button', { name: 'Register' }));
    const registerPassword = screen.getByPlaceholderText('At least 8 characters') as HTMLInputElement;
    expect(registerPassword.minLength).toBe(8);
    expect(registerPassword.maxLength).toBe(72);
  });
});
