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
});
