import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Save, X } from 'lucide-react';
import axios from 'axios';

const Profile = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  React.useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  React.useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || '',
        first_name: user.first_name || '',
        last_name: user.last_name || ''
      });
    }
  }, [user]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.patch('/auth/user/', formData);
      setSuccess('Profile updated successfully!');
      setEditing(false);
      
      // Update the user context if needed
      // You might want to add an updateUser function to your AuthContext
      
    } catch (error) {
      console.error('Failed to update profile:', error);
      setError(
        error.response?.data?.detail || 
        'Failed to update profile'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      username: user?.username || '',
      email: user?.email || '',
      first_name: user?.first_name || '',
      last_name: user?.last_name || ''
    });
    setEditing(false);
    setError('');
    setSuccess('');
  };

  if (!user) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Profile Settings</h1>
      <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>
        Manage your account information and preferences
      </p>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Profile Information */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
            <h2>Personal Information</h2>
            {!editing && (
              <button 
                onClick={() => setEditing(true)}
                className="btn btn-primary"
              >
                Edit Profile
              </button>
            )}
          </div>

          {editing ? (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="username">
                  <User size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                />
              </div>

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
                />
              </div>

              <div className="form-group">
                <label htmlFor="first_name">First Name</label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  placeholder="Enter your first name"
                />
              </div>

              <div className="form-group">
                <label htmlFor="last_name">Last Name</label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Enter your last name"
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={loading}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <Save size={16} />
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  type="button" 
                  onClick={handleCancel}
                  className="btn btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <X size={16} />
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontWeight: 'bold', color: '#7f8c8d', fontSize: '0.9rem' }}>Username</label>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.1rem' }}>{user.username}</p>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontWeight: 'bold', color: '#7f8c8d', fontSize: '0.9rem' }}>Email</label>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.1rem' }}>{user.email}</p>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontWeight: 'bold', color: '#7f8c8d', fontSize: '0.9rem' }}>First Name</label>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.1rem' }}>
                  {user.first_name || 'Not specified'}
                </p>
              </div>
              
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontWeight: 'bold', color: '#7f8c8d', fontSize: '0.9rem' }}>Last Name</label>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.1rem' }}>
                  {user.last_name || 'Not specified'}
                </p>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontWeight: 'bold', color: '#7f8c8d', fontSize: '0.9rem' }}>Member Since</label>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.1rem' }}>
                  {new Date(user.date_joined).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Account Statistics */}
        <div className="card">
          <h2>Account Statistics</h2>
          
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <h3 style={{ color: '#3498db', margin: '0 0 0.5rem 0' }}>0</h3>
                <p style={{ color: '#7f8c8d', margin: 0 }}>Total Quizzes</p>
              </div>
              
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <h3 style={{ color: '#27ae60', margin: '0 0 0.5rem 0' }}>0</h3>
                <p style={{ color: '#7f8c8d', margin: 0 }}>Quiz Attempts</p>
              </div>
              
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <h3 style={{ color: '#e74c3c', margin: '0 0 0.5rem 0' }}>0%</h3>
                <p style={{ color: '#7f8c8d', margin: 0 }}>Average Score</p>
              </div>
            </div>
          </div>

          <div style={{ 
            padding: '1rem', 
            backgroundColor: '#fff3cd', 
            borderRadius: '4px',
            border: '1px solid #ffeaa7'
          }}>
            <h4 style={{ color: '#856404', margin: '0 0 0.5rem 0' }}>Getting Started</h4>
            <p style={{ color: '#856404', margin: 0, fontSize: '0.9rem' }}>
              Upload your first quiz to start tracking your learning progress and see detailed statistics here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;