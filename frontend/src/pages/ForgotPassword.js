import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';
import { Mail, RotateCw } from 'lucide-react';
import { Link } from 'react-router-dom';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const { requestPasswordReset } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    const result = await requestPasswordReset(email);

    if (result.success) {
      setMessage(result.message || 'If an account with that email exists, you will receive a reset link.');
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="page">
      <div className="form-container">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <RotateCw size={48} style={{ color: '#3498db', marginBottom: '1rem' }} />
          <h1>Forgot Password</h1>
          <p style={{ color: '#7f8c8d' }}>Enter your account email to reset your password</p>
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
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-full-width"
            disabled={loading}
          >
            {loading ? 'Submitting...' : 'Send Reset Link'}
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

export default ForgotPassword;
