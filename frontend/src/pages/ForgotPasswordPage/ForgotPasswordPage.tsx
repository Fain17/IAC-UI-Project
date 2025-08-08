import React, { useState } from 'react';
import axios from 'axios';
import './ForgotPasswordPage.css';

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
    } catch (err: any) {
      console.error('Forgot password error:', err);
      
      // Extract error message from backend response
      let errorMessage = 'Failed to send reset email. Try again.';
      
      if (err.response?.data?.detail) {
        // Use the detail message from the backend
        errorMessage = err.response.data.detail;
      } else if (err.response?.data?.message) {
        // Fallback to message field
        errorMessage = err.response.data.message;
      } else if (err.message) {
        // Fallback to error message
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="forgot-password-container">
      <h1>Forgot Password</h1>
      <form onSubmit={handleSubmit} className="forgot-password-form">
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={e => { setEmail(e.target.value); setError(''); setMessage(''); }}
            placeholder="Enter your email"
            required
          />
        </div>
        <button type="submit" disabled={isLoading || !email} className="submit-button">
          {isLoading ? 'Sending...' : 'Send Reset Link'}
        </button>
        {error && <div className="message error-message">{error}</div>}
        {message && <div className="message success-message">{message}</div>}
      </form>
    </div>
  );
};

export default ForgotPasswordPage; 