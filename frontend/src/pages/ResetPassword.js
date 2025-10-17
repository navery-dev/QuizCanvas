import React, { useState, useEffect } from 'react';
import { useAuth } from '../services/AuthContext';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Lock, AlertCircle } from 'lucide-react';
import axios from 'axios';

const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetPassword } = useAuth();
  const [formData, setFormData] = useState({ newPassword: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState('');
  const [tokenValid, setTokenValid] = useState(null); // null = checking, true = valid, false = invalid

  // Validate token on page load
  useEffect(() => {
    const validateToken = async () => {
      const urlParams = new URLSearchParams(location.search);
      const tokenParam = urlParams.get('token');
      
      if (!tokenParam) {
        setError('Invalid reset link. Please request a new password reset.');
        setTokenValid(false);
        return;
      }
      
      setToken(tokenParam);
      
      // Validate token by attempting to decode it on backend
      try {
        const response = await axios.post('/api/auth/validate-reset-token/', {
          token: tokenParam
        });
        
        if (response.data.success) {
          setTokenValid(true);
        } else {
          setError(response.data.error || 'This password reset link has expired or is invalid. Please request a new one.');
          setTokenValid(false);
        }
      } catch (err) {
        setError('This password reset link has expired or is invalid. Please request a new one.');
        setTokenValid(false);
      }
    };
    
    validateToken();
  }, [location]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!token) {
      setError('Invalid reset token. Please request a new password reset.');
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.newPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    setLoading(true);
    const result = await resetPassword(token, formData.newPassword);
    
    if (result.success) {
      setMessage(result.message || 'Password reset successfully. Redirecting to login...');
      setFormData({ newPassword: '', confirmPassword: '' });
      setTimeout(() => navigate('/login'), 3000);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="page">
      <div className="form-container">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Lock size={48} style={{ color: '#3498db', marginBottom: '1rem' }} />
          <h1>Reset Password</h1>
          <p style={{ color: '#7f8c8d' }}>Enter a new password for your account</p>
        </div>

        {/* Show loading while validating token */}
        {tokenValid === null && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>Validating reset link...</p>
          </div>
        )}

        {/* Show error if token is invalid or expired */}
        {tokenValid === false && (
          <div>
            <div className="error-message" style={{ marginBottom: '20px' }}>
              <AlertCircle size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />
              {error}
            </div>
            <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <p style={{ marginBottom: '15px' }}>This password reset link has expired or is invalid.</p>
              <Link 
                to="/forgot-password" 
                className="btn btn-primary"
                style={{ display: 'inline-block', textDecoration: 'none' }}
              >
                Request New Reset Link
              </Link>
            </div>
          </div>
        )}

        {/* Show form only if token is valid */}
        {tokenValid === true && (
          <>
            {error && (
              <div className="error-message">{error}</div>
            )}
            
            {message && (
              <div className="success-message">{message}</div>
            )}

            {!message && (
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="newPassword">
                    <Lock size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                    New Password
                  </label>
                  <input
                    type="password"
                    id="newPassword"
                    name="newPassword"
                    value={formData.newPassword}
                    onChange={handleChange}
                    required
                    minLength="6"
                    placeholder="Enter new password (min 6 characters)"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword">
                    <Lock size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    minLength="6"
                    placeholder="Confirm new password"
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary btn-full-width"
                  disabled={loading}
                >
                  {loading ? 'Updating Password...' : 'Reset Password'}
                </button>
              </form>
            )}
          </>
        )}

        <div style={{ textAlign: 'center', marginTop: '2rem' }}>
          <Link to="/login" style={{ color: '#3498db', textDecoration: 'none', fontSize: '0.9rem' }}>
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;