import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { Plus, BookOpen, BarChart3, Clock, Trash2, Upload, FileText, TrendingUp } from 'lucide-react';
import axios from 'axios';

axios.defaults.baseURL = 'https://api.quizcanvas.xyz';

const Dashboard = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch dashboard data (includes recent activity and stats)
      const dashboardResponse = await axios.get('/api/dashboard/');
      if (dashboardResponse.data.success) {
        setDashboardData(dashboardResponse.data.data);
      }
      
      // Fetch user's quizzes
      const quizzesResponse = await axios.get('/api/quizzes/');
      if (quizzesResponse.data.success) {
        setQuizzes(quizzesResponse.data.data.quizzes || []);
      }
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      if (error.response?.status === 401) {
        navigate('/login');
      } else {
        setError('Failed to load dashboard data. Please try refreshing the page.');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    // Wait for auth loading to complete
    if (authLoading) {
      console.log('Auth is still loading, waiting...');
      return;
    }

    console.log('Auth loading complete. isAuthenticated:', isAuthenticated);
    
    if (!isAuthenticated) {
      console.log('User not authenticated, redirecting to login');
      navigate('/login');
      return;
    }
    
    console.log('User authenticated, fetching dashboard data');
    fetchDashboardData();
  }, [isAuthenticated, authLoading, navigate, fetchDashboardData]); // Add authLoading to dependencies

  const handleDeleteQuiz = async (quizId) => {
    if (!window.confirm('Are you sure you want to delete this quiz? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await axios.delete(`/api/quizzes/${quizId}/delete/`);
      if (response.data.success) {
        setQuizzes(quizzes.filter(quiz => quiz.quiz_id !== quizId));
        // Refresh dashboard data after deletion
        fetchDashboardData();
      }
    } catch (error) {
      console.error('Failed to delete quiz:', error);
      setError('Failed to delete quiz. Please try again.');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Show loading while auth is initializing
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
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show loading while dashboard data is being fetched
  if (loading) {
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
          <p>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  // Check if user is new (no quizzes)
  const isNewUser = quizzes.length === 0;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Welcome back, {user?.username}!</h1>
          <p style={{ color: '#7f8c8d', marginTop: '0.5rem' }}>
            {isNewUser 
              ? "Let's get you started with your first quiz"
              : "Track your progress and continue learning"
            }
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          <Plus size={20} style={{ marginRight: '0.5rem' }} />
          Upload New Quiz
        </Link>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* New User Welcome Section */}
      {isNewUser && (
        <div className="card" style={{ marginBottom: '2rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', textAlign: 'center', padding: '3rem' }}>
          <Upload size={64} style={{ marginBottom: '1rem', opacity: 0.9 }} />
          <h2 style={{ marginBottom: '1rem', color: 'white' }}>Get Started with QuizCanvas</h2>
          <p style={{ marginBottom: '2rem', opacity: 0.9, maxWidth: '600px', margin: '0 auto 2rem' }}>
            Upload your study materials in CSV or JSON format and start tracking your learning progress. 
            Perfect for exam prep, certification studies, or any knowledge area you want to master.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/upload" className="btn" style={{ background: 'white', color: '#667eea', border: 'none' }}>
              <Plus size={20} style={{ marginRight: '0.5rem' }} />
              Upload Your First Quiz
            </Link>
            <Link to="/faq" className="btn" style={{ background: 'transparent', color: 'white', border: '2px solid white' }}>
              <FileText size={20} style={{ marginRight: '0.5rem' }} />
              Learn How It Works
            </Link>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: isNewUser ? '1fr' : '2fr 1fr', gap: '2rem' }}>
        {/* My Quizzes */}
        <div>
          <h2 style={{ marginBottom: '1rem' }}>My Quizzes</h2>
          {quizzes.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <BookOpen size={48} style={{ color: '#bdc3c7', marginBottom: '1rem' }} />
              <h3 style={{ color: '#7f8c8d', marginBottom: '1rem' }}>No quizzes yet</h3>
              <p style={{ color: '#95a5a6', marginBottom: '2rem' }}>
                Upload your first quiz file (CSV or JSON) to get started with tracking your learning progress
              </p>
              <Link to="/upload" className="btn btn-primary">
                <Upload size={20} style={{ marginRight: '0.5rem' }} />
                Upload Your First Quiz
              </Link>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {quizzes.map(quiz => (
                <div key={quiz.quiz_id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ marginBottom: '0.5rem' }}>
                        <Link 
                          to={`/quiz/${quiz.quiz_id}`}
                          style={{ textDecoration: 'none', color: '#2c3e50' }}
                        >
                          {quiz.title}
                        </Link>
                      </h3>
                      <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                        {quiz.description || 'No description provided'}
                      </p>
                      <div style={{ fontSize: '0.9rem', color: '#95a5a6' }}>
                        <span>{quiz.question_count || 0} questions</span>
                        {quiz.sections && quiz.sections.length > 0 && (
                          <span> • {quiz.sections.length} sections</span>
                        )}
                        <span> • Uploaded {formatDate(quiz.upload_date)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteQuiz(quiz.quiz_id)}
                      className="btn"
                      style={{ 
                        padding: '0.5rem', 
                        marginLeft: '1rem',
                        background: '#e74c3c',
                        color: 'white',
                        border: 'none'
                      }}
                      title="Delete quiz"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity - Only show if not a new user */}
        {!isNewUser && (
          <div>
            <h2 style={{ marginBottom: '1rem' }}>Recent Activity</h2>
            {!dashboardData?.recent_activity || dashboardData.recent_activity.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
                <Clock size={32} style={{ color: '#bdc3c7', marginBottom: '1rem' }} />
                <p style={{ color: '#7f8c8d' }}>No recent activity</p>
                <p style={{ color: '#95a5a6', fontSize: '0.9rem' }}>
                  Start taking quizzes to see your activity here
                </p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '1rem' }}>
                {dashboardData.recent_activity.slice(0, 5).map((attempt, index) => (
                  <div key={index} className="card" style={{ padding: '1rem' }}>
                    <h4 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>
                      {attempt.quiz_title}
                    </h4>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ 
                        color: attempt.score >= 70 ? '#27ae60' : '#e74c3c',
                        fontWeight: 'bold'
                      }}>
                        {attempt.score}%
                      </span>
                      <span style={{ color: '#95a5a6', fontSize: '0.8rem' }}>
                        {formatDate(attempt.date)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Quick Actions for New Users */}
      {isNewUser && (
        <div style={{ marginTop: '2rem' }}>
          <h2 style={{ marginBottom: '1rem' }}>Quick Start Guide</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <Upload size={32} style={{ color: '#3498db', marginBottom: '1rem' }} />
              <h3 style={{ marginBottom: '1rem' }}>1. Upload Quiz File</h3>
              <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                Upload your study questions in CSV or JSON format
              </p>
              <Link to="/upload" className="btn btn-primary btn-small">
                Get Started
              </Link>
            </div>
            
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <BookOpen size={32} style={{ color: '#27ae60', marginBottom: '1rem' }} />
              <h3 style={{ marginBottom: '1rem' }}>2. Take Quizzes</h3>
              <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                Test your knowledge and track your progress
              </p>
            </div>
            
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <BarChart3 size={32} style={{ color: '#e74c3c', marginBottom: '1rem' }} />
              <h3 style={{ marginBottom: '1rem' }}>3. Track Progress</h3>
              <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                Monitor your improvement and mastery levels
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;