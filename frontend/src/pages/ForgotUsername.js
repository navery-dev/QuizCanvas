// Create this file: frontend/src/pages/ForgotUsername.js

import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';
import { Mail, Lock, User } from 'lucide-react';
import { Link } from 'react-router-dom';

const ForgotUsername = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const { requestUsernameReminder } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    
    if (!formData.email || !formData.password) {
      setError('Email and password are required');
      return;
    }

    setLoading(true);
    const result = await requestUsernameReminder(formData.email, formData.password);

    if (result.success) {
      setMessage(result.message || 'If the email and password are correct, your username will be sent to your email address.');
      setFormData({ email: '', password: '' }); // Clear form on success
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="page">
      <div className="form-container">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <User size={48} style={{ color: '#3498db', marginBottom: '1rem' }} />
          <h1>Forgot Username</h1>
          <p style={{ color: '#7f8c8d' }}>Enter your email and password to receive your username</p>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">
              <Mail size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email address"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </div>

          <div style={{ 
            backgroundColor: '#e3f2fd', 
            padding: '15px', 
            borderRadius: '5px', 
            marginBottom: '20px',
            border: '1px solid #2196f3'
          }}>
            <p style={{ margin: 0, fontSize: '14px', color: '#1565c0' }}>
              <strong>Security Note:</strong> We need your password to verify your identity before sending your username.
            </p>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full-width"
            disabled={loading}
          >
            {loading ? 'Verifying...' : 'Send Username'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <div style={{ marginBottom: '10px' }}>
            <Link to="/forgot-password" style={{ color: '#3498db', textDecoration: 'none', fontSize: '0.9rem' }}>
              Forgot your password instead?
            </Link>
          </div>
          <Link to="/login" style={{ color: '#3498db', textDecoration: 'none', fontSize: '0.9rem' }}>
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotUsername;