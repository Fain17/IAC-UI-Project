import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const LoginPage: React.FC = () => {
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (localStorage.getItem('token')) {
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
      
      // Store token and user info from response
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userEmail', response.data.user.email);
      
      // Store admin status if provided by backend
      if (response.data.user) {
        localStorage.setItem('username', response.data.user.username || '');
        localStorage.setItem('isAdmin', (!!response.data.user.is_admin).toString());
      }
      
      setIsLoading(false);
      navigate('/home');
    } catch (err: any) {
      setError('Invalid credentials or server error');
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '50px auto', background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.05)' }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="usernameOrEmail">Username or Email</label>
        <input
          id="usernameOrEmail"
          type="text"
          value={usernameOrEmail}
          onChange={e => setUsernameOrEmail(e.target.value)}
          placeholder="Enter your username or email"
          required
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Enter your password"
          required
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
        {error && <div style={{ color: 'red', marginTop: '1rem' }}>{error}</div>}
      </form>
      <div style={{ marginTop: '1rem', textAlign: 'center' }}>
        <span>Don't have an account? </span>
        <Link to="/register" style={{ color: '#007bff', textDecoration: 'none' }}>Register</Link>
      </div>
      <div style={{ marginTop: '0.5rem', textAlign: 'center' }}>
        <Link to="/forgot-password" style={{ color: '#007bff', textDecoration: 'none' }}>Forgot Password?</Link>
      </div>
    </div>
  );
};

export default LoginPage; 