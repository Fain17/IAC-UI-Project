import React, { useState } from 'react';
import axios from 'axios';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setIsLoading(true);
    try {
      // Check if email exists
      const res = await axios.get('http://localhost:8000/auth/check-availability', {
        params: { email }
      });
      if (res.data.available !== false) {
        setIsLoading(false);
        setError('No account found with this email.');
        return;
      }
      // If email exists, send reset link
      await axios.post('http://localhost:8000/auth/request-password-reset', { email });
      setMessage('A password reset link has been sent.');
    } catch {
      setError('Failed to send reset email. Try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '50px auto', background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.05)' }}>
      <h1>Forgot Password</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={e => { setEmail(e.target.value); setError(''); setMessage(''); }}
          placeholder="Enter your email"
          required
        />
        <button type="submit" disabled={isLoading || !email} style={{ display: 'block', marginTop: 16 }}>
          {isLoading ? 'Sending...' : 'Send Reset Link'}
        </button>
        {error && <div style={{ color: 'red', marginTop: '1rem' }}>{error}</div>}
        {message && <div style={{ color: 'green', marginTop: '1rem' }}>{message}</div>}
      </form>
    </div>
  );
};

export default ForgotPasswordPage; 