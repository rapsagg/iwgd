import React, { useState } from 'react';
import authService from '../services/auth';
import '../styles/Login.css';

function Login({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        // Login
        const result = await authService.login(formData.username, formData.password);
        if (result.success) {
          onLoginSuccess();
        } else {
          setError(typeof result.error === 'string' ? result.error : 'Login failed');
        }
      } else {
        // Register
        if (formData.password !== formData.password2) {
          setError('Passwords do not match');
          setLoading(false);
          return;
        }

        const result = await authService.register(
          formData.username,
          formData.email,
          formData.password,
          formData.password2
        );

        if (result.success) {
          // After registration, log them in automatically
          const loginResult = await authService.login(formData.username, formData.password);
          if (loginResult.success) {
            onLoginSuccess();
          } else {
            setError('Registration successful, but login failed. Please try logging in.');
          }
        } else {
          setError(typeof result.error === 'string' ? result.error : 'Registration failed');
        }
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestMode = () => {
    authService.loginAsGuest();
    onLoginSuccess();
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Politics Forum</h1>
          <p className="subtitle">
            {isLogin ? 'Welcome back' : 'Join our community'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {/* Username */}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="Your username"
              disabled={loading}
            />
          </div>

          {/* Email (only for register) */}
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="your@email.com"
                disabled={loading}
              />
            </div>
          )}

          {/* Password */}
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Your password"
              disabled={loading}
            />
          </div>

          {/* Confirm Password (only for register) */}
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="password2">Confirm Password</label>
              <input
                type="password"
                id="password2"
                name="password2"
                value={formData.password2}
                onChange={handleChange}
                required
                placeholder="Confirm password"
                disabled={loading}
              />
            </div>
          )}

          {/* Error message */}
          {error && <div className="error-message">{error}</div>}

          {/* Submit button */}
          <button
            type="submit"
            className="btn-submit"
            disabled={loading}
          >
            {loading ? 'Processing...' : isLogin ? 'Login' : 'Register'}
          </button>
        </form>

        {/* Guest button */}
        <button
          type="button"
          onClick={handleGuestMode}
          className="btn-guest"
          disabled={loading}
        >
          👤 Continue as Guest
        </button>

        {/* Toggle between login and register */}
        <div className="toggle-auth">
          <p>
            {isLogin ? "Don't have an account?" : 'Already have an account?'}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setFormData({
                  username: '',
                  email: '',
                  password: '',
                  password2: '',
                });
              }}
              className="toggle-btn"
              disabled={loading}
            >
              {isLogin ? 'Register' : 'Login'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
