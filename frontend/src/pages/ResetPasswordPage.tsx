import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage('');
    setError('');
    if (!token) {
      setError('Invalid or missing reset token.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setIsLoading(true);
    try {
      await axios.post('http://localhost:8000/auth/reset-password', {
        token,
        new_password: password
      });
      setMessage('Password reset successfully! Redirecting to login...');
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to reset password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '50px auto', background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.05)' }}>
      <h1>Reset Password</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="password">New Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Enter new password"
          required
        />
        <label htmlFor="confirmPassword">Confirm New Password</label>
        <input
          id="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={e => setConfirmPassword(e.target.value)}
          placeholder="Confirm new password"
          required
        />
        <button type="submit" disabled={isLoading} style={{ marginTop: 16 }}>
          {isLoading ? 'Resetting...' : 'Reset Password'}
        </button>
        {error && <div style={{ color: 'red', marginTop: '1rem' }}>{error}</div>}
        {message && <div style={{ color: 'green', marginTop: '1rem' }}>{message}</div>}
      </form>
    </div>
  );
};

export default ResetPasswordPage; 