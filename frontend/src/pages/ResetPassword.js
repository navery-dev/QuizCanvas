import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Lock } from 'lucide-react';

const ResetPassword = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { resetPassword } = useAuth();
  const [formData, setFormData] = useState({ newPassword: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    const result = await resetPassword(token, formData.newPassword);
    if (result.success) {
      setMessage(result.message || 'Password reset successfully. Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
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

        {error && (
          <div className="error-message">{error}</div>
        )}
        {message && (
          <div className="success-message">{message}</div>
        )}

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
              placeholder="Enter new password"
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
              placeholder="Confirm new password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full-width"
            disabled={loading}
          >
            {loading ? 'Updating...' : 'Reset Password'}
          </button>
        </form>

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
