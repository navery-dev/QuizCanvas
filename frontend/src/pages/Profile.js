import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Save, X } from 'lucide-react';
import axios from 'axios';

// Configure axios base URL to match your other components
axios.defaults.baseURL = 'https://api.quizcanvas.xyz';

const Profile = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profileData, setProfileData] = useState(null);

  // Fetch complete user profile data
  React.useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await axios.get('/api/auth/profile/');
        if (response.data.success) {
          setProfileData(response.data.data);
        }
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
      }
    };

    if (isAuthenticated && !authLoading) {
      fetchUserProfile();
    }
  }, [isAuthenticated, authLoading]);

  React.useEffect(() => {
    // Wait for auth loading to complete before redirecting
    if (authLoading) return;
    
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate]);

  React.useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || ''
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
      const response = await axios.patch('/api/auth/profile/', formData);
      if (response.data.success) {
        setSuccess('Profile updated successfully!');
        setEditing(false);
        
        // Update the user data in localStorage to reflect changes
        const updatedUser = { ...user, ...formData };
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }
    } catch (error) {
      console.error('Failed to update profile:', error);
      setError(
        error.response?.data?.error || 
        'Failed to update profile'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      username: user?.username || '',
      email: user?.email || ''
    });
    setEditing(false);
    setError('');
    setSuccess('');
  };

  // Show loading while auth is being initialized
  if (authLoading) {
    return (
      <div className="page">
        <div className="loading" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" style={{ 
            width: '40px', 
            height: '40px', 
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #3498db',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem'
          }}></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="page">
        <div className="loading" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner" style={{ 
            width: '40px', 
            height: '40px', 
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #3498db',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem'
          }}></div>
          <p>Loading user data...</p>
        </div>
      </div>
    );
  }

  // Format member since date - use profileData if available, fallback to user data
  const formatMemberSince = () => {
    const userData = profileData || user;
    const dateField = userData?.date_joined || userData?.dateJoined;
    
    if (dateField) {
      try {
        return new Date(dateField).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
      } catch (error) {
        console.error('Error formatting date:', error);
        return 'Date not available';
      }
    }
    // Fallback - use current date as a reasonable default
    return new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

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
                  maxLength={10}
                />
                <small style={{ color: '#7f8c8d', fontSize: '0.8rem' }}>
                  Maximum 10 characters
                </small>
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
                  maxLength={50}
                />
                <small style={{ color: '#7f8c8d', fontSize: '0.8rem' }}>
                  Maximum 50 characters
                </small>
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
                <label style={{ fontWeight: 'bold', color: '#7f8c8d', fontSize: '0.9rem' }}>Member Since</label>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '1.1rem' }}>
                  {formatMemberSince()}
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
                <p style={{ color: '#7f8c8d', margin: 0 }}>Best Score</p>
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