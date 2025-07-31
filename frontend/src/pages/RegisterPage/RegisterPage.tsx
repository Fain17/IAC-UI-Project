import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { checkFirstUser } from '../../api';
import tokenManager from '../../utils/tokenManager';
import './RegisterPage.css';

const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFirstUser, setIsFirstUser] = useState(false);
  const [checkingFirstUser, setCheckingFirstUser] = useState(true);
  const [success, setSuccess] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null);
  const [emailAvailable, setEmailAvailable] = useState<boolean | null>(null);
  const [checkingUsername, setCheckingUsername] = useState(false);
  const [checkingEmail, setCheckingEmail] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (tokenManager.getToken()) {
      navigate('/home', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    const checkFirstUserStatus = async () => {
      try {
        const response = await checkFirstUser();
        setIsFirstUser(response.data.is_first_user || false);
      } catch (err) {
        setIsFirstUser(false);
      } finally {
        setCheckingFirstUser(false);
      }
    };
    checkFirstUserStatus();
  }, []);

  // Username availability check
  useEffect(() => {
    if (!formData.username) {
      setUsernameAvailable(null);
      return;
    }
    setCheckingUsername(true);
    const timeout = setTimeout(async () => {
      try {
        const res = await axios.get('http://localhost:8000/auth/check-availability', {
          params: { username: formData.username }
        });
        setUsernameAvailable(res.data.available);
      } catch {
        setUsernameAvailable(null);
      } finally {
        setCheckingUsername(false);
      }
    }, 500);
    return () => clearTimeout(timeout);
  }, [formData.username]);

  // Email availability check
  useEffect(() => {
    if (!formData.email) {
      setEmailAvailable(null);
      return;
    }
    setCheckingEmail(true);
    const timeout = setTimeout(async () => {
      try {
        const res = await axios.get('http://localhost:8000/auth/check-availability', {
          params: { email: formData.email }
        });
        setEmailAvailable(res.data.available);
      } catch {
        setEmailAvailable(null);
      } finally {
        setCheckingEmail(false);
      }
    }, 500);
    return () => clearTimeout(timeout);
  }, [formData.email]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess(false);
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    if (usernameAvailable === false) {
      setError('Username is already taken');
      setIsLoading(false);
      return;
    }
    if (emailAvailable === false) {
      setError('Email is already taken');
      setIsLoading(false);
      return;
    }
    try {
      const response = await axios.post('http://localhost:8000/auth/register', {
        username: formData.username,
        email: formData.email,
        password: formData.password
      });
      setIsLoading(false);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed');
      setIsLoading(false);
    }
  };

  if (checkingFirstUser) {
    return (
      <div className="register-container">
        <h1>Register</h1>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div>Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="register-container">
      <h1>Register</h1>
      {isFirstUser && (
        <div className="first-user-banner">
          <strong>🎉 Welcome!</strong> You're the first user to register. You'll be automatically granted admin privileges.
        </div>
      )}
      <form onSubmit={handleSubmit} className="register-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            type="text"
            value={formData.username}
            onChange={handleChange}
            placeholder="Enter your username"
            required
          />
          {checkingUsername && <span className="availability-status checking">Checking...</span>}
          {usernameAvailable === false && <span className="availability-status unavailable">Username is taken</span>}
          {usernameAvailable === true && <span className="availability-status available">Username is available</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Enter your email"
            required
          />
          {checkingEmail && <span className="availability-status checking">Checking...</span>}
          {emailAvailable === false && <span className="availability-status unavailable">Email is taken</span>}
          {emailAvailable === true && <span className="availability-status available">Email is available</span>}
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Enter your password"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your password"
            required
          />
        </div>

        <button type="submit" disabled={isLoading} className="submit-button">
          {isLoading ? 'Creating account...' : 'Register'}
        </button>
        {error && <div className="error-message">{error}</div>}
      </form>
      <div className="links-container">
        <span>Already have an account?</span>
        <Link to="/login" className="link">Login</Link>
      </div>
      {success && (
        <div className="success-message">
          Registered successfully! Redirecting to login...
        </div>
      )}
    </div>
  );
};

export default RegisterPage; 