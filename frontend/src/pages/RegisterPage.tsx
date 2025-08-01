import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { checkFirstUser } from '../api';

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
    if (localStorage.getItem('token')) {
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
        localStorage.clear();
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed');
      setIsLoading(false);
    }
  };

  if (checkingFirstUser) {
    return (
      <div style={{ maxWidth: 400, margin: '50px auto', background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.05)' }}>
        <h1>Register</h1>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div>Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 400, margin: '50px auto', background: '#fff', padding: '2rem', borderRadius: 8, boxShadow: '0 0 10px rgba(0,0,0,0.05)' }}>
      <h1>Register</h1>
      {isFirstUser && (
        <div style={{ 
          background: '#d4edda', 
          color: '#155724', 
          padding: '1rem', 
          borderRadius: '5px', 
          marginBottom: '1rem',
          border: '1px solid #c3e6cb'
        }}>
          <strong>🎉 Welcome!</strong> You're the first user to register. You'll be automatically granted admin privileges.
        </div>
      )}
      <form onSubmit={handleSubmit}>
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
        {checkingUsername && <span style={{ color: '#888', fontSize: '0.95em' }}>Checking...</span>}
        {usernameAvailable === false && <span style={{ color: 'red', fontSize: '0.95em' }}>Username is taken</span>}
        {usernameAvailable === true && <span style={{ color: 'green', fontSize: '0.95em' }}>Username is available</span>}

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
        {checkingEmail && <span style={{ color: '#888', fontSize: '0.95em' }}>Checking...</span>}
        {emailAvailable === false && <span style={{ color: 'red', fontSize: '0.95em' }}>Email is taken</span>}
        {emailAvailable === true && <span style={{ color: 'green', fontSize: '0.95em' }}>Email is available</span>}

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
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Creating account...' : 'Register'}
        </button>
        {error && <div style={{ color: 'red', marginTop: '1rem' }}>{error}</div>}
      </form>
      <div style={{ marginTop: '1rem', textAlign: 'center' }}>
        <span>Already have an account? </span>
        <Link to="/login" style={{ color: '#007bff', textDecoration: 'none' }}>Login</Link>
      </div>
      {success && (
        <div style={{
          marginTop: '2rem',
          background: '#d4edda',
          color: '#155724',
          border: '1px solid #c3e6cb',
          borderRadius: '5px',
          padding: '1rem',
          textAlign: 'center',
          fontWeight: 500
        }}>
          Registered successfully! Redirecting to login...
        </div>
      )}
    </div>
  );
};

export default RegisterPage; 