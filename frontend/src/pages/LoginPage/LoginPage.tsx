import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import tokenManager from '../../utils/tokenManager';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (tokenManager.getToken()) {
      navigate('/home', { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      // Send a single identifier field, backend determines if it's email or username
      const response = await axios.post('http://localhost:8000/auth/login', {
        username_or_email: usernameOrEmail,
        password
      });
      
      // Store tokens and user data using TokenManager
      // This will automatically establish WebSocket connection
      if (response.data.refresh_token) {
        tokenManager.setTokens(
          response.data.access_token,
          response.data.refresh_token,
          {
            id: response.data.user.id,
            username: response.data.user.username,
            email: response.data.user.email
            // Role will be fetched dynamically from /workflow/debug/user-role endpoint
          }
        );
      } else {
        // Fallback for backward compatibility
        tokenManager.setToken(
          response.data.access_token,
          {
            id: response.data.user.id,
            username: response.data.user.username,
            email: response.data.user.email
            // Role will be fetched dynamically from /workflow/debug/user-role endpoint
          }
        );
      }
      
      setIsLoading(false);
      navigate('/home');
    } catch (err: any) {
      console.error('Login error:', err);
      
      // Extract error message from backend response
      let errorMessage = 'Invalid credentials or server error';
      
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
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h1>Login</h1>
      <form onSubmit={handleSubmit} className="login-form">
        <div className="form-group">
        <label htmlFor="usernameOrEmail">Username or Email</label>
        <input
          id="usernameOrEmail"
          type="text"
          value={usernameOrEmail}
          onChange={e => setUsernameOrEmail(e.target.value)}
          placeholder="Enter your username or email"
          required
        />
        </div>
        <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Enter your password"
          required
        />
        </div>
        <button type="submit" disabled={isLoading} className="submit-button">
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
        {error && <div className="error-message">{error}</div>}
      </form>
      <div className="links-container">
        <span>Don't have an account?</span>
        <Link to="/register" className="link">Register</Link>
      </div>
      <div className="links-container">
        <Link to="/forgot-password" className="link">Forgot Password?</Link>
      </div>
    </div>
  );
};

export default LoginPage; 