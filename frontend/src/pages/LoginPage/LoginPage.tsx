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
      if (response.data.refresh_token) {
        tokenManager.setTokens(
          response.data.access_token,
          response.data.refresh_token,
          {
            username: response.data.user.username,
            email: response.data.user.email,
            isAdmin: !!response.data.user.is_admin
          }
        );
      } else {
        // Fallback for backward compatibility
        tokenManager.setToken(
          response.data.access_token,
          {
            username: response.data.user.username,
            email: response.data.user.email,
            isAdmin: !!response.data.user.is_admin
          }
        );
      }
      
      setIsLoading(false);
      navigate('/home');
    } catch (err: any) {
      setError('Invalid credentials or server error');
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